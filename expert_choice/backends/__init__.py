from __future__ import annotations

from typing import Optional

from expert_choice.backends.base import BaseChatBackend
from expert_choice.backends.mock import MockBackend
from expert_choice.backends.openai_compat import OpenAIBackend


def create_backend(
    *,
    provider: str,
    model: str,
    agent_models: Optional[dict[str, str]] = None,
    temperature: Optional[float] = None,
    max_workers: int = 8,
    mock: Optional[MockBackend] = None,
) -> BaseChatBackend:
    name = provider.lower()
    if name == "mock":
        if mock is not None:
            return mock
        return MockBackend(default_reply="MY RANKING:\n1. placeholder")
    if name == "openai":
        return OpenAIBackend(
            model=model,
            agent_models=agent_models,
            temperature=temperature,
            max_workers=max_workers,
        )
    if name in {"azure", "azure_openai", "foundry"}:
        return OpenAIBackend(
            model=model,
            agent_models=agent_models,
            temperature=temperature,
            max_workers=max_workers,
            azure=True,
        )
    raise ValueError(f"Unknown backend provider: {provider}")
