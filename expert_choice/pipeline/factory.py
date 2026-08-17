from __future__ import annotations

from expert_choice.adapters.teamwork import TeamworkRankingAdapter
from expert_choice.backends import create_backend
from expert_choice.backends.mock import MockBackend
from expert_choice.claims import get_claim_schema, get_thesis_selector
from expert_choice.pipeline.config import DEFAULT_SYSTEM_PROMPT, PipelineConfig
from expert_choice.pipeline.orchestrator import Orchestrator, RunContext
from expert_choice.topology import get_topology_policy


def build_orchestrator(
    config: PipelineConfig,
    *,
    adapter=None,
    backend=None,
    mock: MockBackend | None = None,
) -> Orchestrator:
    adapter = adapter or TeamworkRankingAdapter(
        task_name=config.task,
        n_agents=config.n_agents,
        expert_info_mode=config.expert_info_mode,
        seed=config.seed,
        decision_mode=config.decision_mode,
    )
    backend = backend or create_backend(
        provider=config.backend.provider,
        model=config.backend.model,
        agent_models=config.backend.agent_models,
        temperature=config.backend.temperature,
        max_workers=config.backend.max_workers,
        mock=mock,
    )
    context = RunContext(
        adapter=adapter,
        backend=backend,
        schema=get_claim_schema(config.claim_schema),
        thesis_selector=get_thesis_selector(config.thesis_selector),
        topology_policy=get_topology_policy(
            config.topology_policy, replication_k=config.replication_k
        ),
        config=config,
        system_prompt=config.system_prompt or DEFAULT_SYSTEM_PROMPT,
    )
    return Orchestrator(context)
