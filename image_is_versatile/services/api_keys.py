"""Load and save runtime API key overrides (persist across process restarts).

Saved keys take precedence over Django settings / .env. An empty or missing
entry falls back to the environment. The file is not part of the catalog;
keep it out of version control.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from django.conf import settings

KEYS_PATH = Path(settings.BASE_DIR) / "config" / "api_keys.json"
MAX_KEY_LENGTH = 1024


def mask_api_key(key: str) -> str:
    cleaned = (key or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= 4:
        return "•" * len(cleaned)
    return "••••" + cleaned[-4:]


def _known_provider_ids() -> set[str]:
    return set(settings.VISION_PROVIDERS)


def _validate_key(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("API key must be a string.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("API key cannot be empty.")
    if "\n" in cleaned or "\r" in cleaned:
        raise ValueError("API key cannot contain line breaks.")
    if len(cleaned) > MAX_KEY_LENGTH:
        raise ValueError(f"API key must be at most {MAX_KEY_LENGTH} characters.")
    return cleaned


def _read_keys_file() -> dict[str, str]:
    if not KEYS_PATH.is_file():
        return {}
    try:
        data = json.loads(KEYS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    known = _known_provider_ids()
    result: dict[str, str] = {}
    for provider_id, raw in data.items():
        if provider_id not in known or not isinstance(raw, str):
            continue
        cleaned = raw.strip()
        if cleaned:
            result[provider_id] = cleaned
    return result


def _write_keys_file(keys: dict[str, str]) -> None:
    KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(keys, indent=2, sort_keys=True) + "\n"
    fd, tmp_path = tempfile.mkstemp(
        dir=KEYS_PATH.parent,
        prefix=".api_keys.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, KEYS_PATH)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    try:
        os.chmod(KEYS_PATH, 0o600)
    except OSError:
        pass


def get_override_api_key(provider_id: str) -> str:
    return _read_keys_file().get(provider_id, "")


def get_env_api_key(provider_id: str) -> str:
    config = settings.VISION_PROVIDERS.get(provider_id)
    if not config:
        raise KeyError(f"Unknown provider id: {provider_id}")
    env_key = config["env_key"]
    return getattr(settings, env_key, "") or ""


def save_api_key_updates(
    *,
    updates: dict[str, str],
    clears: list[str] | None = None,
) -> dict[str, str]:
    current = _read_keys_file()
    clear_ids = set(clears or [])
    known = _known_provider_ids()
    for provider_id in clear_ids:
        if provider_id not in known:
            raise ValueError(f"Unknown provider id: {provider_id}")
        current.pop(provider_id, None)
    for provider_id, value in updates.items():
        if provider_id in clear_ids:
            continue
        if provider_id not in known:
            raise ValueError(f"Unknown provider id: {provider_id}")
        current[provider_id] = _validate_key(value)
    current = {k: v for k, v in current.items() if v}
    if not current:
        reset_api_keys()
        return {}
    _write_keys_file(current)
    return current


def reset_api_keys() -> None:
    if KEYS_PATH.is_file():
        KEYS_PATH.unlink()


def is_using_saved_keys() -> bool:
    return bool(_read_keys_file())


def list_provider_key_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    overrides = _read_keys_file()
    for provider_id, config in settings.VISION_PROVIDERS.items():
        env_key = config["env_key"]
        override = overrides.get(provider_id, "")
        env_value = getattr(settings, env_key, "") or ""
        if override:
            source = "saved"
            masked = mask_api_key(override)
        elif env_value.strip():
            source = "env"
            masked = mask_api_key(env_value)
        else:
            source = "missing"
            masked = ""
        rows.append(
            {
                "provider_id": provider_id,
                "label": config.get("label", provider_id),
                "env_key": env_key,
                "source": source,
                "masked": masked,
                "has_override": bool(override),
            }
        )
    return rows
