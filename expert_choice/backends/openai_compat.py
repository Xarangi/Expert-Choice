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


def _chat_create_kwargs(
    model: str,
    messages: list[Message],
    temperature: Optional[float],
) -> dict:
    kwargs: dict = {
        "model": model,
        "messages": _messages_payload(messages),
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return kwargs


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


def _openai_client(api_key: Optional[str], *, azure_endpoint: Optional[str] = None):
    """Official ``OpenAI()`` client, optionally pointed at Azure Foundry."""
    from openai import OpenAI

    if not azure_endpoint:
        return OpenAI(api_key=api_key)

    import httpx

    def _use_api_key_header(request: httpx.Request) -> None:
        request.headers["api-key"] = api_key
        request.headers.pop("Authorization", None)

    return OpenAI(
        api_key=api_key,
        base_url=azure_v1_base_url(azure_endpoint),
        http_client=httpx.Client(event_hooks={"request": [_use_api_key_header]}),
    )


class OpenAIBackend(BaseChatBackend):
    """Chat Completions via the official OpenAI Python SDK.

    Official OpenAI, or Azure AI Foundry / Azure OpenAI with ``azure=True``:
    same client, ``.../openai/v1/`` base URL, Azure ``api-key`` header.
    ``model`` is the OpenAI model id or the Azure deployment name.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        agent_models: Optional[dict[str, str]] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_workers: int = 8,
        *,
        azure: bool = False,
    ) -> None:
        if azure:
            endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            if not endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT is required")
            key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
            if not key:
                raise ValueError("AZURE_OPENAI_API_KEY is required")
            self.client = _openai_client(key, azure_endpoint=endpoint)
            self.model = model or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
            if not self.model:
                raise ValueError(
                    "Azure requires a deployment name via config model "
                    "or AZURE_OPENAI_DEPLOYMENT"
                )
        else:
            self.client = _openai_client(api_key or os.getenv("OPENAI_API_KEY"))
            if not model:
                raise ValueError("OpenAI backend requires a model name")
            self.model = model

        self.agent_models = agent_models or {}
        self.temperature = temperature
        self.max_workers = max_workers

    def complete(self, messages: list[Message], *, agent_id: str) -> Completion:
        model = self.agent_models.get(agent_id, self.model)
        response = self.client.chat.completions.create(
            **_chat_create_kwargs(model, messages, self.temperature)
        )
        choice = response.choices[0]
        usage = response.usage
        return Completion(
            text=choice.message.content or "",
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            logprob=_mean_logprob(choice),
        )
