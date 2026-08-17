from __future__ import annotations

from expert_choice.core.types import Message, PipelineState
from expert_choice.eval.metrics import finalize_team_metrics


class SynthesizeStage:
    name = "synthesize"

    def run(self, context, state: PipelineState) -> PipelineState:
        if state.topology is None:
            raise RuntimeError("SynthesizeStage requires topology from reconstruct")
        verified = state.topology.verified_claims
        assembled = context.schema.assemble(verified, context.adapter.items)
        if assembled is not None:
            state.final_ranking = assembled
            state.final_solution = context.adapter.format_ranking(assembled)
            state.metadata["synthesis_mode"] = "deterministic_assembly"
            state.metrics.update(
                finalize_team_metrics(state, context.adapter.score(assembled))
            )
            return state

        if context.config.synthesis == "assemble_only":
            raise RuntimeError("Deterministic assembly failed and synthesis=assemble_only")

        hub_ids = sorted(
            {
                hub
                for hubs in state.topology.hubs_by_claim.values()
                for hub in hubs
            }
        )
        if not hub_ids:
            hub_ids = [
                aid
                for aid, rights in state.topology.speaking_rights.items()
                if rights > 0
            ] or list(state.agent_ids)

        constraints = context.schema.format_constraints(verified)
        requests = []
        for hub_id in hub_ids:
            prompt = (
                f"{context.adapter.prompt_for(hub_id)}\n"
                "The following sub-claims were independently replicated by agents who "
                "originally disagreed. Produce a single consistent ranking that preserves "
                "as many of these verified placements as possible. Do not average with "
                "unverified opinions.\n\n"
                f"{constraints}\n\n"
                "Provide brief reasoning, then output the complete ranking in the required "
                "MY RANKING format."
            )
            requests.append(
                (
                    hub_id,
                    [
                        Message(role="system", content=context.system_prompt),
                        Message(role="user", content=prompt),
                    ],
                )
            )

        completions = context.backend.complete_many(requests)
        hub_rankings: dict[str, dict[str, int]] = {}
        for hub_id, completion in completions.items():
            state.usage.add(completion)
            try:
                hub_rankings[hub_id] = context.adapter.parse_ranking(completion.text)
            except Exception:  # noqa: BLE001
                continue

        chosen = _pick_hub_ranking(
            hub_rankings, verified, context.schema, context.adapter.items
        )
        if chosen is None:
            chosen = _fallback_from_drafts(state, context.adapter)
        state.final_ranking = chosen
        state.final_solution = context.adapter.format_ranking(chosen)
        state.metadata["synthesis_mode"] = "constraint_preserving_hubs"
        state.metrics.update(finalize_team_metrics(state, context.adapter.score(chosen)))
        return state


def _pick_hub_ranking(hub_rankings, verified, schema, items):
    if not hub_rankings:
        return None
    unique = {tuple(sorted(r.items())) for r in hub_rankings.values()}
    if len(unique) == 1:
        return next(iter(hub_rankings.values()))

    best = None
    best_key = (-1, -1.0)
    for hub_id, ranking in hub_rankings.items():
        extracted = schema.extract(ranking, items)
        preserved = sum(
            1 for claim in verified if extracted.get(claim.claim_id) == claim.choice
        )
        owned = [c for c in verified if hub_id in c.hub_ids]
        mean_rep = (
            sum(c.replication_rate for c in owned) / len(owned) if owned else 0.0
        )
        key = (preserved, mean_rep)
        if key > best_key:
            best_key = key
            best = ranking
    return best


def _fallback_from_drafts(state: PipelineState, adapter) -> dict[str, int]:
    valid = [d for d in state.drafts.values() if d.ranking and d.score is not None]
    if not valid:
        return {item: i + 1 for i, item in enumerate(adapter.items)}
    return min(valid, key=lambda d: d.score).ranking
