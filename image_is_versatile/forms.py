from django import forms

from image_is_versatile.prompt_presets import (
    ComposeEvalTextError,
    compose_eval_text,
    default_preset_id,
    preset_choices,
)
from image_is_versatile.services.api_keys import MAX_KEY_LENGTH
from image_is_versatile.services.model_registry import default_model_id, model_choices
from image_is_versatile.services.vision_runtime import (
    IMAGE_DETAIL_CHOICES,
    REASONING_EFFORT_CHOICES,
    get_active_vision_params,
)


class VisionSettingsForm(forms.Form):
    reasoning_effort = forms.ChoiceField(
        choices=[(v, v) for v in REASONING_EFFORT_CHOICES],
    )
    max_output_tokens = forms.IntegerField(
        min_value=1,
        max_value=32000,
    )
    image_detail = forms.ChoiceField(
        choices=[(v, v) for v in IMAGE_DETAIL_CHOICES],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            active = get_active_vision_params()
            self.fields["reasoning_effort"].initial = active["reasoning_effort"]
            self.fields["max_output_tokens"].initial = active["max_output_tokens"]
            self.fields["image_detail"].initial = active["image_detail"]


class ApiKeysForm(forms.Form):
    def __init__(self, provider_ids: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        for provider_id in provider_ids:
            self.fields[f"key_{provider_id}"] = forms.CharField(
                required=False,
                max_length=MAX_KEY_LENGTH,
                strip=True,
                widget=forms.PasswordInput(
                    render_value=False,
                    attrs={
                        "autocomplete": "off",
                        "spellcheck": "false",
                        "data-i18n-placeholder": "apiKeyPlaceholder",
                        "placeholder": "Leave blank to keep current key",
                    },
                ),
            )
            self.fields[f"clear_{provider_id}"] = forms.BooleanField(required=False)


MAX_IMAGE_BYTES = 20 * 1024 * 1024


class NewAnalysisForm(forms.Form):
    vision_model = forms.ChoiceField(choices=[])
    image = forms.ImageField(
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/png,image/jpeg,image/webp,image/gif"}
        ),
        error_messages={
            "required": "image_required",
            "missing": "image_required",
            "empty": "image_required",
            "invalid": "image_invalid",
            "invalid_image": "image_invalid",
        },
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    omit_instructions = forms.BooleanField(required=False, initial=False)
    prompt_preset = forms.ChoiceField(choices=[], initial=default_preset_id)
    additional = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    ui_lang = forms.ChoiceField(
        choices=[("en", "en"), ("pt", "pt")],
        required=False,
        initial="en",
        widget=forms.HiddenInput,
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
            raise forms.ValidationError("unknown_vision_model") from exc
        return vision_model_id

    def clean_image(self):
        uploaded = self.cleaned_data["image"]
        size = getattr(uploaded, "size", None)
        if size is not None and size > MAX_IMAGE_BYTES:
            raise forms.ValidationError("image_too_large")
        return uploaded

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        try:
            instructions, user_prompt = compose_eval_text(
                omit_instructions=cleaned.get("omit_instructions", False),
                preset_id=cleaned.get("prompt_preset", default_preset_id()),
                additional=cleaned.get("additional", ""),
                response_lang=cleaned.get("ui_lang") or "en",
            )
        except ComposeEvalTextError as exc:
            raise forms.ValidationError(exc.code) from exc
        cleaned["instructions"] = instructions
        cleaned["user_prompt"] = user_prompt
        return cleaned
