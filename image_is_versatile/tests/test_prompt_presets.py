from django.test import SimpleTestCase

from image_is_versatile.prompt_presets import ComposeEvalTextError, compose_eval_text, default_preset_id


class ComposeEvalTextTests(SimpleTestCase):
    def test_default_preset_instructions_only(self):
        instructions, user_prompt = compose_eval_text(
            omit_instructions=False,
            preset_id=default_preset_id(),
            additional="",
        )
        self.assertTrue(instructions)
        self.assertEqual(user_prompt, "")

    def test_additional_appended_to_preset(self):
        instructions, user_prompt = compose_eval_text(
            omit_instructions=False,
            preset_id="describe",
            additional="Focus on signage.",
        )
        self.assertIn("Focus on signage.", instructions)
        self.assertEqual(user_prompt, "")

    def test_omit_requires_additional(self):
        with self.assertRaises(ComposeEvalTextError):
            compose_eval_text(
                omit_instructions=True,
                preset_id="describe",
                additional="",
            )

    def test_omit_uses_additional_as_user_prompt(self):
        instructions, user_prompt = compose_eval_text(
            omit_instructions=True,
            preset_id="describe",
            additional="Is there a cat?",
        )
        self.assertEqual(instructions, "")
        self.assertEqual(user_prompt, "Is there a cat?")
