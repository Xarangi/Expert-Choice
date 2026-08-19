from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlparse, urlunparse

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


def azure_v1_base_url(endpoint: str) -> str:
    """Build the OpenAI-SDK base URL for Foundry / Azure OpenAI.

    Default shape: ``https://<resource>.openai.azure.com/openai/v1/``.
    Resource hosts on ``*.services.ai.azure.com`` are rewritten to
    ``*.openai.azure.com`` unless the URL is a Foundry project path.
    """
    raw = endpoint.strip()
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    host = parsed.netloc
    path = parsed.path.rstrip("/")
    if host.endswith(".services.ai.azure.com") and "/api/projects/" not in path:
        resource = host[: -len(".services.ai.azure.com")]
        host = f"{resource}.openai.azure.com"
    if not path.endswith("/openai/v1"):
        path = f"{path}/openai/v1" if path else "/openai/v1"
    return urlunparse((parsed.scheme or "https", host, path + "/", "", "", ""))


def _openai_client_with_azure_api_key(api_key: str, base_url: str):
    """OpenAI() client against Azure, authenticating with the `api-key` header."""
    import httpx
    from openai import OpenAI

    def _use_api_key_header(request: httpx.Request) -> None:
        request.headers["api-key"] = api_key
        request.headers.pop("Authorization", None)

    http_client = httpx.Client(event_hooks={"request": [_use_api_key_header]})
    return OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


class AzureOpenAIBackend(BaseChatBackend):
    """Microsoft Foundry / Azure OpenAI backend (GA OpenAI v1 API).

    Uses the standard ``OpenAI`` client with
    ``https://<resource>.openai.azure.com/openai/v1/`` and the Azure ``api-key``
    header. No dated ``api-version`` query parameter. ``model`` is the deployment
    name.
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
        endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        if not key:
            raise ValueError("AZURE_OPENAI_API_KEY is required")

        base_url = azure_v1_base_url(endpoint)
        self.client = _openai_client_with_azure_api_key(key, base_url)

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
