from __future__ import annotations

import os

import pytest

from expert_choice.pipeline.config import PipelineConfig
from expert_choice.pipeline.factory import build_orchestrator


def _has_live_backend() -> bool:
    if os.getenv("EXPERT_CHOICE_LIVE") != "1":
        return False
    if os.getenv("OPENAI_API_KEY"):
        return True
    return bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))


@pytest.mark.skipif(not _has_live_backend(), reason="Set EXPERT_CHOICE_LIVE=1 with OpenAI/Azure credentials")
def test_live_smoke_two_agents_nasa():
    provider = "azure" if os.getenv("AZURE_OPENAI_API_KEY") else "openai"
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    config = PipelineConfig(
        method="replication_broadcast",
        task="moon_survival",
        n_agents=2,
        seed=0,
        expert_info_mode="single_expert",
        claim_schema="per_item_rank",
        cross_examine="top2_coalitions",
        backend={"provider": provider, "model": model, "max_workers": 2},
        stages=[
            "isolated_drafts",
            "grouping",
            "cross_examine",
            "reconstruct",
            "synthesize",
        ],
    )
    state = build_orchestrator(config).run()
    assert state.final_ranking
    assert len(state.final_ranking) == 15
    assert "team_l1" in state.metrics
