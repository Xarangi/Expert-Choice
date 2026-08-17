from __future__ import annotations

from abc import ABC, abstractmethod

from expert_choice.claims.base import format_ranking


class RankingTaskAdapter(ABC):
    """Task-facing interface used by the pipeline. Independent of the paper's execute()."""

    name: str
    items: list[str]
    agent_ids: list[str]
    designated_expert_ids: list[str]

    @abstractmethod
    def prepare(self) -> None: ...

    @abstractmethod
    def prompt_for(self, agent_id: str) -> str: ...

    @abstractmethod
    def parse_ranking(self, text: str) -> dict[str, int]: ...

    @abstractmethod
    def score(self, ranking: dict[str, int]) -> float: ...

    def worst_score(self) -> float:
        n = len(self.items)
        if n % 2 == 0:
            return float(n * n / 2)
        return float((n - 1) * (n + 1) / 2)

    def format_ranking(self, ranking: dict[str, int]) -> str:
        return format_ranking(ranking)

    def hidden_info(self, agent_id: str) -> str:
        return ""
