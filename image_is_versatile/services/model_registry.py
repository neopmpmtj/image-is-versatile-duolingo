"""Vision model catalog loaded from Django settings."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class VisionModel:
    id: str
    label: str
    provider: str
    api_model: str


def _load_models() -> dict[str, VisionModel]:
    models: dict[str, VisionModel] = {}
    for entry in settings.VISION_MODELS:
        model = VisionModel(
            id=entry["id"],
            label=entry["label"],
            provider=entry["provider"],
            api_model=entry["api_model"],
        )
        models[model.id] = model
    return models


def get_model(model_id: str) -> VisionModel:
    models = _load_models()
    if model_id not in models:
        raise KeyError(f"Unknown vision model id: {model_id}")
    return models[model_id]


def all_models() -> list[VisionModel]:
    return list(_load_models().values())


def model_choices() -> list[tuple[str, str]]:
    return [(m.id, m.label) for m in all_models()]


def default_model_id() -> str:
    return settings.VISION_DEFAULT_MODEL_ID
