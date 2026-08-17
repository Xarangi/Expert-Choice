from __future__ import annotations

import threading
from collections import defaultdict
from typing import Callable, Optional

from expert_choice.backends.base import BaseChatBackend
from expert_choice.core.types import Completion, Message

ReplyHandler = Callable[[str, list[Message]], str]


class MockBackend(BaseChatBackend):
    """Deterministic backend for tests.

    Provide either a `handler(agent_id, messages) -> text` or a per-agent queue
    of scripted replies. If both are set, the handler wins.
    """

    def __init__(
        self,
        handler: Optional[ReplyHandler] = None,
        scripted: Optional[dict[str, list[str]]] = None,
        default_reply: str = "",
        max_workers: int = 4,
    ) -> None:
        self.handler = handler
        self._scripted = defaultdict(list)
        if scripted:
            for agent_id, replies in scripted.items():
                self._scripted[agent_id].extend(replies)
        self.default_reply = default_reply
        self.max_workers = max_workers
        self._lock = threading.Lock()
        self.calls: list[tuple[str, list[Message]]] = []

    def complete(self, messages: list[Message], *, agent_id: str) -> Completion:
        with self._lock:
            self.calls.append((agent_id, list(messages)))
            if self.handler is not None:
                text = self.handler(agent_id, messages)
            elif self._scripted[agent_id]:
                text = self._scripted[agent_id].pop(0)
            else:
                text = self.default_reply
        return Completion(text=text, input_tokens=0, output_tokens=len(text.split()))
