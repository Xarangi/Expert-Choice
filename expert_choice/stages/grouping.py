from __future__ import annotations

from collections import defaultdict

from expert_choice.core.types import Coalition, PipelineState


class GroupingStage:
    """Exact-match quotient grouping on discrete sub-claim choices."""

    name = "grouping"

    def run(self, context, state: PipelineState) -> PipelineState:
        schema = context.schema
        items = context.adapter.items
        claim_ids = schema.claim_ids(items)
        extracted: dict[str, dict[str, str]] = {}
        for agent_id, draft in state.drafts.items():
            if draft.parse_error or not draft.ranking:
                extracted[agent_id] = {}
            else:
                extracted[agent_id] = schema.extract(draft.ranking, items)

        coalitions: list[Coalition] = []
        for claim_id in claim_ids:
            buckets: dict[str, list[str]] = defaultdict(list)
            for agent_id in state.agent_ids:
                choice = extracted.get(agent_id, {}).get(claim_id)
                if choice is None:
                    continue
                buckets[choice].append(agent_id)
            for choice, agent_ids in buckets.items():
                thesis = context.thesis_selector.select(
                    state.drafts, agent_ids, claim_id, schema
                )
                thesis.choice = choice
                thesis.coalition_agent_ids = list(agent_ids)
                thesis.coalition_size = len(agent_ids)
                coalitions.append(
                    Coalition(
                        claim_id=claim_id,
                        choice=choice,
                        agent_ids=list(agent_ids),
                        thesis=thesis,
                    )
                )

        state.coalitions = coalitions
        state.metadata["claim_ids"] = claim_ids
        return state
