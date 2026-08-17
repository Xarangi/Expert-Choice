from __future__ import annotations

from collections import defaultdict

from expert_choice.core.types import (
    Coalition,
    Message,
    PipelineState,
    ReplicationAttempt,
    ReplicationResult,
)


class CrossExamineStage:
    """Inject a candidate thesis into complement agents and test independent replication."""

    name = "cross_examine"

    def run(self, context, state: PipelineState) -> PipelineState:
        mode = context.config.cross_examine
        if mode == "skip":
            return state

        to_test = _select_coalitions(state.coalitions, state.agent_ids, mode)
        results: list[ReplicationResult] = []
        requests: list[tuple[str, list[Message], Coalition]] = []

        for coalition in to_test:
            complement = [
                aid for aid in state.agent_ids if aid not in coalition.agent_ids
            ]
            if not complement:
                results.append(
                    ReplicationResult(
                        claim_id=coalition.claim_id,
                        choice=coalition.choice,
                        thesis=coalition.thesis,
                        complement_ids=[],
                        attempts=[],
                        replication_rate=1.0,
                        unanimous=True,
                        tested=True,
                    )
                )
                continue
            for listener_id in complement:
                prompt = _replication_prompt(
                    original=context.adapter.prompt_for(listener_id),
                    thesis=coalition.thesis,
                    schema=context.schema,
                )
                request_id = f"{listener_id}::{coalition.claim_id}::{coalition.choice}"
                requests.append(
                    (
                        request_id,
                        [
                            Message(role="system", content=context.system_prompt),
                            Message(role="user", content=prompt),
                        ],
                        coalition,
                    )
                )

        completions = context.backend.complete_many(
            [(request_id, messages) for request_id, messages, _ in requests],
            route_agent_id={
                request_id: request_id.split("::", 1)[0] for request_id, _, _ in requests
            },
        )
        attempts_by_key: dict[tuple[str, str], list[ReplicationAttempt]] = defaultdict(list)
        request_coalition = {
            request_id: coalition for request_id, _, coalition in requests
        }

        for request_id, completion in completions.items():
            state.usage.add(completion)
            coalition = request_coalition[request_id]
            listener_id = request_id.split("::", 1)[0]
            listener_choice = None
            replicated = False
            try:
                ranking = context.adapter.parse_ranking(completion.text)
                extracted = context.schema.extract(ranking, context.adapter.items)
                listener_choice = extracted.get(coalition.claim_id)
                replicated = listener_choice == coalition.choice
            except Exception:  # noqa: BLE001
                replicated = False
            attempts_by_key[(coalition.claim_id, coalition.choice)].append(
                ReplicationAttempt(
                    claim_id=coalition.claim_id,
                    choice=coalition.choice,
                    listener_id=listener_id,
                    replicated=replicated,
                    listener_choice=listener_choice,
                    raw_text=completion.text,
                )
            )

        tested_keys = {(c.claim_id, c.choice) for c in to_test}
        for coalition in to_test:
            key = (coalition.claim_id, coalition.choice)
            if any(
                r.claim_id == coalition.claim_id
                and r.choice == coalition.choice
                and r.unanimous
                for r in results
            ):
                continue
            attempts = attempts_by_key.get(key, [])
            complement_ids = [aid for aid in state.agent_ids if aid not in coalition.agent_ids]
            n_ok = sum(1 for attempt in attempts if attempt.replicated)
            rate = (n_ok / len(complement_ids)) if complement_ids else 1.0
            results.append(
                ReplicationResult(
                    claim_id=coalition.claim_id,
                    choice=coalition.choice,
                    thesis=coalition.thesis,
                    complement_ids=complement_ids,
                    attempts=attempts,
                    replication_rate=rate,
                    unanimous=not complement_ids,
                    tested=True,
                )
            )

        # Keep any unanimous results already added; drop accidental duplicates.
        deduped: dict[tuple[str, str], ReplicationResult] = {}
        for result in results:
            deduped[(result.claim_id, result.choice)] = result
        state.replications = list(deduped.values())
        state.metadata["cross_examine_tested"] = sorted(
            f"{cid}:{choice}" for cid, choice in tested_keys
        )
        state.metrics["stage3_llm_calls"] = len(requests)
        return state


def _select_coalitions(
    coalitions: list[Coalition], agent_ids: list[str], mode: str
) -> list[Coalition]:
    if mode in {"full_complement", "full"}:
        return list(coalitions)
    if mode in {"top2_coalitions", "top2"}:
        grouped: dict[str, list[Coalition]] = defaultdict(list)
        for coalition in coalitions:
            grouped[coalition.claim_id].append(coalition)
        selected: list[Coalition] = []
        for group in grouped.values():
            ordered = sorted(
                group, key=lambda c: (-c.coalition_size, c.choice)
            )
            selected.extend(ordered[:2])
        return selected
    raise ValueError(f"Unknown cross_examine mode: {mode}")


def _replication_prompt(*, original: str, thesis, schema) -> str:
    description = schema.describe_claim(thesis.claim_id, thesis.choice)
    return (
        f"{original}\n"
        "A candidate analysis for one specific decision has been proposed. "
        "Re-evaluate the original problem independently. You may use the analysis "
        "if you find the reasoning convincing, but you must reach your own conclusion. "
        "Do not assume the analysis is authoritative, and do not try to compromise "
        "with other viewpoints.\n\n"
        f"Candidate analysis:\n{thesis.rationale}\n\n"
        f"The candidate concludes: {description}.\n\n"
        "Provide your own reasoning, then output a complete ranking in the required "
        "MY RANKING format."
    )
