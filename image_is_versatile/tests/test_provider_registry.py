from django.test import SimpleTestCase

from image_is_versatile.services.provider_registry import get_adapter, get_provider_config


class ProviderRegistryTests(SimpleTestCase):
    def test_openai_adapter(self):
        adapter = get_adapter("openai")
        self.assertEqual(adapter.provider_id, "openai")
        self.assertEqual(adapter.env_key, "OPENAI_API_KEY")

    def test_deepseek_adapter(self):
        adapter = get_adapter("deepseek")
        self.assertEqual(adapter.provider_id, "deepseek")
        self.assertEqual(adapter.base_url, "https://api.deepseek.com")

    def test_gemini_adapter(self):
        adapter = get_adapter("gemini")
        self.assertEqual(adapter.provider_id, "gemini")
        self.assertEqual(adapter.env_key, "GEMINI_API_KEY")

    def test_unknown_provider(self):
        with self.assertRaises(KeyError):
            get_provider_config("unknown")
