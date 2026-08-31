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
        self.assertIn("Respond in English.", instructions)
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
        self.assertEqual(user_prompt, "Is there a cat?\n\nRespond in English.")

    def test_portuguese_response_directive_on_instructions(self):
        instructions, user_prompt = compose_eval_text(
            omit_instructions=False,
            preset_id="describe",
            additional="",
            response_lang="pt",
        )
        self.assertIn("Descreva esta imagem com cuidado", instructions)
        self.assertNotIn("Describe this image carefully", instructions)
        self.assertIn("Responda em português de Portugal.", instructions)
        self.assertEqual(user_prompt, "")

    def test_portuguese_response_directive_on_user_prompt_when_omitted(self):
        instructions, user_prompt = compose_eval_text(
            omit_instructions=True,
            preset_id="describe",
            additional="Há um gato?",
            response_lang="pt-PT",
        )
        self.assertEqual(instructions, "")
        self.assertIn("Responda em português de Portugal.", user_prompt)
