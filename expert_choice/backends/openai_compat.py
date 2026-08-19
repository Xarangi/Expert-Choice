from __future__ import annotations

import os
from typing import Optional

from expert_choice.backends.base import BaseChatBackend
from expert_choice.core.types import Completion, Message


def _messages_payload(messages: list[Message]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _mean_logprob(choice: object) -> Optional[float]:
    logprobs = getattr(choice, "logprobs", None)
    if logprobs is None:
        return None
    content = getattr(logprobs, "content", None)
    if not content:
        return None
    values = [getattr(token, "logprob", None) for token in content]
    values = [v for v in values if v is not None]
    if not values:
        return None
    return float(sum(values) / len(values))


class OpenAIBackend(BaseChatBackend):
    """Official OpenAI Chat Completions backend."""

    def __init__(
        self,
        model: str,
        agent_models: Optional[dict[str, str]] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_workers: int = 8,
    ) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.agent_models = agent_models or {}
        self.temperature = temperature
        self.max_workers = max_workers

    def complete(self, messages: list[Message], *, agent_id: str) -> Completion:
        model = self.agent_models.get(agent_id, self.model)
        response = self.client.chat.completions.create(
            model=model,
            messages=_messages_payload(messages),
            temperature=self.temperature,
        )
        choice = response.choices[0]
        usage = response.usage
        return Completion(
            text=choice.message.content or "",
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            logprob=_mean_logprob(choice),
        )


class AzureOpenAIBackend(BaseChatBackend):
    """Azure OpenAI / Microsoft Foundry backend.

    `model` is the Azure deployment name.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        agent_models: Optional[dict[str, str]] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_workers: int = 8,
    ) -> None:
        from openai import OpenAI

        endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")

        # Accept either:
        #   https://foo.openai.azure.com
        # or
        #   https://foo.openai.azure.com/openai/v1/
        base_url = endpoint.rstrip("/")
        if not base_url.endswith("/openai/v1"):
            base_url += "/openai/v1/"
        else:
            base_url += "/"

        self.client = OpenAI(
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=base_url,
        )

        self.model = model or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        self.agent_models = agent_models or {}
        self.temperature = temperature
        self.max_workers = max_workers

    def complete(
        self,
        messages: list[Message],
        *,
        agent_id: str,
    ) -> Completion:
        deployment = self.agent_models.get(agent_id, self.model)

        if not deployment:
            raise ValueError(
                "Azure backend requires a deployment name via config model "
                "or AZURE_OPENAI_DEPLOYMENT"
            )

        kwargs = {
            "model": deployment,
            "messages": _messages_payload(messages),
        }

        # Important: some reasoning models don't accept temperature.
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        response = self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        usage = response.usage

        return Completion(
            text=choice.message.content or "",
            input_tokens=int(
                getattr(usage, "prompt_tokens", 0) or 0
            ),
            output_tokens=int(
                getattr(usage, "completion_tokens", 0) or 0
            ),
            logprob=_mean_logprob(choice),
        )
