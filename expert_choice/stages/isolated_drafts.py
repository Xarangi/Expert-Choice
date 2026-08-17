from __future__ import annotations

from expert_choice.claims.base import split_rationale_and_ranking
from expert_choice.core.types import Draft, Message, PipelineState
from expert_choice.eval.metrics import draft_baselines


DEFAULT_SYSTEM_PROMPT = (
    "You are a careful reasoning agent. Follow the task instructions exactly. "
    "Do not discuss other agents. Output the ranking in the required MY RANKING format."
)


class IsolatedDraftsStage:
    name = "isolated_drafts"

    def run(self, context, state: PipelineState) -> PipelineState:
        adapter = context.adapter
        adapter.prepare()
        requests: list[tuple[str, list[Message]]] = []
        for agent_id in state.agent_ids:
            prompt = adapter.prompt_for(agent_id)
            requests.append(
                (
                    agent_id,
                    [
                        Message(role="system", content=context.system_prompt),
                        Message(role="user", content=prompt),
                    ],
                )
            )

        completions = context.backend.complete_many(requests)
        drafts: dict[str, Draft] = {}
        for agent_id in state.agent_ids:
            completion = completions[agent_id]
            state.usage.add(completion)
            rationale, _ = split_rationale_and_ranking(completion.text)
            try:
                ranking = adapter.parse_ranking(completion.text)
                score = adapter.score(ranking)
                parse_error = None
            except Exception as exc:  # noqa: BLE001 - parse failures are data, not bugs
                ranking = {}
                score = adapter.worst_score()
                parse_error = str(exc)
            drafts[agent_id] = Draft(
                agent_id=agent_id,
                raw_text=completion.text,
                rationale=rationale,
                ranking=ranking,
                score=score,
                parse_error=parse_error,
                logprob=completion.logprob,
            )

        state.drafts = drafts
        state.metadata["designated_expert_ids"] = list(adapter.designated_expert_ids)
        state.metadata["expert_info_mode"] = getattr(adapter, "expert_info_mode", None)
        state.metrics.update(draft_baselines(drafts))
        return state
