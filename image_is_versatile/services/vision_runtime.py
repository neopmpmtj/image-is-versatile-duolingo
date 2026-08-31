"""Load and save runtime vision API parameters (overrides vision_defaults.py)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from django.conf import settings

REASONING_EFFORT_CHOICES = ("none", "low", "high", "max")
IMAGE_DETAIL_CHOICES = ("auto", "low", "high", "original")
MAX_OUTPUT_TOKENS_MIN = 1
MAX_OUTPUT_TOKENS_MAX = 32000

RUNTIME_PATH = Path(settings.BASE_DIR) / "config" / "vision_runtime.json"


def get_defaults() -> dict[str, Any]:
    return {
        "reasoning_effort": settings.VISION_REASONING_EFFORT,
        "max_output_tokens": settings.VISION_MAX_OUTPUT_TOKENS,
        "image_detail": settings.VISION_IMAGE_DETAIL,
    }


def _validate_params(
    reasoning_effort: str,
    max_output_tokens: int,
    image_detail: str,
) -> dict[str, Any]:
    effort = str(reasoning_effort).strip().lower()
    detail = str(image_detail).strip().lower()
    if effort not in REASONING_EFFORT_CHOICES:
        raise ValueError(
            f"reasoning_effort must be one of: {', '.join(REASONING_EFFORT_CHOICES)}"
        )
    if detail not in IMAGE_DETAIL_CHOICES:
        raise ValueError(
            f"image_detail must be one of: {', '.join(IMAGE_DETAIL_CHOICES)}"
        )
    try:
        tokens = int(max_output_tokens)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_output_tokens must be an integer.") from exc
    if tokens < MAX_OUTPUT_TOKENS_MIN or tokens > MAX_OUTPUT_TOKENS_MAX:
        raise ValueError(
            f"max_output_tokens must be between {MAX_OUTPUT_TOKENS_MIN} "
            f"and {MAX_OUTPUT_TOKENS_MAX}."
        )
    return {
        "reasoning_effort": effort,
        "max_output_tokens": tokens,
        "image_detail": detail,
    }


def _read_runtime_file() -> dict[str, Any] | None:
    if not RUNTIME_PATH.is_file():
        return None
    try:
        data = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return _validate_params(
            data.get("reasoning_effort", ""),
            data.get("max_output_tokens", 0),
            data.get("image_detail", ""),
        )
    except ValueError:
        return None


def get_active_vision_params() -> dict[str, Any]:
    runtime = _read_runtime_file()
    if runtime is not None:
        return runtime
    return get_defaults()


def save_vision_params(
    reasoning_effort: str,
    max_output_tokens: int,
    image_detail: str,
) -> dict[str, Any]:
    params = _validate_params(reasoning_effort, max_output_tokens, image_detail)
    RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(params, indent=2, sort_keys=True) + "\n"
    fd, tmp_path = tempfile.mkstemp(
        dir=RUNTIME_PATH.parent,
        prefix=".vision_runtime.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, RUNTIME_PATH)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return params


def reset_vision_params() -> None:
    if RUNTIME_PATH.is_file():
        RUNTIME_PATH.unlink()


def is_using_runtime_file() -> bool:
    return _read_runtime_file() is not None
