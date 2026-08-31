from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from image_is_versatile.models import AnalysisStatus, ImageAnalysis
from image_is_versatile.services.analysis import AnalysisResult
from image_is_versatile.services.persistence import (
    save_error_analysis,
    save_success_analysis,
    save_success_analysis_fallback,
)
from image_is_versatile.services.providers.base import ModelAvailabilityStatus


def _test_image_file(name: str = "sample.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def _sample_result() -> AnalysisResult:
    now = datetime.now(timezone.utc)
    return AnalysisResult(
        response_text="A red square.",
        request_started_at=now,
        request_finished_at=now,
        latency_wall_seconds=1.234,
        latency_provider_seconds=1.1,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        reasoning_tokens=10,
        cached_tokens=0,
        cache_write_tokens=0,
        usage_raw={"input_tokens": 100},
        api_request={"api_model": "deepseek-v4-flash-vision-exp"},
        api_response={"id": "resp_123"},
        provider_response_id="resp_123",
        response_model="deepseek-v4-flash-vision-exp",
        provider_status="completed",
    )


class PersistenceTests(TestCase):
    def _create_analysis(self) -> ImageAnalysis:
        image = SimpleUploadedFile("test.png", b"fake", content_type="image/png")
        return ImageAnalysis.objects.create(
            image=image,
            image_name="test.png",
            vision_model_id="deepseek_flash",
            provider="deepseek",
            api_model="deepseek-v4-flash-vision-exp",
            status=AnalysisStatus.IN_PROGRESS,
        )

    def test_save_success_analysis(self):
        analysis = self._create_analysis()
        save_success_analysis(analysis=analysis, result=_sample_result())
        analysis.refresh_from_db()
        self.assertEqual(analysis.status, AnalysisStatus.COMPLETED)
        self.assertEqual(analysis.response_text, "A red square.")
        self.assertEqual(analysis.provider_response_id, "resp_123")
        self.assertEqual(analysis.input_tokens, 100)

    def test_save_error_analysis(self):
        analysis = self._create_analysis()
        save_error_analysis(
            analysis=analysis,
            error=RuntimeError("API failed"),
            api_request={"api_model": "deepseek-v4-flash-vision-exp"},
        )
        analysis.refresh_from_db()
        self.assertEqual(analysis.status, AnalysisStatus.ERROR)
        self.assertEqual(analysis.error_type, "RuntimeError")
        self.assertIn("API failed", analysis.error_message)

    def test_save_success_analysis_fallback(self):
        analysis = self._create_analysis()
        save_success_analysis_fallback(analysis=analysis, result=_sample_result())
        analysis.refresh_from_db()
        self.assertEqual(analysis.status, AnalysisStatus.COMPLETED)
        self.assertEqual(analysis.response_text, "A red square.")
        self.assertEqual(analysis.provider_response_id, "resp_123")


class ViewTests(TestCase):
    def test_history_page(self):
        response = self.client.get(reverse("image_is_versatile:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "History")

    def test_new_page_renders_form(self):
        response = self.client.get(reverse("image_is_versatile:new"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New analysis")
        self.assertContains(response, "Vision model")

    @patch("image_is_versatile.views.check_model_availability")
    def test_new_page_skips_model_listing(self, mock_check):
        mock_check.return_value = ModelAvailabilityStatus(
            ok=True,
            code="checking_model_availability",
            message="Checking model availability…",
            provider="deepseek",
            model_id="deepseek_flash",
        )
        response = self.client.get(reverse("image_is_versatile:new"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_check.called)
        self.assertFalse(mock_check.call_args.kwargs.get("list_models", True))

    def test_detail_in_progress_not_shown_as_empty_response(self):
        analysis = ImageAnalysis.objects.create(
            image=SimpleUploadedFile("x.png", b"x", content_type="image/png"),
            image_name="x.png",
            vision_model_id="deepseek_flash",
            provider="deepseek",
            api_model="deepseek-v4-flash-vision-exp",
            status=AnalysisStatus.IN_PROGRESS,
        )
        response = self.client.get(
            reverse("image_is_versatile:detail", kwargs={"analysis_id": analysis.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "did not finish")

    @override_settings(DEEPSEEK_API_KEY="")
    def test_model_status_missing_key(self):
        response = self.client.get(
            reverse("image_is_versatile:model_status", kwargs={"model_id": "deepseek_flash"})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["code"], "api_key_missing")
        self.assertIn("DEEPSEEK_API_KEY", data["message"])

    def test_model_status_unknown(self):
        response = self.client.get(
            reverse("image_is_versatile:model_status", kwargs={"model_id": "unknown"})
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["code"], "unknown_model")

    @patch("image_is_versatile.views.analyze_image")
    @patch("image_is_versatile.views.check_model_availability")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_new_post_creates_analysis(self, mock_check, mock_analyze):
        mock_check.return_value = ModelAvailabilityStatus(
            ok=True,
            message="ok",
            provider="deepseek",
            model_id="deepseek_flash",
        )
        mock_analyze.return_value = _sample_result()
        image = _test_image_file()
        response = self.client.post(
            reverse("image_is_versatile:new"),
            {
                "vision_model": "deepseek_flash",
                "image": image,
                "description": "Test session",
                "omit_instructions": False,
                "prompt_preset": "describe",
                "additional": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        analysis = ImageAnalysis.objects.get()
        self.assertEqual(analysis.status, AnalysisStatus.COMPLETED)
        self.assertEqual(analysis.description, "Test session")
        self.assertEqual(analysis.vision_model_id, "deepseek_flash")

    @patch("image_is_versatile.views.analyze_image")
    @patch("image_is_versatile.views.check_model_availability")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_new_post_portuguese_prompt_language(self, mock_check, mock_analyze):
        mock_check.return_value = ModelAvailabilityStatus(
            ok=True,
            message="ok",
            provider="deepseek",
            model_id="deepseek_flash",
        )
        mock_analyze.return_value = _sample_result()
        response = self.client.post(
            reverse("image_is_versatile:new"),
            {
                "vision_model": "deepseek_flash",
                "image": _test_image_file(),
                "description": "",
                "omit_instructions": False,
                "prompt_preset": "describe",
                "additional": "",
                "ui_lang": "pt",
            },
        )
        self.assertEqual(response.status_code, 302)
        analysis = ImageAnalysis.objects.get()
        self.assertIn("Descreva esta imagem com cuidado", analysis.instructions)
        self.assertIn("Responda em português de Portugal.", analysis.instructions)
        _args, kwargs = mock_analyze.call_args
        self.assertIn("Responda em português de Portugal.", kwargs["instructions"])

    @patch("image_is_versatile.views.save_success_analysis")
    @patch("image_is_versatile.views.analyze_image")
    @patch("image_is_versatile.views.check_model_availability")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_new_post_keeps_response_if_full_save_fails(
        self, mock_check, mock_analyze, mock_save
    ):
        mock_check.return_value = ModelAvailabilityStatus(
            ok=True,
            message="ok",
            provider="deepseek",
            model_id="deepseek_flash",
        )
        mock_analyze.return_value = _sample_result()
        mock_save.side_effect = OSError("disk full")
        response = self.client.post(
            reverse("image_is_versatile:new"),
            {
                "vision_model": "deepseek_flash",
                "image": _test_image_file(),
                "description": "Keep this",
                "omit_instructions": False,
                "prompt_preset": "describe",
                "additional": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        analysis = ImageAnalysis.objects.get()
        self.assertEqual(analysis.status, AnalysisStatus.COMPLETED)
        self.assertEqual(analysis.response_text, "A red square.")
        self.assertEqual(analysis.description, "Keep this")

    def test_new_post_requires_image(self):
        response = self.client.post(
            reverse("image_is_versatile:new"),
            {
                "vision_model": "deepseek_flash",
                "omit_instructions": False,
                "prompt_preset": "describe",
                "additional": "",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "image_required", status_code=400)
        self.assertEqual(ImageAnalysis.objects.count(), 0)

    @patch("image_is_versatile.views.check_model_availability")
    def test_new_post_blocked_when_unavailable(self, mock_check):
        mock_check.return_value = ModelAvailabilityStatus(
            ok=False,
            code="api_key_missing",
            vars={"env_key": "DEEPSEEK_API_KEY"},
            message="DEEPSEEK_API_KEY is not set.",
            provider="deepseek",
            model_id="deepseek_flash",
        )
        image = _test_image_file()
        response = self.client.post(
            reverse("image_is_versatile:new"),
            {
                "vision_model": "deepseek_flash",
                "image": image,
                "description": "",
                "omit_instructions": False,
                "prompt_preset": "describe",
                "additional": "",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ImageAnalysis.objects.count(), 0)

    def test_detail_page(self):
        analysis = ImageAnalysis.objects.create(
            image=SimpleUploadedFile("x.png", b"x", content_type="image/png"),
            image_name="x.png",
            vision_model_id="deepseek_flash",
            provider="deepseek",
            api_model="deepseek-v4-flash-vision-exp",
            status=AnalysisStatus.COMPLETED,
            response_text="Done.",
        )
        response = self.client.get(
            reverse("image_is_versatile:detail", kwargs={"analysis_id": analysis.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Done.")

    def test_settings_page(self):
        response = self.client.get(reverse("image_is_versatile:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vision API parameters")
        self.assertContains(response, "Reasoning effort")

    def test_settings_post_saves(self):
        from image_is_versatile.services import vision_runtime

        original_path = vision_runtime.RUNTIME_PATH
        tmp_path = vision_runtime.RUNTIME_PATH.parent / ".test_settings_runtime.json"
        vision_runtime.RUNTIME_PATH = tmp_path
        try:
            if tmp_path.is_file():
                tmp_path.unlink()
            response = self.client.post(
                reverse("image_is_versatile:settings"),
                {
                    "reasoning_effort": "low",
                    "max_output_tokens": "900",
                    "image_detail": "low",
                },
            )
            self.assertEqual(response.status_code, 302)
            self.assertTrue(tmp_path.is_file())
            data = tmp_path.read_text(encoding="utf-8")
            self.assertIn('"reasoning_effort": "low"', data)
        finally:
            if tmp_path.is_file():
                tmp_path.unlink()
            vision_runtime.RUNTIME_PATH = original_path

    def test_settings_reset_without_other_fields(self):
        from image_is_versatile.services import vision_runtime

        original_path = vision_runtime.RUNTIME_PATH
        tmp_path = vision_runtime.RUNTIME_PATH.parent / ".test_settings_reset.json"
        vision_runtime.RUNTIME_PATH = tmp_path
        try:
            tmp_path.write_text('{"reasoning_effort": "low", "max_output_tokens": 9, "image_detail": "low"}\n')
            response = self.client.post(
                reverse("image_is_versatile:settings"),
                {"action": "reset"},
            )
            self.assertEqual(response.status_code, 302)
            self.assertFalse(tmp_path.is_file())
        finally:
            if tmp_path.is_file():
                tmp_path.unlink()
            vision_runtime.RUNTIME_PATH = original_path


class NewAnalysisFormTests(TestCase):
    def test_rejects_oversized_image(self):
        from image_is_versatile.forms import NewAnalysisForm

        image = _test_image_file()
        with patch("image_is_versatile.forms.MAX_IMAGE_BYTES", 1):
            form = NewAnalysisForm(
                {
                    "vision_model": "deepseek_flash",
                    "prompt_preset": "describe",
                    "ui_lang": "en",
                },
                {"image": image},
            )
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["image"][0], "image_too_large")


class JsonFormatTests(TestCase):
    def test_json_pretty_is_escaped_by_templates(self):
        from django.utils.safestring import SafeData

        from image_is_versatile.templatetags.json_format import json_pretty

        rendered = json_pretty({"note": "</code><script>alert(1)</script>"})
        self.assertNotIsInstance(rendered, SafeData)
        self.assertIn("</code>", rendered)
