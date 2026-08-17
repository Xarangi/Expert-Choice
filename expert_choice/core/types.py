from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class Completion(BaseModel):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    logprob: Optional[float] = None


class UsageStats(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0

    def add(self, completion: Completion) -> None:
        self.input_tokens += completion.input_tokens
        self.output_tokens += completion.output_tokens
        self.llm_calls += 1


class Draft(BaseModel):
    agent_id: str
    raw_text: str
    rationale: str
    ranking: dict[str, int] = Field(default_factory=dict)
    score: Optional[float] = None
    parse_error: Optional[str] = None
    logprob: Optional[float] = None


class Thesis(BaseModel):
    claim_id: str
    choice: str
    author_id: str
    rationale: str
    coalition_agent_ids: list[str]
    coalition_size: int


class Coalition(BaseModel):
    claim_id: str
    choice: str
    agent_ids: list[str]
    thesis: Thesis

    @property
    def coalition_size(self) -> int:
        return len(self.agent_ids)


class ReplicationAttempt(BaseModel):
    claim_id: str
    choice: str
    listener_id: str
    replicated: bool
    listener_choice: Optional[str] = None
    raw_text: str = ""


class ReplicationResult(BaseModel):
    claim_id: str
    choice: str
    thesis: Thesis
    complement_ids: list[str]
    attempts: list[ReplicationAttempt] = Field(default_factory=list)
    replication_rate: float = 0.0
    unanimous: bool = False
    tested: bool = True


class VerifiedClaim(BaseModel):
    claim_id: str
    choice: str
    rationale: str
    hub_ids: list[str]
    replication_rate: float
    coalition_size: int


class Topology(BaseModel):
    speaking_rights: dict[str, float] = Field(default_factory=dict)
    hubs_by_claim: dict[str, list[str]] = Field(default_factory=dict)
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)


class PipelineState(BaseModel):
    task_name: str
    agent_ids: list[str]
    drafts: dict[str, Draft] = Field(default_factory=dict)
    coalitions: list[Coalition] = Field(default_factory=list)
    replications: list[ReplicationResult] = Field(default_factory=list)
    topology: Optional[Topology] = None
    final_solution: Optional[str] = None
    final_ranking: Optional[dict[str, int]] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    usage: UsageStats = Field(default_factory=UsageStats)
    metadata: dict[str, Any] = Field(default_factory=dict)
