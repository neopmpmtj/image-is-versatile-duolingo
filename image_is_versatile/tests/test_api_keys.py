from pathlib import Path

from django.test import SimpleTestCase, override_settings

from image_is_versatile.services.api_keys import (
    get_env_api_key,
    get_override_api_key,
    is_using_saved_keys,
    list_provider_key_rows,
    mask_api_key,
    reset_api_keys,
    save_api_key_updates,
)
from image_is_versatile.services.provider_registry import get_api_key


class ApiKeysPersistenceTests(SimpleTestCase):
    def setUp(self):
        from image_is_versatile.services import api_keys

        self._original_path = api_keys.KEYS_PATH
        self._tmpdir = Path(self._original_path.parent) / ".test_api_keys"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        api_keys.KEYS_PATH = self._tmpdir / "api_keys.json"
        reset_api_keys()

    def tearDown(self):
        from image_is_versatile.services import api_keys

        reset_api_keys()
        api_keys.KEYS_PATH = self._original_path

    def test_mask_hides_secret(self):
        self.assertEqual(mask_api_key(""), "")
        self.assertEqual(mask_api_key("abcd"), "••••")
        self.assertEqual(mask_api_key("sk-live-unique-zzQ8"), "••••zzQ8")

    def test_env_used_when_no_file(self):
        with override_settings(DEEPSEEK_API_KEY="from-env"):
            self.assertEqual(get_api_key("deepseek"), "from-env")
            self.assertFalse(is_using_saved_keys())

    def test_saved_key_overrides_env(self):
        with override_settings(DEEPSEEK_API_KEY="from-env"):
            save_api_key_updates(updates={"deepseek": "from-ui"})
            self.assertEqual(get_api_key("deepseek"), "from-ui")
            self.assertEqual(get_override_api_key("deepseek"), "from-ui")
            self.assertEqual(get_env_api_key("deepseek"), "from-env")
            self.assertTrue(is_using_saved_keys())

    def test_save_round_trip_survives_reread(self):
        save_api_key_updates(updates={"openai": "sk-ui-openai-zzQ8", "gemini": "gem-ui-zzQ8"})
        self.assertEqual(get_override_api_key("openai"), "sk-ui-openai-zzQ8")
        self.assertEqual(get_override_api_key("gemini"), "gem-ui-zzQ8")
        self.assertEqual(get_override_api_key("deepseek"), "")

    def test_blank_update_keeps_existing(self):
        save_api_key_updates(updates={"openai": "sk-keep-zzQ8"})
        save_api_key_updates(updates={})
        self.assertEqual(get_override_api_key("openai"), "sk-keep-zzQ8")

    def test_clear_falls_back_to_env(self):
        with override_settings(OPENAI_API_KEY="from-env"):
            save_api_key_updates(updates={"openai": "from-ui"})
            save_api_key_updates(updates={}, clears=["openai"])
            self.assertEqual(get_override_api_key("openai"), "")
            self.assertEqual(get_api_key("openai"), "from-env")
            self.assertFalse(is_using_saved_keys())

    def test_reset_removes_file(self):
        save_api_key_updates(updates={"gemini": "gem-ui-zzQ8"})
        reset_api_keys()
        self.assertEqual(get_override_api_key("gemini"), "")
        self.assertFalse(is_using_saved_keys())

    def test_rejects_unknown_provider(self):
        with self.assertRaises(ValueError):
            save_api_key_updates(updates={"unknown": "x"})

    def test_rejects_newlines(self):
        with self.assertRaises(ValueError):
            save_api_key_updates(updates={"openai": "sk-one\nsk-two"})

    def test_rows_never_include_full_key(self):
        secret = "sk-live-unique-zzQ8"
        save_api_key_updates(updates={"openai": secret})
        rows = {row["provider_id"]: row for row in list_provider_key_rows()}
        openai = rows["openai"]
        self.assertEqual(openai["source"], "saved")
        self.assertEqual(openai["masked"], "••••zzQ8")
        self.assertNotIn(secret, openai["masked"])
