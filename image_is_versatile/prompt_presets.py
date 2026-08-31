"""Eval system-instruction preset catalog helpers."""

from __future__ import annotations

from typing import Any

from django.conf import settings


class ComposeEvalTextError(ValueError):
    """Invalid omit/preset/additional combination."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def preset_catalog() -> dict[str, dict[str, Any]]:
    return dict(settings.EVAL_PROMPT_PRESETS)


def preset_choices() -> list[tuple[str, str]]:
    return [
        (preset_id, preset["label"])
        for preset_id, preset in settings.EVAL_PROMPT_PRESETS.items()
    ]


def preset_text_for(preset_id: str, lang: str) -> str:
    lang = normalize_response_lang(lang)
    preset = settings.EVAL_PROMPT_PRESETS[preset_id]
    return preset["text"][lang]


def preset_texts(lang: str = "en") -> dict[str, str]:
    lang = normalize_response_lang(lang)
    return {
        preset_id: preset["text"][lang]
        for preset_id, preset in settings.EVAL_PROMPT_PRESETS.items()
    }


def default_preset_id() -> str:
    return settings.EVAL_PROMPT_DEFAULT_ID


RESPONSE_LANG_DIRECTIVES = {
    "en": "Respond in English.",
    "pt": "Responda em português de Portugal.",
}


def normalize_response_lang(raw: str | None) -> str:
    if raw and str(raw).lower().startswith("pt"):
        return "pt"
    return "en"


def apply_response_language(
    instructions: str,
    user_prompt: str,
    response_lang: str,
) -> tuple[str, str]:
    """Append a response-language directive to the prompt sent to the vision API."""
    lang = normalize_response_lang(response_lang)
    directive = RESPONSE_LANG_DIRECTIVES[lang]
    if instructions.strip():
        return f"{instructions.rstrip()}\n\n{directive}", user_prompt
    if user_prompt.strip():
        return instructions, f"{user_prompt.rstrip()}\n\n{directive}"
    return instructions, directive


def compose_eval_text(
    *,
    omit_instructions: bool,
    preset_id: str,
    additional: str,
    response_lang: str = "en",
) -> tuple[str, str]:
    """Return (instructions, user_prompt) for an analysis session."""
    lang = normalize_response_lang(response_lang)
    extra = additional.strip()
    if omit_instructions:
        if not extra:
            raise ComposeEvalTextError("additional_required_when_omit")
        instructions, user_prompt = "", extra
    else:
        texts = preset_texts(lang)
        if preset_id not in texts:
            raise ComposeEvalTextError("invalid_preset")
        body = texts[preset_id]
        instructions = body if not extra else f"{body}\n\n{extra}"
        user_prompt = ""
    return apply_response_language(instructions, user_prompt, lang)
