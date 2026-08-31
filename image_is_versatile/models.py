import uuid

from django.db import models
from django.utils import timezone


class AnalysisStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    ERROR = "error", "Error"


class ImageAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to="uploads/%Y/%m/%d/")
    image_name = models.CharField(max_length=255)
    image_content_type = models.CharField(max_length=100, default="image/jpeg")
    image_size_bytes = models.PositiveIntegerField(null=True, blank=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    instructions = models.TextField(blank=True, default="")
    user_prompt = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    api_defaults = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.IN_PROGRESS,
    )
    vision_model_id = models.CharField(max_length=64)
    provider = models.CharField(max_length=32)
    api_model = models.CharField(max_length=100)
    response_text = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    error_type = models.CharField(max_length=255, blank=True)
    provider_response_id = models.CharField(max_length=255, blank=True)
    response_model = models.CharField(max_length=100, blank=True)
    provider_status = models.CharField(max_length=50, blank=True)
    request_started_at = models.DateTimeField(null=True, blank=True)
    request_finished_at = models.DateTimeField(null=True, blank=True)
    latency_wall_seconds = models.FloatField(null=True, blank=True)
    latency_provider_seconds = models.FloatField(null=True, blank=True)
    time_to_first_token_seconds = models.FloatField(null=True, blank=True)
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    total_tokens = models.PositiveIntegerField(null=True, blank=True)
    reasoning_tokens = models.PositiveIntegerField(null=True, blank=True)
    cached_tokens = models.PositiveIntegerField(null=True, blank=True)
    cache_write_tokens = models.PositiveIntegerField(null=True, blank=True)
    usage_raw = models.JSONField(default=dict, blank=True)
    api_request = models.JSONField(default=dict, blank=True)
    api_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Analysis {self.id} ({self.image_name})"

    @property
    def is_success(self) -> bool:
        return self.status == AnalysisStatus.COMPLETED

    @property
    def display_label(self) -> str:
        from image_is_versatile.services.model_registry import get_model

        try:
            return get_model(self.vision_model_id).label
        except KeyError:
            return self.api_model or self.vision_model_id

    @property
    def provider_label(self) -> str:
        from django.conf import settings

        provider_cfg = settings.VISION_PROVIDERS.get(self.provider, {})
        return provider_cfg.get("label", self.provider)

    def mark_completed(self) -> None:
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = timezone.now()
