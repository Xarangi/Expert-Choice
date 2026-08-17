from __future__ import annotations

import re

from expert_choice.adapters.base import RankingTaskAdapter


class FakeRankingAdapter(RankingTaskAdapter):
    """Small ranking task used by unit tests. No LLM and no paper dependency."""

    def __init__(
        self,
        items: list[str] | None = None,
        ground_truth: list[int] | None = None,
        n_agents: int = 3,
        designated_expert_ids: list[str] | None = None,
    ) -> None:
        self.name = "fake_ranking"
        self.items = items or ["Alpha", "Beta", "Gamma", "Delta"]
        self.ground_truth = ground_truth or [1, 2, 3, 4]
        self.agent_ids = [str(i) for i in range(n_agents)]
        self.designated_expert_ids = designated_expert_ids or ["0"]
        self.expert_info_mode = "single_expert"

    def prepare(self) -> None:
        return

    def prompt_for(self, agent_id: str) -> str:
        listed = "\n".join(f"{i+1}. {item}" for i, item in enumerate(self.items))
        return (
            f"You are Agent {agent_id}. Rank these items from 1 (best) to {len(self.items)} (worst):\n"
            f"{listed}\n\n"
            "Explain your reasoning, then output:\nMY RANKING:\n1. [item]\n..."
        )

    def parse_ranking(self, text: str) -> dict[str, int]:
        ranking: dict[str, int] = {}
        for line in text.splitlines():
            match = re.match(r"^\s*(\d+)[\.\)]\s*(.+)$", line.strip())
            if not match:
                continue
            rank = int(match.group(1))
            blob = match.group(2).strip()
            matched = None
            best = 0
            for item in self.items:
                if item in ranking:
                    continue
                if item.lower() == blob.lower():
                    matched = item
                    break
                if item.lower() in blob.lower() or blob.lower() in item.lower():
                    score = min(len(item), len(blob))
                    if score > best:
                        best = score
                        matched = item
            if matched:
                ranking[matched] = rank
        if len(ranking) != len(self.items):
            missing = [item for item in self.items if item not in ranking]
            raise ValueError(f"Incomplete ranking, missing {missing}")
        return ranking

    def score(self, ranking: dict[str, int]) -> float:
        return float(
            sum(
                abs(ranking[item] - self.ground_truth[i])
                for i, item in enumerate(self.items)
            )
        )
