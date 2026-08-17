from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from expert_choice.core.types import (
    Coalition,
    Completion,
    Draft,
    Message,
    PipelineState,
    ReplicationResult,
    Thesis,
    Topology,
    VerifiedClaim,
)


@runtime_checkable
class ChatBackend(Protocol):
    def complete(self, messages: list[Message], *, agent_id: str) -> Completion: ...


@runtime_checkable
class RankingTaskAdapter(Protocol):
    name: str
    items: list[str]
    agent_ids: list[str]
    designated_expert_ids: list[str]

    def prepare(self) -> None: ...

    def prompt_for(self, agent_id: str) -> str: ...

    def parse_ranking(self, text: str) -> dict[str, int]: ...

    def score(self, ranking: dict[str, int]) -> float: ...

    def worst_score(self) -> float: ...

    def format_ranking(self, ranking: dict[str, int]) -> str: ...

    def hidden_info(self, agent_id: str) -> str: ...


@runtime_checkable
class ClaimSchema(Protocol):
    name: str

    def claim_ids(self, items: list[str]) -> list[str]: ...

    def extract(self, ranking: dict[str, int], items: list[str]) -> dict[str, str]: ...

    def slice_rationale(self, draft: Draft, claim_id: str) -> str: ...

    def assemble(
        self, verified: list[VerifiedClaim], items: list[str]
    ) -> Optional[dict[str, int]]: ...

    def format_constraints(self, verified: list[VerifiedClaim]) -> str: ...

    def describe_claim(self, claim_id: str, choice: str) -> str: ...


@runtime_checkable
class ThesisSelector(Protocol):
    name: str

    def select(
        self,
        drafts: dict[str, Draft],
        agent_ids: list[str],
        claim_id: str,
        schema: ClaimSchema,
    ) -> Thesis: ...


@runtime_checkable
class TopologyPolicy(Protocol):
    name: str

    def build(
        self,
        agent_ids: list[str],
        coalitions: list[Coalition],
        replications: list[ReplicationResult],
    ) -> Topology: ...


class Stage(Protocol):
    name: str

    def run(self, context: object, state: PipelineState) -> PipelineState: ...
