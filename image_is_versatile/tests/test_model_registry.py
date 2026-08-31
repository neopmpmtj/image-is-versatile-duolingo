from django.test import SimpleTestCase

from image_is_versatile.services.model_registry import (
    all_models,
    default_model_id,
    get_model,
    model_choices,
)


class ModelRegistryTests(SimpleTestCase):
    def test_all_models_count(self):
        self.assertEqual(len(all_models()), 7)

    def test_get_model(self):
        model = get_model("deepseek_flash")
        self.assertEqual(model.provider, "deepseek")
        self.assertEqual(model.api_model, "deepseek-v4-flash-vision-exp")

    def test_get_model_unknown(self):
        with self.assertRaises(KeyError):
            get_model("not_a_model")

    def test_model_choices(self):
        choices = model_choices()
        self.assertEqual(len(choices), 7)
        self.assertTrue(all(isinstance(c[0], str) for c in choices))

    def test_default_model_id(self):
        self.assertEqual(default_model_id(), "deepseek_flash")
