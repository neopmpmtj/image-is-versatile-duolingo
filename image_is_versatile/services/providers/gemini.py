"""Google Gemini vision adapter."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from image_is_versatile.services.analysis import AnalysisResult
from image_is_versatile.services.model_registry import VisionModel
from image_is_versatile.services.providers.base import (
    ModelAvailabilityStatus,
    ProviderModelsList,
    map_provider_error,
)
from image_is_versatile.services.vision_config import VisionApiRequestConfig, build_api_request_dict


class GeminiAdapter:
    provider_id = "gemini"

    def __init__(self, provider_id: str, config: dict[str, Any]) -> None:
        self.provider_id = provider_id
        self._config = config
        self.label = config.get("label", provider_id)
        self.env_key = config["env_key"]

    def _client(self, api_key: str) -> genai.Client:
        return genai.Client(api_key=api_key)

    def _normalize_model_id(self, name: str) -> str:
        if name.startswith("models/"):
            return name.split("/", 1)[1]
        return name

    def list_available_models(self, api_key: str) -> ProviderModelsList:
        if not api_key.strip():
            return ProviderModelsList(
                ok=False,
                message=f"{self.env_key} is not set.",
            )
        try:
            client = self._client(api_key)
            model_ids = [
                self._normalize_model_id(model.name)
                for model in client.models.list()
                if model.name
            ]
            return ProviderModelsList(ok=True, message="Models listed.", model_ids=model_ids)
        except Exception as exc:
            return ProviderModelsList(
                ok=False,
                message=map_provider_error(self.label, self.env_key, exc),
            )

    def check_availability(self, model: VisionModel, api_key: str) -> ModelAvailabilityStatus:
        if not api_key.strip():
            return ModelAvailabilityStatus(
                ok=False,
                message=f"{self.env_key} is not set.",
                provider=self.provider_id,
                model_id=model.id,
            )
        listed = self.list_available_models(api_key)
        if not listed.ok:
            return ModelAvailabilityStatus(
                ok=False,
                message=listed.message,
                provider=self.provider_id,
                model_id=model.id,
            )
        if model.api_model not in listed.model_ids:
            return ModelAvailabilityStatus(
                ok=False,
                message=(
                    f"API key is valid, but model {model.api_model} is not available on your "
                    f"{self.label} account."
                ),
                provider=self.provider_id,
                model_id=model.id,
                missing_models=[model.api_model],
            )
        return ModelAvailabilityStatus(
            ok=True,
            message=f"{model.label} is available on {self.label}.",
            provider=self.provider_id,
            model_id=model.id,
        )

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
    ) -> AnalysisResult:
        image_bytes = Path(image_path).read_bytes()
        instructions_text = instructions.strip()
        user_text = user_prompt.strip()

        parts: list[types.Part] = [
            types.Part.from_bytes(data=image_bytes, mime_type=image_content_type),
        ]
        prompt_parts: list[str] = []
        if instructions_text:
            prompt_parts.append(instructions_text)
        if user_text:
            prompt_parts.append(user_text)
        if prompt_parts:
            parts.append(types.Part.from_text(text="\n\n".join(prompt_parts)))
        elif not instructions_text and not user_text:
            parts.append(types.Part.from_text(text="Describe this image."))

        api_request = build_api_request_dict(
            vision_model_id=model.id,
            api_model=model.api_model,
            instructions=instructions_text,
            user_prompt=user_text,
            api_config=api_config,
        )

        client = self._client(api_key)
        request_started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        response = client.models.generate_content(
            model=model.api_model,
            contents=types.Content(role="user", parts=parts),
            config=types.GenerateContentConfig(
                max_output_tokens=api_config.max_output_tokens,
            ),
        )
        request_finished_at = datetime.now(timezone.utc)
        latency_wall_seconds = round(time.perf_counter() - started_perf, 3)

        response_text = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        usage_raw: dict[str, Any] = {}
        input_tokens = None
        output_tokens = None
        total_tokens = None
        if usage is not None:
            usage_raw = {
                "prompt_token_count": getattr(usage, "prompt_token_count", None),
                "candidates_token_count": getattr(usage, "candidates_token_count", None),
                "total_token_count": getattr(usage, "total_token_count", None),
            }
            input_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)
            total_tokens = getattr(usage, "total_token_count", None)

        return AnalysisResult(
            response_text=response_text,
            request_started_at=request_started_at,
            request_finished_at=request_finished_at,
            latency_wall_seconds=latency_wall_seconds,
            latency_provider_seconds=latency_wall_seconds,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            reasoning_tokens=None,
            cached_tokens=None,
            cache_write_tokens=None,
            usage_raw=usage_raw,
            api_request=api_request,
            api_response={
                "model": model.api_model,
                "text": response_text[:500],
                "usage": usage_raw,
            },
            provider_response_id="",
            response_model=model.api_model,
            provider_status="completed",
        )
