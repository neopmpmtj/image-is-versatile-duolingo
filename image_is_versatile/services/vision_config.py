"""Shared vision API request configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings

from image_is_versatile.services.vision_runtime import get_active_vision_params


@dataclass(frozen=True)
class VisionApiRequestConfig:
    reasoning_effort: str
    max_output_tokens: int
    image_detail: str

    @classmethod
    def from_active(cls) -> VisionApiRequestConfig:
        params = get_active_vision_params()
        return cls(
            reasoning_effort=params["reasoning_effort"],
            max_output_tokens=params["max_output_tokens"],
            image_detail=params["image_detail"],
        )

    @classmethod
    def from_settings(cls) -> VisionApiRequestConfig:
        return cls.from_active()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> VisionApiRequestConfig:
        if not data:
            return cls.from_active()
        reasoning = data.get("reasoning") if isinstance(data.get("reasoning"), dict) else {}
        effort = reasoning.get("effort") or data.get("reasoning_effort")
        active = get_active_vision_params()
        return cls(
            reasoning_effort=str(effort or active["reasoning_effort"]),
            max_output_tokens=int(
                data.get("max_output_tokens") or active["max_output_tokens"]
            ),
            image_detail=str(data.get("image_detail") or active["image_detail"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning": {"effort": self.reasoning_effort},
            "max_output_tokens": self.max_output_tokens,
            "image_detail": self.image_detail,
        }


def build_api_request_dict(
    *,
    vision_model_id: str,
    api_model: str,
    instructions: str,
    user_prompt: str,
    api_config: VisionApiRequestConfig | None = None,
    omit_instructions: bool = False,
    prompt_preset: str = "",
) -> dict[str, Any]:
    config = api_config or VisionApiRequestConfig.from_active()
    return {
        "vision_model_id": vision_model_id,
        "api_model": api_model,
        "omit_instructions": omit_instructions,
        "prompt_preset": prompt_preset,
        "instructions": instructions.strip(),
        "user_prompt": user_prompt.strip(),
        **config.to_dict(),
    }
