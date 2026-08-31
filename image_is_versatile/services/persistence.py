"""Persistence helpers for ImageAnalysis records."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone as django_timezone

from image_is_versatile.models import AnalysisStatus, ImageAnalysis

from .analysis import AnalysisResult


def save_success_analysis(*, analysis: ImageAnalysis, result: AnalysisResult) -> ImageAnalysis:
    analysis.status = AnalysisStatus.COMPLETED
    analysis.response_text = result.response_text
    analysis.error_message = ""
    analysis.error_type = ""
    analysis.provider_response_id = result.provider_response_id
    analysis.response_model = result.response_model
    analysis.provider_status = result.provider_status
    analysis.request_started_at = result.request_started_at
    analysis.request_finished_at = result.request_finished_at
    analysis.latency_wall_seconds = result.latency_wall_seconds
    analysis.latency_provider_seconds = result.latency_provider_seconds
    analysis.time_to_first_token_seconds = result.time_to_first_token_seconds
    analysis.input_tokens = result.input_tokens
    analysis.output_tokens = result.output_tokens
    analysis.total_tokens = result.total_tokens
    analysis.reasoning_tokens = result.reasoning_tokens
    analysis.cached_tokens = result.cached_tokens
    analysis.cache_write_tokens = result.cache_write_tokens
    analysis.usage_raw = result.usage_raw
    analysis.api_request = result.api_request
    analysis.api_response = result.api_response
    analysis.completed_at = django_timezone.now()
    analysis.save()
    return analysis


def save_error_analysis(
    *,
    analysis: ImageAnalysis,
    error: Exception,
    request_started_at: datetime | None = None,
    request_finished_at: datetime | None = None,
    latency_wall_seconds: float | None = None,
    api_request: dict | None = None,
) -> ImageAnalysis:
    started = request_started_at or django_timezone.now()
    finished = request_finished_at or django_timezone.now()
    analysis.status = AnalysisStatus.ERROR
    analysis.error_message = str(error)
    analysis.error_type = type(error).__name__
    analysis.request_started_at = started
    analysis.request_finished_at = finished
    analysis.latency_wall_seconds = latency_wall_seconds
    if api_request is not None:
        analysis.api_request = api_request
    analysis.completed_at = django_timezone.now()
    analysis.save()
    return analysis
