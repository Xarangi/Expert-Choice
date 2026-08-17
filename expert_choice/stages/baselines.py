from __future__ import annotations

from collections import Counter, defaultdict

from expert_choice.core.types import PipelineState
from expert_choice.eval.metrics import finalize_team_metrics


class MajorityAggregateStage:
    """CoT + majority vote baseline: mode rank per item, then a valid permutation."""

    name = "majority_aggregate"

    def run(self, context, state: PipelineState) -> PipelineState:
        items = context.adapter.items
        ranks_by_item: dict[str, list[int]] = defaultdict(list)
        for draft in state.drafts.values():
            for item in items:
                if item in draft.ranking:
                    ranks_by_item[item].append(draft.ranking[item])

        mode_rank: dict[str, float] = {}
        for item in items:
            ranks = ranks_by_item.get(item) or [len(items)]
            counts = Counter(ranks)
            mode = min(counts, key=lambda r: (-counts[r], r))
            avg = sum(ranks) / len(ranks)
            mode_rank[item] = mode + avg / 1000.0

        ordered = sorted(items, key=lambda item: (mode_rank[item], item))
        ranking = {item: i + 1 for i, item in enumerate(ordered)}
        state.final_ranking = ranking
        state.final_solution = context.adapter.format_ranking(ranking)
        state.metadata["synthesis_mode"] = "majority_drafts"
        state.metrics.update(finalize_team_metrics(state, context.adapter.score(ranking)))
        return state


class IsolatedBestSelectStage:
    """Oracle individual: take the Stage-1 draft with lowest L1 vs ground truth."""

    name = "isolated_best_select"

    def run(self, context, state: PipelineState) -> PipelineState:
        valid = [d for d in state.drafts.values() if d.ranking and d.score is not None]
        if not valid:
            ranking = {item: i + 1 for i, item in enumerate(context.adapter.items)}
            winner = None
        else:
            winner = min(valid, key=lambda d: (d.score, d.agent_id))
            ranking = winner.ranking
        state.final_ranking = ranking
        state.final_solution = context.adapter.format_ranking(ranking)
        state.metadata["synthesis_mode"] = "isolated_best"
        state.metadata["oracle_best_agent_id"] = winner.agent_id if winner else None
        state.metrics.update(finalize_team_metrics(state, context.adapter.score(ranking)))
        return state
