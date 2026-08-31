"""English fallback strings for server responses and flash messages."""

from __future__ import annotations

import json
from typing import Any


MESSAGES_EN: dict[str, str] = {
    "analysis_completed": "Analysis completed.",
    "analysis_failed": "Analysis failed: {detail}",
    "analysis_save_failed": "The model responded, but saving the result failed: {detail}",
    "settings_saved": "Settings saved.",
    "settings_reset": "Vision parameters reset to factory defaults.",
    "unknown_vision_model": "Unknown vision model selected.",
    "additional_required_when_omit": (
        "Enter additional instructions when system instructions are omitted."
    ),
    "invalid_preset": "Select a valid system-instruction preset.",
    "image_required": "Upload an image to analyze.",
    "image_invalid": "Upload a valid PNG, JPEG, WebP, or GIF image.",
    "image_too_large": "Image is too large. Maximum size is 20 MB.",
    "api_key_missing": "{env_key} is not set.",
    "model_available": "{model} is available on {provider}.",
    "model_not_on_account": (
        "API key is valid, but model {api_model} is not available on your {provider} account."
    ),
    "unknown_model": "Unknown model: {model_id}",
    "provider_auth_rejected": "{env_key} was rejected by {provider} (invalid or revoked).",
    "provider_permission_denied": (
        "{env_key} is valid but lacks permission to list models on {provider}."
    ),
    "provider_rate_limited": "{provider} rate limit reached. Try again shortly.",
    "provider_unreachable": "Could not reach {provider}. Check your network.",
    "provider_timeout": "{provider} did not respond in time. Try again.",
    "provider_unexpected_error": "Unexpected error from {provider}: {detail}",
    "checking_model_availability": "Checking model availability…",
}


def en(code: str, **vars: Any) -> str:
    text = MESSAGES_EN.get(code, code)
    for name, value in vars.items():
        text = text.replace(f"{{{name}}}", str(value))
    return text


def flash_payload(code: str, **vars: Any) -> str:
    if vars:
        return json.dumps({"code": code, "vars": vars})
    return code


def flash_fallback(message: str) -> str:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return en(message)
    code = payload.get("code", message)
    vars_dict = payload.get("vars") or {}
    return en(code, **vars_dict)
