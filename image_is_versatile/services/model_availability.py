"""Model availability pre-check with per-provider session cache."""

from __future__ import annotations

from typing import Any

from image_is_versatile.services.model_registry import get_model
from image_is_versatile.services.providers.base import ModelAvailabilityStatus
from image_is_versatile.services.provider_registry import get_adapter, get_api_key


def _session_cache_key(provider_id: str) -> str:
    return f"vision_provider_{provider_id}"


def _get_cached_model_ids(session: dict[str, Any], provider_id: str, api_key: str) -> list[str] | None:
    cached = session.get(_session_cache_key(provider_id))
    if cached and cached.get("key") == api_key and cached.get("ok"):
        return cached.get("model_ids")
    return None


def _set_cached_model_ids(
    session: dict[str, Any],
    provider_id: str,
    api_key: str,
    ok: bool,
    model_ids: list[str],
) -> None:
    session[_session_cache_key(provider_id)] = {
        "key": api_key,
        "ok": ok,
        "model_ids": model_ids,
    }


def check_model_availability(
    model_id: str,
    session: dict[str, Any] | None = None,
    force_recheck: bool = False,
) -> ModelAvailabilityStatus:
    model = get_model(model_id)
    provider_id = model.provider
    api_key = get_api_key(provider_id)
    adapter = get_adapter(provider_id)

    if not api_key.strip():
        from image_is_versatile.services.provider_registry import get_provider_config

        env_key = get_provider_config(provider_id)["env_key"]
        return ModelAvailabilityStatus(
            ok=False,
            message=f"{env_key} is not set.",
            provider=provider_id,
            model_id=model.id,
        )

    model_ids: list[str] | None = None
    if session is not None and not force_recheck:
        model_ids = _get_cached_model_ids(session, provider_id, api_key)

    if model_ids is None:
        listed = adapter.list_available_models(api_key)
        if session is not None:
            _set_cached_model_ids(
                session,
                provider_id,
                api_key,
                listed.ok,
                listed.model_ids,
            )
        if not listed.ok:
            return ModelAvailabilityStatus(
                ok=False,
                message=listed.message,
                provider=provider_id,
                model_id=model.id,
            )
        model_ids = listed.model_ids

    if model.api_model not in model_ids:
        return ModelAvailabilityStatus(
            ok=False,
            message=(
                f"API key is valid, but model {model.api_model} is not available on your account."
            ),
            provider=provider_id,
            model_id=model.id,
            missing_models=[model.api_model],
        )

    from image_is_versatile.services.provider_registry import get_provider_config

    label = get_provider_config(provider_id).get("label", provider_id)
    return ModelAvailabilityStatus(
        ok=True,
        message=f"{model.label} is available on {label}.",
        provider=provider_id,
        model_id=model.id,
    )
