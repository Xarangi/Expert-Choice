from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class BackendConfig(BaseModel):
    provider: str = "azure"
    model: str = "DeepSeek-V4-Flash"
    agent_models: dict[str, str] = Field(default_factory=dict)
    temperature: Optional[float] = None
    max_workers: int = 8


class PipelineConfig(BaseModel):
    method: str = "replication_broadcast"
    task: str = "moon_survival"
    n_agents: int = 4
    seed: int = 0
    expert_info_mode: str = "single_expert"
    decision_mode: str = "expert_not_mentioned"
    claim_schema: str = "per_item_rank"
    thesis_selector: str = "rationale_span"
    topology_policy: str = "max_replication"
    replication_k: float = 0.5
    synthesis: str = "assemble_then_hubs"
    cross_examine: str = "full_complement"
    stages: list[str] = Field(
        default_factory=lambda: [
            "isolated_drafts",
            "grouping",
            "cross_examine",
            "reconstruct",
            "synthesize",
        ]
    )
    backend: BackendConfig = Field(default_factory=BackendConfig)
    output_dir: str = "outputs"
    system_prompt: Optional[str] = None

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PipelineConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.model_validate(data)


DEFAULT_SYSTEM_PROMPT = (
    "You are a careful reasoning agent. Follow the task instructions exactly. "
    "Do not discuss other agents. Output the ranking in the required MY RANKING format."
)
