import time
from datetime import datetime, timezone

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from image_is_versatile.forms import ApiKeysForm, NewAnalysisForm, VisionSettingsForm
from image_is_versatile.i18n import en, flash_payload
from image_is_versatile.image_utils import extract_image_metadata
from image_is_versatile.models import AnalysisStatus, ImageAnalysis
from image_is_versatile.services import (
    analyze_image,
    build_api_request_dict,
    check_model_availability,
    get_model,
    save_error_analysis,
    save_success_analysis,
    save_success_analysis_fallback,
)
from image_is_versatile.services.vision_config import VisionApiRequestConfig
from image_is_versatile.services.api_keys import (
    is_using_saved_keys,
    list_provider_key_rows,
    reset_api_keys,
    save_api_key_updates,
)
from image_is_versatile.services.vision_runtime import (
    get_defaults,
    is_using_runtime_file,
    reset_vision_params,
    save_vision_params,
)


def _api_defaults_snapshot(
    *,
    vision_model_id: str,
    omit_instructions: bool,
    prompt_preset: str,
    ui_lang: str = "en",
) -> dict:
    model = get_model(vision_model_id)
    config = VisionApiRequestConfig.from_active()
    return {
        "vision_model_id": vision_model_id,
        "provider": model.provider,
        "omit_instructions": omit_instructions,
        "prompt_preset": prompt_preset,
        "ui_lang": ui_lang,
        **config.to_dict(),
    }


class HistoryView(View):
    def get(self, request):
        analyses = ImageAnalysis.objects.all()[:200]
        return render(request, "image_is_versatile/history.html", {"analyses": analyses})


class ModelStatusView(View):
    def get(self, request, model_id: str):
        try:
            status = check_model_availability(
                model_id,
                session=request.session,
                force_recheck=request.GET.get("recheck") == "1",
            )
        except KeyError:
            vars_dict = {"model_id": model_id}
            return JsonResponse(
                {
                    "ok": False,
                    "code": "unknown_model",
                    "message": en("unknown_model", **vars_dict),
                    "model_id": model_id,
                    **vars_dict,
                },
                status=400,
            )
        request.session.modified = True
        return JsonResponse(status.to_api_dict())


class NewAnalysisView(View):
    def get(self, request):
        form = NewAnalysisForm()
        default_model_id = form.fields["vision_model"].initial
        model_status = check_model_availability(
            default_model_id,
            session=request.session,
            list_models=False,
        )
        request.session.modified = True
        return render(
            request,
            "image_is_versatile/new.html",
            {
                "form": form,
                "model_status": model_status,
                "model_ok": model_status.ok,
            },
        )

    def post(self, request):
        form = NewAnalysisForm(request.POST, request.FILES)
        vision_model_id = request.POST.get("vision_model", "")
        model_status = None
        if vision_model_id:
            try:
                model_status = check_model_availability(
                    vision_model_id,
                    session=request.session,
                    list_models=False,
                )
                request.session.modified = True
            except KeyError:
                model_status = None

        if not form.is_valid():
            return render(
                request,
                "image_is_versatile/new.html",
                {
                    "form": form,
                    "model_status": model_status,
                    "model_ok": model_status.ok if model_status else False,
                },
                status=400,
            )

        vision_model_id = form.cleaned_data["vision_model"]
        model_status = check_model_availability(
            vision_model_id,
            session=request.session,
        )
        request.session.modified = True
        if not model_status.ok:
            if model_status.code:
                form.add_error(
                    None,
                    flash_payload(model_status.code, **(model_status.vars or {})),
                )
            else:
                form.add_error(None, model_status.message)
            return render(
                request,
                "image_is_versatile/new.html",
                {
                    "form": form,
                    "model_status": model_status,
                    "model_ok": False,
                },
                status=400,
            )

        uploaded = form.cleaned_data["image"]
        omit_instructions = form.cleaned_data["omit_instructions"]
        prompt_preset = form.cleaned_data["prompt_preset"]
        ui_lang = form.cleaned_data.get("ui_lang") or "en"
        instructions = form.cleaned_data["instructions"]
        user_prompt = form.cleaned_data["user_prompt"]
        description = form.cleaned_data["description"]

        model = get_model(vision_model_id)
        size_bytes, width, height = extract_image_metadata(uploaded)
        api_defaults = _api_defaults_snapshot(
            vision_model_id=vision_model_id,
            omit_instructions=omit_instructions,
            prompt_preset=prompt_preset,
            ui_lang=ui_lang,
        )
        api_config = VisionApiRequestConfig.from_dict(api_defaults)

        analysis = ImageAnalysis.objects.create(
            image=uploaded,
            image_name=uploaded.name,
            image_content_type=getattr(uploaded, "content_type", None) or "image/jpeg",
            image_size_bytes=size_bytes,
            image_width=width,
            image_height=height,
            instructions=instructions,
            user_prompt=user_prompt,
            description=description,
            api_defaults=api_defaults,
            vision_model_id=vision_model_id,
            provider=model.provider,
            api_model=model.api_model,
            status=AnalysisStatus.IN_PROGRESS,
        )

        api_request = build_api_request_dict(
            vision_model_id=vision_model_id,
            api_model=model.api_model,
            instructions=instructions,
            user_prompt=user_prompt,
            api_config=api_config,
            omit_instructions=omit_instructions,
            prompt_preset=prompt_preset,
        )
        request_started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            result = analyze_image(
                model_id=vision_model_id,
                instructions=instructions,
                user_prompt=user_prompt,
                image_path=analysis.image.path,
                image_content_type=analysis.image_content_type,
                api_config=api_config,
            )
        except Exception as exc:
            finished_perf = time.perf_counter()
            try:
                save_error_analysis(
                    analysis=analysis,
                    error=exc,
                    request_started_at=request_started_at,
                    request_finished_at=datetime.now(timezone.utc),
                    latency_wall_seconds=round(finished_perf - started_perf, 3),
                    api_request=api_request,
                )
            except Exception:
                analysis.status = AnalysisStatus.ERROR
                analysis.error_type = type(exc).__name__
                analysis.error_message = str(exc)
                analysis.save(update_fields=["status", "error_type", "error_message", "updated_at"])
            messages.error(request, flash_payload("analysis_failed", detail=str(exc)))
            return redirect(reverse("image_is_versatile:detail", kwargs={"analysis_id": analysis.id}))

        try:
            save_success_analysis(analysis=analysis, result=result)
            messages.success(request, flash_payload("analysis_completed"))
        except Exception:
            try:
                save_success_analysis_fallback(analysis=analysis, result=result)
                messages.success(request, flash_payload("analysis_completed"))
            except Exception as persist_exc:
                messages.error(
                    request,
                    flash_payload("analysis_save_failed", detail=str(persist_exc)),
                )

        return redirect(reverse("image_is_versatile:detail", kwargs={"analysis_id": analysis.id}))


