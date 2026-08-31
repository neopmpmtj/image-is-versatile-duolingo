from pathlib import Path

from django.test import SimpleTestCase

from image_is_versatile.services.vision_runtime import (
    get_active_vision_params,
    get_defaults,
    reset_vision_params,
    save_vision_params,
)


class VisionRuntimeTests(SimpleTestCase):
    def setUp(self):
        from image_is_versatile.services import vision_runtime

        self._original_path = vision_runtime.RUNTIME_PATH
        self._tmpdir = Path(self._original_path.parent) / ".test_vision_runtime"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        vision_runtime.RUNTIME_PATH = self._tmpdir / "vision_runtime.json"
        reset_vision_params()

    def tearDown(self):
        from image_is_versatile.services import vision_runtime

        reset_vision_params()
        vision_runtime.RUNTIME_PATH = self._original_path

    def test_fallback_to_defaults_when_no_file(self):
        params = get_active_vision_params()
        defaults = get_defaults()
        self.assertEqual(params, defaults)

    def test_save_and_load_round_trip(self):
        save_vision_params(
            reasoning_effort="low",
            max_output_tokens=900,
            image_detail="low",
        )
        params = get_active_vision_params()
        self.assertEqual(params["reasoning_effort"], "low")
        self.assertEqual(params["max_output_tokens"], 900)
        self.assertEqual(params["image_detail"], "low")

    def test_save_rejects_invalid_effort(self):
        with self.assertRaises(ValueError):
            save_vision_params(
                reasoning_effort="invalid",
                max_output_tokens=100,
                image_detail="auto",
            )

    def test_save_rejects_unsupported_image_detail(self):
        with self.assertRaises(ValueError):
            save_vision_params(
                reasoning_effort="low",
                max_output_tokens=100,
                image_detail="original",
            )

    def test_save_rejects_invalid_tokens(self):
        with self.assertRaises(ValueError):
            save_vision_params(
                reasoning_effort="high",
                max_output_tokens=0,
                image_detail="auto",
            )

    def test_reset_removes_file(self):
        save_vision_params(
            reasoning_effort="max",
            max_output_tokens=2000,
            image_detail="high",
        )
        reset_vision_params()
        self.assertEqual(get_active_vision_params(), get_defaults())
