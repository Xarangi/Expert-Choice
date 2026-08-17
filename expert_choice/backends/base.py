from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from expert_choice.core.types import Completion, Message


class BaseChatBackend:
    """Shared helpers for chat backends."""

    max_workers: int = 8

    def complete(self, messages: list[Message], *, agent_id: str) -> Completion:
        raise NotImplementedError

    def complete_many(
        self,
        requests: list[tuple[str, list[Message]]],
        *,
        route_agent_id: Optional[dict[str, str]] = None,
    ) -> dict[str, Completion]:
        """Run completions in parallel.

        `requests` is (key, messages). `route_agent_id` maps key -> agent_id used
        for per-agent model routing. Keys must be unique.
        """
        if not requests:
            return {}

        keys = [key for key, _ in requests]
        if len(keys) != len(set(keys)):
            raise ValueError("complete_many requires unique request keys")

        def _route(key: str) -> str:
            if route_agent_id and key in route_agent_id:
                return route_agent_id[key]
            return key

        if len(requests) == 1:
            key, messages = requests[0]
            return {key: self.complete(messages, agent_id=_route(key))}

        workers = max(1, min(self.max_workers, len(requests)))
        results: dict[str, Completion] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_map = {
                pool.submit(self.complete, messages, agent_id=_route(key)): key
                for key, messages in requests
            }
            for future in as_completed(future_map):
                key = future_map[future]
                results[key] = future.result()
        return results
