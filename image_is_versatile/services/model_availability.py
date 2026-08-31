"""Model availability pre-check with per-provider session cache."""

from __future__ import annotations

import time
from typing import Any

from image_is_versatile.i18n import en
from image_is_versatile.services.model_registry import get_model
from image_is_versatile.services.providers.base import (
    ModelAvailabilityStatus,
    api_model_is_listed,
)
from image_is_versatile.services.provider_registry import get_adapter, get_api_key

CACHE_OK_TTL_SECONDS = 300
CACHE_FAIL_TTL_SECONDS = 20


def _session_cache_key(provider_id: str) -> str:
    return f"vision_provider_{provider_id}"


def _cache_age_seconds(cached: dict[str, Any]) -> float:
    cached_at = cached.get("cached_at")
    if not isinstance(cached_at, (int, float)):
        return 0.0
    return max(0.0, time.time() - cached_at)


def _get_cached_listing(
    session: dict[str, Any], provider_id: str, api_key: str
) -> dict[str, Any] | None:
    cached = session.get(_session_cache_key(provider_id))
    if not cached or cached.get("key") != api_key:
        return None
    ttl = CACHE_OK_TTL_SECONDS if cached.get("ok") else CACHE_FAIL_TTL_SECONDS
    if _cache_age_seconds(cached) > ttl:
        return None
    return cached


def _set_cached_listing(
    session: dict[str, Any],
    provider_id: str,
    api_key: str,
    *,
    ok: bool,
    model_ids: list[str],
    code: str = "",
    vars: dict[str, Any] | None = None,
    message: str = "",
) -> None:
    session[_session_cache_key(provider_id)] = {
        "key": api_key,
        "ok": ok,
        "model_ids": model_ids,
        "code": code,
        "vars": vars or {},
        "message": message,
        "cached_at": time.time(),
    }


def check_model_availability(
    model_id: str,
    session: dict[str, Any] | None = None,
    force_recheck: bool = False,
    list_models: bool = True,
) -> ModelAvailabilityStatus:
    from image_is_versatile.services.provider_registry import get_provider_config

    model = get_model(model_id)
    provider_id = model.provider
    api_key = get_api_key(provider_id)
    adapter = get_adapter(provider_id)
    provider_label = get_provider_config(provider_id).get("label", provider_id)

    if not api_key.strip():
        env_key = get_provider_config(provider_id)["env_key"]
        vars_dict = {"env_key": env_key}
        return ModelAvailabilityStatus(
            ok=False,
            code="api_key_missing",
            vars=vars_dict,
            message=en("api_key_missing", **vars_dict),
            provider=provider_id,
            model_id=model.id,
        )

    if not list_models:
        vars_dict = {"model": model.label, "provider": provider_label}
        return ModelAvailabilityStatus(
            ok=True,
            code="checking_model_availability",
            vars=vars_dict,
            message=en("checking_model_availability"),
            provider=provider_id,
            model_id=model.id,
        )

    cached = None
    if session is not None and not force_recheck:
        cached = _get_cached_listing(session, provider_id, api_key)

    if cached is not None and not cached.get("ok"):
        return ModelAvailabilityStatus(
            ok=False,
            code=cached.get("code") or "provider_unexpected_error",
            vars=dict(cached.get("vars") or {}),
            message=cached.get("message") or "",
            provider=provider_id,
            model_id=model.id,
        )

    if cached is not None:
        model_ids = list(cached.get("model_ids") or [])
    else:
        listed = adapter.list_available_models(api_key)
        if session is not None:
            _set_cached_listing(
                session,
                provider_id,
                api_key,
                ok=listed.ok,
                model_ids=listed.model_ids,
                code=listed.code,
                vars=dict(listed.vars),
                message=listed.message,
            )
        if not listed.ok:
            return ModelAvailabilityStatus(
                ok=False,
                code=listed.code,
                vars=dict(listed.vars),
                message=listed.message,
                provider=provider_id,
                model_id=model.id,
            )
        model_ids = listed.model_ids

    if not api_model_is_listed(model.api_model, model_ids):
        vars_dict = {"api_model": model.api_model, "provider": provider_label}
        return ModelAvailabilityStatus(
            ok=False,
            code="model_not_on_account",
            vars=vars_dict,
            message=en("model_not_on_account", **vars_dict),
            provider=provider_id,
            model_id=model.id,
            missing_models=[model.api_model],
        )

    vars_dict = {"model": model.label, "provider": provider_label}
    return ModelAvailabilityStatus(
        ok=True,
        code="model_available",
        vars=vars_dict,
        message=en("model_available", **vars_dict),
        provider=provider_id,
        model_id=model.id,
    )
