"""Routes vision analysis to the correct provider adapter."""

from __future__ import annotations

from pathlib import Path

from image_is_versatile.services.analysis import AnalysisResult
from image_is_versatile.services.model_registry import get_model
from image_is_versatile.services.provider_registry import get_adapter, get_api_key
from image_is_versatile.services.vision_config import VisionApiRequestConfig


def analyze_image(
    *,
    model_id: str,
    instructions: str = "",
    user_prompt: str = "",
    image_path: Path | str,
    image_content_type: str = "image/jpeg",
    api_config: VisionApiRequestConfig | None = None,
) -> AnalysisResult:
    model = get_model(model_id)
    adapter = get_adapter(model.provider)
    api_key = get_api_key(model.provider)
    config = api_config or VisionApiRequestConfig.from_active()
    return adapter.analyze(
        model,
        instructions=instructions,
        user_prompt=user_prompt,
        image_path=str(image_path),
        image_content_type=image_content_type,
        api_config=config,
        api_key=api_key,
    )
