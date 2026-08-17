from __future__ import annotations

from expert_choice.core.types import PipelineState


class ReconstructStage:
    name = "reconstruct"

    def run(self, context, state: PipelineState) -> PipelineState:
        state.topology = context.topology_policy.build(
            state.agent_ids, state.coalitions, state.replications
        )
        hubs = sorted(
            {
                hub
                for hubs in state.topology.hubs_by_claim.values()
                for hub in hubs
            }
        )
        state.metrics["n_hubs"] = len(hubs)
        state.metrics["hub_ids"] = hubs
        experts = set(state.metadata.get("designated_expert_ids") or [])
        hub_set = set(hubs)
        union = hub_set | experts
        state.metrics["hub_expert_jaccard"] = (
            len(hub_set & experts) / len(union) if union else 0.0
        )
        return state
