"""Provider adapter protocol and shared types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from image_is_versatile.services.analysis import AnalysisResult
from image_is_versatile.services.model_registry import VisionModel
from image_is_versatile.services.vision_config import VisionApiRequestConfig


@dataclass(frozen=True)
class ModelAvailabilityStatus:
    ok: bool
    message: str
    provider: str
    model_id: str
    missing_models: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProviderModelsList:
    ok: bool
    message: str
    model_ids: list[str] = field(default_factory=list)


class VisionProviderAdapter(Protocol):
    provider_id: str

    def list_available_models(self, api_key: str) -> ProviderModelsList: ...

    def check_availability(self, model: VisionModel, api_key: str) -> ModelAvailabilityStatus: ...

    def analyze(
        self,
        model: VisionModel,
        *,
        instructions: str,
        user_prompt: str,
        image_path: str,
        image_content_type: str,
        api_config: VisionApiRequestConfig,
        api_key: str,
    ) -> AnalysisResult: ...


def map_provider_error(provider_label: str, env_key: str, exc: Exception) -> str:
    exc_name = type(exc).__name__
    if exc_name == "AuthenticationError":
        return f"{env_key} was rejected by {provider_label} (invalid or revoked)."
    if exc_name == "PermissionDeniedError":
        return f"{env_key} is valid but lacks permission to list models on {provider_label}."
    if exc_name == "RateLimitError":
        return f"{provider_label} rate limit reached. Try again shortly."
    if exc_name in ("APIConnectionError", "ConnectError"):
        return f"Could not reach {provider_label}. Check your network."
    return f"Unexpected error from {provider_label}: {exc}"
