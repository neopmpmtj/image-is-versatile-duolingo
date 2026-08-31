"""OpenAI Responses API adapter (OpenAI and DeepSeek base URLs)."""

from __future__ import annotations

import base64
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from image_is_versatile.services.analysis import AnalysisResult
from image_is_versatile.services.model_registry import VisionModel
from image_is_versatile.i18n import en
from image_is_versatile.services.providers.base import (
    PROVIDER_ANALYZE_TIMEOUT_SECONDS,
    PROVIDER_LIST_TIMEOUT_SECONDS,
    ModelAvailabilityStatus,
    ProviderModelsList,
    api_model_is_listed,
    map_provider_error,
)
from image_is_versatile.services.vision_config import VisionApiRequestConfig, build_api_request_dict


class OpenAIResponsesAdapter:
    def __init__(self, provider_id: str, config: dict[str, Any]) -> None:
        self.provider_id = provider_id
        self._config = config
        self.label = config.get("label", provider_id)
        self.env_key = config["env_key"]
        self.base_url = config.get("base_url")

    def _client(self, api_key: str, *, timeout: float, max_retries: int = 0) -> OpenAI:
        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": timeout,
            "max_retries": max_retries,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def list_available_models(self, api_key: str) -> ProviderModelsList:
        if not api_key.strip():
            vars_dict = {"env_key": self.env_key}
            return ProviderModelsList(
                ok=False,
                code="api_key_missing",
                vars=vars_dict,
                message=en("api_key_missing", **vars_dict),
            )
        try:
            client = self._client(api_key, timeout=PROVIDER_LIST_TIMEOUT_SECONDS)
            model_ids = [model.id for model in client.models.list()]
            return ProviderModelsList(ok=True, message="Models listed.", model_ids=model_ids)
        except Exception as exc:
            code, vars_dict, message = map_provider_error(self.label, self.env_key, exc)
            return ProviderModelsList(
                ok=False,
                code=code,
                vars=vars_dict,
                message=message,
            )

    def check_availability(self, model: VisionModel, api_key: str) -> ModelAvailabilityStatus:
        if not api_key.strip():
            vars_dict = {"env_key": self.env_key}
            return ModelAvailabilityStatus(
                ok=False,
                code="api_key_missing",
                vars=vars_dict,
                message=en("api_key_missing", **vars_dict),
                provider=self.provider_id,
                model_id=model.id,
            )
        listed = self.list_available_models(api_key)
        if not listed.ok:
            return ModelAvailabilityStatus(
                ok=False,
                code=listed.code,
                vars=dict(listed.vars),
                message=listed.message,
                provider=self.provider_id,
                model_id=model.id,
            )
        if not api_model_is_listed(model.api_model, listed.model_ids):
            vars_dict = {"api_model": model.api_model, "provider": self.label}
            return ModelAvailabilityStatus(
                ok=False,
                code="model_not_on_account",
                vars=vars_dict,
                message=en("model_not_on_account", **vars_dict),
                provider=self.provider_id,
                model_id=model.id,
                missing_models=[model.api_model],
            )
        vars_dict = {"model": model.label, "provider": self.label}
        return ModelAvailabilityStatus(
            ok=True,
            code="model_available",
            vars=vars_dict,
            message=en("model_available", **vars_dict),
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
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{image_content_type};base64,{encoded_image}"
        instructions_text = instructions.strip()
        user_text = user_prompt.strip()

        content: list[dict[str, Any]] = []
        if user_text:
            content.append({"type": "input_text", "text": user_text})
        content.append(
            {
                "type": "input_image",
                "image_url": image_data_url,
                "detail": api_config.image_detail,
            }
        )

        api_request = build_api_request_dict(
            vision_model_id=model.id,
            api_model=model.api_model,
            instructions=instructions_text,
            user_prompt=user_text,
            api_config=api_config,
        )

        create_kwargs: dict[str, Any] = {
            "model": model.api_model,
            "input": [{"role": "user", "content": content}],
            "reasoning": {"effort": api_config.reasoning_effort},
            "max_output_tokens": api_config.max_output_tokens,
        }
        if instructions_text:
            create_kwargs["instructions"] = instructions_text

        client = self._client(api_key, timeout=PROVIDER_ANALYZE_TIMEOUT_SECONDS)
        request_started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        response = client.responses.create(**create_kwargs)
        request_finished_at = datetime.now(timezone.utc)
        latency_wall_seconds = round(time.perf_counter() - started_perf, 3)
        usage = getattr(response, "usage", None)
        usage_raw: dict[str, Any] = {}
        if usage is not None and hasattr(usage, "model_dump"):
            usage_raw = usage.model_dump(mode="json")

        return AnalysisResult(
            response_text=response.output_text,
            request_started_at=request_started_at,
            request_finished_at=request_finished_at,
            latency_wall_seconds=latency_wall_seconds,
            latency_provider_seconds=_provider_latency_seconds(response),
            input_tokens=_usage_value(usage, "input_tokens"),
            output_tokens=_usage_value(usage, "output_tokens"),
            total_tokens=_usage_value(usage, "total_tokens"),
            reasoning_tokens=_usage_value(usage, "output_tokens_details", "reasoning_tokens"),
            cached_tokens=_usage_value(usage, "input_tokens_details", "cached_tokens"),
            cache_write_tokens=_usage_value(usage, "input_tokens_details", "cache_write_tokens"),
            usage_raw=usage_raw,
            api_request=api_request,
            api_response=_response_snapshot(response),
            provider_response_id=getattr(response, "id", "") or "",
            response_model=str(getattr(response, "model", "") or model.api_model),
            provider_status=str(getattr(response, "status", "") or ""),
        )


def _usage_value(usage: Any, attr: str, nested_attr: str | None = None) -> int | None:
    if usage is None:
        return None
    if nested_attr:
        nested = getattr(usage, attr, None)
        if nested is None:
            return None
        return getattr(nested, nested_attr, None)
    return getattr(usage, attr, None)


def _response_snapshot(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        data = response.model_dump(mode="json", exclude_none=True)
    else:
        data = {}
    return {
        "id": getattr(response, "id", ""),
        "model": str(getattr(response, "model", "")),
        "status": str(getattr(response, "status", "") or ""),
        "created_at": getattr(response, "created_at", None),
        "completed_at": getattr(response, "completed_at", None),
        "usage": data.get("usage"),
    }


def _provider_latency_seconds(response: Any) -> float | None:
    created_at = getattr(response, "created_at", None)
    completed_at = getattr(response, "completed_at", None)
    if created_at is None or completed_at is None:
        return None
    return round(float(completed_at) - float(created_at), 3)
