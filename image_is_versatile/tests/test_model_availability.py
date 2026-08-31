from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from image_is_versatile.services.model_availability import check_model_availability
from image_is_versatile.services.providers.base import ProviderModelsList


class ModelAvailabilityTests(SimpleTestCase):
    @override_settings(DEEPSEEK_API_KEY="")
    def test_missing_key(self):
        status = check_model_availability("deepseek_flash")
        self.assertFalse(status.ok)
        self.assertEqual(status.code, "api_key_missing")
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
        self.assertEqual(status.code, "model_available")

    @patch("image_is_versatile.services.providers.openai_responses.OpenAI")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_model_not_listed(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = [MagicMock(id="other-model")]
        status = check_model_availability("deepseek_flash")
        self.assertFalse(status.ok)
        self.assertEqual(status.code, "model_not_on_account")
        self.assertIn("not available", status.message)

    @patch("image_is_versatile.services.providers.openai_responses.OpenAI")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_versioned_api_model_counts_as_available(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = [
            MagicMock(id="deepseek-v4-flash-vision-exp-001"),
        ]
        status = check_model_availability("deepseek_flash")
        self.assertTrue(status.ok)
        self.assertEqual(status.code, "model_available")

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

    @patch("image_is_versatile.services.providers.openai_responses.OpenAIResponsesAdapter.list_available_models")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_list_models_false_skips_network(self, mock_list):
        status = check_model_availability("deepseek_flash", list_models=False)
        self.assertTrue(status.ok)
        self.assertEqual(status.code, "checking_model_availability")
        mock_list.assert_not_called()

    @patch("image_is_versatile.services.providers.openai_responses.OpenAIResponsesAdapter.list_available_models")
    @override_settings(DEEPSEEK_API_KEY="ds-test")
    def test_failed_listing_cached_briefly(self, mock_list):
        mock_list.return_value = ProviderModelsList(
            ok=False,
            code="provider_unreachable",
            vars={"provider": "DeepSeek"},
            message="Could not reach DeepSeek. Check your network.",
        )
        session: dict = {}
        first = check_model_availability("deepseek_flash", session=session)
        second = check_model_availability("deepseek_flash", session=session)
        self.assertFalse(first.ok)
        self.assertFalse(second.ok)
        self.assertEqual(first.code, "provider_unreachable")
        self.assertEqual(second.code, "provider_unreachable")
        self.assertEqual(mock_list.call_count, 1)

    def test_api_model_version_suffix_match(self):
        from image_is_versatile.services.providers.base import api_model_is_listed

        self.assertTrue(api_model_is_listed("gemini-2.0-flash", ["gemini-2.0-flash"]))
        self.assertTrue(api_model_is_listed("gemini-2.0-flash", ["gemini-2.0-flash-001"]))
        self.assertTrue(api_model_is_listed("gpt-5.6-sol", ["gpt-5.6-sol-2026-03-15"]))
        self.assertFalse(api_model_is_listed("gemini-2.0-flash", ["gemini-2.0-flash-lite"]))
        self.assertFalse(api_model_is_listed("gemini-2.0-flash", ["other-model"]))

    def test_map_provider_timeout_and_gemini_status(self):
        from image_is_versatile.services.providers.base import map_provider_error

        class APITimeoutError(Exception):
            pass

        code, vars_dict, message = map_provider_error(
            "OpenAI", "OPENAI_API_KEY", APITimeoutError("timed out")
        )
        self.assertEqual(code, "provider_timeout")
        self.assertIn("OpenAI", message)

        class ClientError(Exception):
            def __init__(self):
                self.code = 401
                self.status = "UNAUTHORIZED"

        code, vars_dict, message = map_provider_error(
            "Google Gemini", "GEMINI_API_KEY", ClientError()
        )
        self.assertEqual(code, "provider_auth_rejected")
        self.assertEqual(vars_dict["env_key"], "GEMINI_API_KEY")
