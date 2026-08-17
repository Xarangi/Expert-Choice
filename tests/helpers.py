from __future__ import annotations

from expert_choice.claims.base import format_ranking
from expert_choice.core.types import Draft
from expert_choice.pipeline.config import PipelineConfig
from expert_choice.pipeline.orchestrator import RunContext
from tests.fakes import FakeRankingAdapter


def ranking_reply(order: list[str], rationale: str = "Because of domain facts.") -> str:
    return f"{rationale}\n\n{format_ranking({item: i + 1 for i, item in enumerate(order)})}"


def make_draft(agent_id: str, order: list[str], rationale: str, adapter: FakeRankingAdapter) -> Draft:
    text = ranking_reply(order, rationale)
    ranking = adapter.parse_ranking(text)
    return Draft(
        agent_id=agent_id,
        raw_text=text,
        rationale=rationale,
        ranking=ranking,
        score=adapter.score(ranking),
    )


def make_context(
    adapter: FakeRankingAdapter | None = None,
    backend=None,
    schema=None,
    thesis_selector=None,
    topology_policy=None,
    config: PipelineConfig | None = None,
) -> RunContext:
    from expert_choice.backends.mock import MockBackend
    from expert_choice.claims import get_claim_schema, get_thesis_selector
    from expert_choice.topology import get_topology_policy

    adapter = adapter or FakeRankingAdapter()
    config = config or PipelineConfig(
        task="fake", n_agents=len(adapter.agent_ids), backend={"provider": "mock"}
    )
    return RunContext(
        adapter=adapter,
        backend=backend or MockBackend(default_reply=""),
        schema=schema or get_claim_schema("per_item_rank"),
        thesis_selector=thesis_selector or get_thesis_selector("rationale_span"),
        topology_policy=topology_policy or get_topology_policy("max_replication"),
        config=config,
    )
