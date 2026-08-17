from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from expert_choice.adapters.base import RankingTaskAdapter


def _ensure_teamwork_on_path() -> None:
    root = Path(__file__).resolve().parents[2] / "third_party" / "teamwork"
    if root.is_dir() and str(root) not in sys.path:
        sys.path.insert(0, str(root))


@dataclass
class _DummyProfile:
    agent_id: int


@dataclass
class _DummyAgent:
    profile: _DummyProfile


class TeamworkRankingAdapter(RankingTaskAdapter):
    """Wraps the paper's ranking tasks without calling Task.execute()."""

    def __init__(
        self,
        task_name: str,
        n_agents: int,
        expert_info_mode: str = "single_expert",
        seed: int = 0,
        decision_mode: str = "expert_not_mentioned",
    ) -> None:
        _ensure_teamwork_on_path()
        self._task = _build_teamwork_task(
            task_name=task_name,
            n_agents=n_agents,
            expert_info_mode=expert_info_mode,
            seed=seed,
            decision_mode=decision_mode,
        )
        self.name = task_name
        self.items = list(self._task.items)
        self.agent_ids = [str(aid) for aid in self._task.agent_ids]
        self.designated_expert_ids: list[str] = []
        self._prepared = False

    def prepare(self) -> None:
        if self._prepared:
            return
        dummies = [_DummyAgent(_DummyProfile(int(aid))) for aid in self.agent_ids]
        self._task._assign_expert_information(dummies)
        if self._task.designated_expert_agent_id is not None:
            self.designated_expert_ids = [str(self._task.designated_expert_agent_id)]
        else:
            self.designated_expert_ids = [
                str(aid)
                for aid, info in self._task.information_assigned_per_expert.items()
                if info
            ]
        self._prepared = True

    def prompt_for(self, agent_id: str) -> str:
        self.prepare()
        numeric_id = int(agent_id)
        task_desc = self._task.get_task_description(numeric_id)
        assigned_info = self._task.information_assigned_per_expert.get(numeric_id, [])
        mode = self._task.expert_info_mode
        if mode == "none" or not assigned_info:
            return f"{task_desc}\n\n"
        joined = "\n\n".join(assigned_info)
        if mode == "full":
            return f"{task_desc}\n\nNASA Ground Truth Analysis: {joined}\n\n"
        return (
            f"{task_desc}\n\n"
            f"Additional context that ONLY YOU KNOW and NO OTHER TEAMMATE KNOWS:\n"
            f"{joined}\n\n"
        )

    def parse_ranking(self, text: str) -> dict[str, int]:
        return self._task._parse_ranking(text)

    def score(self, ranking: dict[str, int]) -> float:
        l1 = 0.0
        for i, item in enumerate(self.items):
            l1 += abs(ranking[item] - self._task.ground_truth_ranking[i])
        return float(l1)

    def hidden_info(self, agent_id: str) -> str:
        self.prepare()
        return self._task.get_hidden_info(int(agent_id))

    @property
    def expert_info_mode(self) -> str:
        return self._task.expert_info_mode

    @property
    def items_expert_in_per_agent(self) -> dict[str, list[str]]:
        self.prepare()
        return {
            str(aid): list(items)
            for aid, items in self._task.items_expert_in_per_agent.items()
        }


def _build_teamwork_task(
    *,
    task_name: str,
    n_agents: int,
    expert_info_mode: str,
    seed: int,
    decision_mode: str,
) -> Any:
    agent_ids = list(range(n_agents))
    kwargs = dict(
        agent_ids=agent_ids,
        max_rounds=1,
        expert_info_mode=expert_info_mode,
        seed=seed,
        decision_mode=decision_mode,
        interactive_brainstorming_mode=False,
    )
    if task_name in {"moon_survival", "nasa", "nasa_moon_survival"}:
        from teamwork.tasks.moon_survival_task import MoonSurvivalTask

        return MoonSurvivalTask(**kwargs)
    if task_name in {"lost_at_sea", "lost-at-sea"}:
        from teamwork.tasks.lost_at_sea_task import LostAtSeaTask

        return LostAtSeaTask(**kwargs)
    if task_name in {"student_body_president", "sbp"}:
        from teamwork.tasks.student_body_president_task import StudentBodyPresidentTask

        return StudentBodyPresidentTask(**kwargs)
    raise ValueError(f"Unknown psychology task: {task_name}")
