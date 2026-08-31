"""Maps provider ids to adapter implementations."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from image_is_versatile.services.providers.gemini import GeminiAdapter
from image_is_versatile.services.providers.openai_responses import OpenAIResponsesAdapter

_ADAPTER_CLASSES = {
    "openai_responses": OpenAIResponsesAdapter,
    "gemini": GeminiAdapter,
}


def get_provider_config(provider_id: str) -> dict[str, Any]:
    providers = settings.VISION_PROVIDERS
    if provider_id not in providers:
        raise KeyError(f"Unknown provider id: {provider_id}")
    return providers[provider_id]


def get_api_key(provider_id: str) -> str:
    from image_is_versatile.services.api_keys import get_env_api_key, get_override_api_key

    override = get_override_api_key(provider_id)
    if override:
        return override
    return get_env_api_key(provider_id)


def get_adapter(provider_id: str):
    config = get_provider_config(provider_id)
    adapter_name = config["adapter"]
    adapter_class = _ADAPTER_CLASSES[adapter_name]
    return adapter_class(provider_id=provider_id, config=config)
