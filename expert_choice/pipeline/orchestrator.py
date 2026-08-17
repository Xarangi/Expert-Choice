from __future__ import annotations

from dataclasses import dataclass

from expert_choice.adapters.base import RankingTaskAdapter
from expert_choice.backends.base import BaseChatBackend
from expert_choice.core.types import PipelineState
from expert_choice.pipeline.config import DEFAULT_SYSTEM_PROMPT, PipelineConfig
from expert_choice.stages import build_stage


@dataclass
class RunContext:
    adapter: RankingTaskAdapter
    backend: BaseChatBackend
    schema: object
    thesis_selector: object
    topology_policy: object
    config: PipelineConfig
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


class Orchestrator:
    """Runs an ordered list of stages. Ablations are config.stages, not hardcoded branches."""

    def __init__(self, context: RunContext, stages: list | None = None) -> None:
        self.context = context
        self.stages = stages or [build_stage(name) for name in context.config.stages]

    def run(self) -> PipelineState:
        adapter = self.context.adapter
        adapter.prepare()
        state = PipelineState(task_name=adapter.name, agent_ids=list(adapter.agent_ids))
        state.metadata["method"] = self.context.config.method
        state.metadata["seed"] = self.context.config.seed
        state.metadata["stages"] = [stage.name for stage in self.stages]
        for stage in self.stages:
            state = stage.run(self.context, state)
        return state
