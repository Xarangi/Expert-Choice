from __future__ import annotations

from expert_choice.core.types import PipelineState
from expert_choice.stages.grouping import GroupingStage
from tests.helpers import make_context, make_draft
from tests.fakes import FakeRankingAdapter


def test_exact_match_coalitions_not_similarity():
    adapter = FakeRankingAdapter()
    context = make_context(adapter)
    state = PipelineState(task_name="fake", agent_ids=adapter.agent_ids)
    items = adapter.items
    state.drafts = {
        "0": make_draft("0", items, "Alpha is essential for survival.", adapter),
        "1": make_draft(
            "1",
            ["Beta", "Alpha", "Gamma", "Delta"],
            "I would put Beta first and Alpha second.",
            adapter,
        ),
        "2": make_draft(
            "2",
            ["Beta", "Alpha", "Gamma", "Delta"],
            "Beta first, Alpha second as well.",
            adapter,
        ),
    }

    state = GroupingStage().run(context, state)
    alpha = [c for c in state.coalitions if c.claim_id == "Alpha"]
    choices = {c.choice: set(c.agent_ids) for c in alpha}
    assert choices["1"] == {"0"}
    assert choices["2"] == {"1", "2"}
    beta = {c.choice: set(c.agent_ids) for c in state.coalitions if c.claim_id == "Beta"}
    assert beta["1"] == {"1", "2"}
    assert beta["2"] == {"0"}


def test_unparsed_drafts_are_excluded_from_coalitions():
    adapter = FakeRankingAdapter()
    context = make_context(adapter)
    state = PipelineState(task_name="fake", agent_ids=adapter.agent_ids)
    good = make_draft("0", adapter.items, "ok", adapter)
    state.drafts = {
        "0": good,
        "1": good.model_copy(
            update={"agent_id": "1", "ranking": {}, "parse_error": "boom", "score": adapter.worst_score()}
        ),
        "2": make_draft("2", adapter.items, "ok", adapter),
    }
    state = GroupingStage().run(context, state)
    alpha = [c for c in state.coalitions if c.claim_id == "Alpha"]
    assert len(alpha) == 1
    assert set(alpha[0].agent_ids) == {"0", "2"}