class VisionSettingsView(View):
    def get(self, request):
        form = VisionSettingsForm()
        defaults = get_defaults()
        return render(
            request,
            "image_is_versatile/settings.html",
            {
                "form": form,
                "using_runtime_file": is_using_runtime_file(),
                "factory_defaults": defaults,
            },
        )

    def post(self, request):
        if request.POST.get("action") == "reset":
            reset_vision_params()
            messages.success(request, flash_payload("settings_reset"))
            return redirect(reverse("image_is_versatile:settings"))

        form = VisionSettingsForm(request.POST)
        if not form.is_valid():
            defaults = get_defaults()
            return render(
                request,
                "image_is_versatile/settings.html",
                {
                    "form": form,
                    "using_runtime_file": is_using_runtime_file(),
                    "factory_defaults": defaults,
                },
                status=400,
            )

        save_vision_params(
            reasoning_effort=form.cleaned_data["reasoning_effort"],
            max_output_tokens=form.cleaned_data["max_output_tokens"],
            image_detail=form.cleaned_data["image_detail"],
        )
        messages.success(request, flash_payload("settings_saved"))
        return redirect(reverse("image_is_versatile:settings"))


def _api_keys_context(form: ApiKeysForm) -> dict:
    rows = []
    for row in list_provider_key_rows():
        provider_id = row["provider_id"]
        rows.append(
            {
                **row,
                "key_field": form[f"key_{provider_id}"],
                "clear_field": form[f"clear_{provider_id}"],
            }
        )
    return {
        "form": form,
        "key_rows": rows,
        "using_saved_keys": is_using_saved_keys(),
    }


class ApiKeysSettingsView(View):
    def get(self, request):
        rows = list_provider_key_rows()
        form = ApiKeysForm([row["provider_id"] for row in rows])
        return render(
            request,
            "image_is_versatile/api_keys.html",
            _api_keys_context(form),
        )

    def post(self, request):
        rows = list_provider_key_rows()
        provider_ids = [row["provider_id"] for row in rows]
        if request.POST.get("action") == "reset":
            reset_api_keys()
            messages.success(request, flash_payload("api_keys_reset"))
            return redirect(reverse("image_is_versatile:api_keys"))

        form = ApiKeysForm(provider_ids, request.POST)
        if not form.is_valid():
            return render(
                request,
                "image_is_versatile/api_keys.html",
                _api_keys_context(form),
                status=400,
            )

        updates: dict[str, str] = {}
        clears: list[str] = []
        for provider_id in provider_ids:
            if form.cleaned_data.get(f"clear_{provider_id}"):
                clears.append(provider_id)
                continue
            value = form.cleaned_data.get(f"key_{provider_id}") or ""
            if value:
                updates[provider_id] = value
        try:
            save_api_key_updates(updates=updates, clears=clears)
        except ValueError:
            form.add_error(None, "api_key_invalid")
            return render(
                request,
                "image_is_versatile/api_keys.html",
                _api_keys_context(form),
                status=400,
            )
        messages.success(request, flash_payload("api_keys_saved"))
        return redirect(reverse("image_is_versatile:api_keys"))


class DetailView(View):
    def get(self, request, analysis_id):
        analysis = get_object_or_404(ImageAnalysis, id=analysis_id)
        return render(request, "image_is_versatile/detail.html", {"analysis": analysis})
