from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from image_is_versatile.services.model_availability import check_model_availability
from image_is_versatile.services.providers.base import ProviderModelsList


class ModelAvailabilityTests(SimpleTestCase):
    @override_settings(DEEPSEEK_API_KEY="")
    def test_missing_key(self):
        status = check_model_availability("deepseek_flash")
        self.assertFalse(status.ok)
        self.assertIn("DEEPSEEK_API_KEY", status.message)

    @patch("image_is_versatile.services.providers.openai_responses.OpenAI")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_model_available(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = [
            MagicMock(id="deepseek-v4-flash-vision-exp"),
        ]
        status = check_model_availability("deepseek_flash")
        self.assertTrue(status.ok)

    @patch("image_is_versatile.services.providers.openai_responses.OpenAI")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_model_not_listed(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = [MagicMock(id="other-model")]
        status = check_model_availability("deepseek_flash")
        self.assertFalse(status.ok)
        self.assertIn("not available", status.message)

    @patch("image_is_versatile.services.providers.openai_responses.OpenAIResponsesAdapter.list_available_models")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_session_cache(self, mock_list):
        mock_list.return_value = ProviderModelsList(
            ok=True,
            message="ok",
            model_ids=["deepseek-v4-flash-vision-exp"],
        )
        session: dict = {}
        check_model_availability("deepseek_flash", session=session)
        check_model_availability("deepseek_flash", session=session)
        self.assertEqual(mock_list.call_count, 1)
