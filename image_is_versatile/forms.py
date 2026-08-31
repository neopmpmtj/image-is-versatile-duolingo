from django import forms

from image_is_versatile.prompt_presets import (
    ComposeEvalTextError,
    compose_eval_text,
    default_preset_id,
    preset_choices,
)
from image_is_versatile.services.model_registry import default_model_id, model_choices
from image_is_versatile.services.vision_runtime import (
    IMAGE_DETAIL_CHOICES,
    REASONING_EFFORT_CHOICES,
    get_active_vision_params,
    get_defaults,
)


class VisionSettingsForm(forms.Form):
    reasoning_effort = forms.ChoiceField(
        label="Reasoning effort",
        choices=[(v, v) for v in REASONING_EFFORT_CHOICES],
        help_text="Used by OpenAI and DeepSeek (Responses API). Ignored by Gemini.",
    )
    max_output_tokens = forms.IntegerField(
        label="Max output tokens",
        min_value=1,
        max_value=32000,
        help_text="Maximum tokens in the model response.",
    )
    image_detail = forms.ChoiceField(
        label="Image detail",
        choices=[(v, v) for v in IMAGE_DETAIL_CHOICES],
        help_text="Image resolution hint for OpenAI and DeepSeek vision requests.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            active = get_active_vision_params()
            self.fields["reasoning_effort"].initial = active["reasoning_effort"]
            self.fields["max_output_tokens"].initial = active["max_output_tokens"]
            self.fields["image_detail"].initial = active["image_detail"]


class NewAnalysisForm(forms.Form):
    vision_model = forms.ChoiceField(
        label="Vision model",
        choices=[],
        help_text="Select which model will analyze this image.",
    )
    image = forms.ImageField(
        label="Upload one image",
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/png,image/jpeg,image/webp,image/gif"}
        ),
    )
    description = forms.CharField(
        label="Session description",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Optional. What this analysis is for — used to find it later.",
    )
    omit_instructions = forms.BooleanField(
        label="Omit system instructions",
        required=False,
        initial=False,
        help_text="Send only additional text as the user prompt (for short yes/no questions).",
    )
    prompt_preset = forms.ChoiceField(
        label="System instructions",
        choices=[],
        initial=default_preset_id,
        help_text="Sent as system/developer instructions when enabled.",
    )
    additional = forms.CharField(
        label="Additional instructions",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Appended to the preset when system instructions are on. Required when they are omitted.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vision_model"].choices = model_choices()
        self.fields["vision_model"].initial = default_model_id()
        self.fields["prompt_preset"].choices = preset_choices()

    def clean_vision_model(self):
        from image_is_versatile.services.model_registry import get_model

        vision_model_id = self.cleaned_data["vision_model"]
        try:
            get_model(vision_model_id)
        except KeyError as exc:
            raise forms.ValidationError("Unknown vision model selected.") from exc
        return vision_model_id

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        try:
            instructions, user_prompt = compose_eval_text(
                omit_instructions=cleaned.get("omit_instructions", False),
                preset_id=cleaned.get("prompt_preset", default_preset_id()),
                additional=cleaned.get("additional", ""),
            )
        except ComposeEvalTextError as exc:
            raise forms.ValidationError(str(exc)) from exc
        cleaned["instructions"] = instructions
        cleaned["user_prompt"] = user_prompt
        return cleaned
