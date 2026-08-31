"""Provider adapter protocol and shared types."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from image_is_versatile.i18n import en
from image_is_versatile.services.analysis import AnalysisResult
from image_is_versatile.services.model_registry import VisionModel
from image_is_versatile.services.vision_config import VisionApiRequestConfig

PROVIDER_LIST_TIMEOUT_SECONDS = 12
PROVIDER_ANALYZE_TIMEOUT_SECONDS = 180

_API_MODEL_VERSION_SUFFIX = re.compile(r"(?:-\d{3}|-\d{4}-\d{2}-\d{2})$")
_TIMEOUT_EXC_NAMES = frozenset(
    {
        "APITimeoutError",
        "TimeoutException",
        "TimeoutError",
        "ReadTimeout",
        "ConnectTimeout",
        "WriteTimeout",
        "PoolTimeout",
    }
)
_AUTH_EXC_NAMES = frozenset({"AuthenticationError"})
_PERMISSION_EXC_NAMES = frozenset({"PermissionDeniedError"})
_RATE_EXC_NAMES = frozenset({"RateLimitError"})
_CONNECT_EXC_NAMES = frozenset({"APIConnectionError", "ConnectError"})


@dataclass(frozen=True)
class ModelAvailabilityStatus:
    ok: bool
    message: str
    provider: str
    model_id: str
    code: str = ""
    vars: dict[str, Any] = field(default_factory=dict)
    missing_models: list[str] = field(default_factory=list)

    def to_api_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "ok": self.ok,
            "code": self.code,
            "message": self.message,
            "provider": self.provider,
            "model_id": self.model_id,
        }
        data.update(self.vars)
        return data


@dataclass(frozen=True)
class ProviderModelsList:
    ok: bool
    message: str
    code: str = ""
    vars: dict[str, Any] = field(default_factory=dict)
    model_ids: list[str] = field(default_factory=list)


class VisionProviderAdapter(Protocol):
    provider_id: str

    def list_available_models(self, api_key: str) -> ProviderModelsList: ...

    def check_availability(self, model: VisionModel, api_key: str) -> ModelAvailabilityStatus: ...

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
    ) -> AnalysisResult: ...


def api_model_is_listed(api_model: str, model_ids: list[str]) -> bool:
    """True if catalog id is listed, or listed as a dated/numeric revision."""
    if api_model in model_ids:
        return True
    for listed in model_ids:
        if not listed.startswith(api_model):
            continue
        rest = listed[len(api_model) :]
        if rest and _API_MODEL_VERSION_SUFFIX.fullmatch(rest):
            return True
    return False


def _http_status(exc: Exception) -> int | None:
    raw = getattr(exc, "status_code", None)
    if raw is None:
        raw = getattr(exc, "code", None)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


def map_provider_error(provider_label: str, env_key: str, exc: Exception) -> tuple[str, dict[str, str], str]:
    exc_name = type(exc).__name__
    http_code = _http_status(exc)
    status_str = str(getattr(exc, "status", "") or "").upper()

    if exc_name in _TIMEOUT_EXC_NAMES:
        code = "provider_timeout"
        vars_dict = {"provider": provider_label}
    elif (
        exc_name in _AUTH_EXC_NAMES
        or http_code == 401
        or status_str in {"UNAUTHORIZED", "UNAUTHENTICATED"}
    ):
        code = "provider_auth_rejected"
        vars_dict = {"env_key": env_key, "provider": provider_label}
    elif (
        exc_name in _PERMISSION_EXC_NAMES
        or http_code == 403
        or status_str == "PERMISSION_DENIED"
    ):
        code = "provider_permission_denied"
        vars_dict = {"env_key": env_key, "provider": provider_label}
    elif (
        exc_name in _RATE_EXC_NAMES
        or http_code == 429
        or status_str in {"RESOURCE_EXHAUSTED", "TOO_MANY_REQUESTS"}
    ):
        code = "provider_rate_limited"
        vars_dict = {"provider": provider_label}
    elif exc_name in _CONNECT_EXC_NAMES or http_code in {408, 502, 503, 504}:
        code = "provider_unreachable"
        vars_dict = {"provider": provider_label}
    else:
        code = "provider_unexpected_error"
        vars_dict = {"provider": provider_label, "detail": str(exc)}
    return code, vars_dict, en(code, **vars_dict)
