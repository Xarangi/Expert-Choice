from __future__ import annotations

from expert_choice.adapters.teamwork import TeamworkRankingAdapter
from expert_choice.claims.base import format_ranking


def test_moon_survival_parser_extracts_all_items():
    adapter = TeamworkRankingAdapter("moon_survival", n_agents=4, seed=0)
    adapter.prepare()
    text = format_ranking({item: i + 1 for i, item in enumerate(adapter.items)})
    parsed = adapter.parse_ranking(text)
    assert set(parsed) == set(adapter.items)
    assert adapter.score(parsed) == 0.0


def test_lost_at_sea_and_sbp_construct():
    sea = TeamworkRankingAdapter("lost_at_sea", n_agents=4, seed=1, expert_info_mode="distributed")
    sea.prepare()
    assert len(sea.items) == 15
    assert sea.designated_expert_ids

    sbp = TeamworkRankingAdapter(
        "student_body_president", n_agents=4, seed=2, expert_info_mode="distributed"
    )
    sbp.prepare()
    assert len(sbp.items) == 4
    ranking = {item: i + 1 for i, item in enumerate(["Candidate D", "Candidate C", "Candidate A", "Candidate B"])}
    # ground truth D=1, C=2, A=3, B=4
    assert sbp.score(ranking) == 0.0


def test_single_expert_hidden_info_is_concentrated():
    adapter = TeamworkRankingAdapter(
        "moon_survival", n_agents=4, seed=0, expert_info_mode="single_expert"
    )
    adapter.prepare()
    assert len(adapter.designated_expert_ids) == 1
    expert = adapter.designated_expert_ids[0]
    nonempty = [aid for aid in adapter.agent_ids if adapter.hidden_info(aid).strip()]
    assert nonempty == [expert]
