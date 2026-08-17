from __future__ import annotations

from typing import Optional

from expert_choice.core.types import Draft, PipelineState


def relative_synergy_gap(team_error: float, expert_error: float) -> float:
    """(team - expert) / expert for error metrics. 0 means the team matched the expert."""
    if expert_error == 0:
        return 0.0 if team_error == 0 else float(team_error)
    return (team_error - expert_error) / expert_error


def draft_baselines(drafts: dict[str, Draft]) -> dict[str, float]:
    scores = [d.score for d in drafts.values() if d.score is not None]
    if not scores:
        return {
            "best_individual_l1": None,
            "member_average_l1": None,
            "n_parsed_drafts": 0,
        }
    return {
        "best_individual_l1": min(scores),
        "member_average_l1": sum(scores) / len(scores),
        "n_parsed_drafts": len(scores),
        "individual_l1": {aid: d.score for aid, d in drafts.items()},
    }


def finalize_team_metrics(state: PipelineState, team_l1: float) -> dict:
    best = state.metrics.get("best_individual_l1")
    avg = state.metrics.get("member_average_l1")
    metrics = {
        "team_l1": team_l1,
        "relative_synergy_gap": relative_synergy_gap(team_l1, best)
        if best is not None
        else None,
        "weak_synergy": (avg is not None and team_l1 <= avg),
        "strong_synergy": (best is not None and team_l1 <= best),
        "llm_calls": state.usage.llm_calls,
        "input_tokens": state.usage.input_tokens,
        "output_tokens": state.usage.output_tokens,
    }
    return metrics
