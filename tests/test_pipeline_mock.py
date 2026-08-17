from __future__ import annotations

import re
from pathlib import Path

from expert_choice.backends.mock import MockBackend
from expert_choice.core.types import Message, PipelineState
from expert_choice.eval.logging import write_trace
from expert_choice.pipeline.config import PipelineConfig
from expert_choice.pipeline.factory import build_orchestrator
from expert_choice.stages.grouping import GroupingStage
from tests.helpers import make_context, make_draft, ranking_reply
from tests.fakes import FakeRankingAdapter


def _orders():
    expert = ["Alpha", "Beta", "Gamma", "Delta"]
    majority = ["Beta", "Alpha", "Gamma", "Delta"]
    return expert, majority


def test_complement_pool_excludes_coalition_members():
    adapter = FakeRankingAdapter()
    expert, majority = _orders()
    context = make_context(adapter)
    state = PipelineState(task_name="fake", agent_ids=adapter.agent_ids)
    state.drafts = {
        "0": make_draft("0", expert, "Alpha must be first because it is essential.", adapter),
        "1": make_draft("1", majority, "I prefer Beta first.", adapter),
        "2": make_draft("2", majority, "Beta first as well.", adapter),
    }
    state = GroupingStage().run(context, state)
    alpha_expert = next(c for c in state.coalitions if c.claim_id == "Alpha" and c.choice == "1")
    complement = [aid for aid in state.agent_ids if aid not in alpha_expert.agent_ids]
    assert complement == ["1", "2"]


def test_full_pipeline_promotes_replicable_expert_thesis():
    adapter = FakeRankingAdapter()
    expert, majority = _orders()
    true_ranks = {item: i + 1 for i, item in enumerate(expert)}

    def handler(agent_id: str, messages: list[Message]) -> str:
        user = messages[-1].content
        isolated = "Candidate analysis" not in user and "Verified sub-claims" not in user
        if isolated:
            order = expert if agent_id == "0" else majority
            rationale = (
                "Alpha is essential and must be ranked 1."
                if agent_id == "0"
                else "I think Beta should be first."
            )
            return ranking_reply(order, rationale)
        match = re.search(r'"([^"]+)" should be ranked (\d+)', user)
        if match and true_ranks.get(match.group(1)) == int(match.group(2)):
            return ranking_reply(expert, "The injected reasoning is convincing.")
        order = expert if agent_id == "0" else majority
        return ranking_reply(order, "I keep my original view.")

    config = PipelineConfig(
        method="replication_broadcast",
        task="fake",
        n_agents=3,
        backend={"provider": "mock"},
        stages=[
            "isolated_drafts",
            "grouping",
            "cross_examine",
            "reconstruct",
            "synthesize",
        ],
    )
    orch = build_orchestrator(
        config, adapter=adapter, backend=MockBackend(handler=handler)
    )
    state = orch.run()
    assert state.final_ranking is not None
    assert state.metrics["best_individual_l1"] == 0.0
    assert state.metrics["team_l1"] == 0.0
    assert state.metrics["strong_synergy"] is True
    alpha_hubs = state.topology.hubs_by_claim["Alpha"]
    assert "0" in alpha_hubs
    trace_path = Path(__file__).resolve().parent / "_pipeline_trace.jsonl"
    try:
        write_trace(trace_path, state)
        assert trace_path.read_text(encoding="utf-8").strip()
    finally:
        trace_path.unlink(missing_ok=True)


def test_majority_baseline_follows_the_crowd():
    adapter = FakeRankingAdapter()
    expert, majority = _orders()

    def handler(agent_id: str, messages: list[Message]) -> str:
        order = expert if agent_id == "0" else majority
        return ranking_reply(order, "draft")

    config = PipelineConfig(
        method="majority_drafts",
        n_agents=3,
        backend={"provider": "mock"},
        stages=["isolated_drafts", "majority_aggregate"],
    )
    state = build_orchestrator(
        config, adapter=adapter, backend=MockBackend(handler=handler)
    ).run()
    assert state.final_ranking["Alpha"] == 2
    assert state.final_ranking["Beta"] == 1
    assert state.metrics["team_l1"] > state.metrics["best_individual_l1"]
