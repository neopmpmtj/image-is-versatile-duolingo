# Session handoff

Last updated: 2026-08-31

## Project

**Versatile** — multi-provider Django app for single-image vision analysis. User picks one model per run from a dropdown (7 models: GPT-5.6 Sol/Terra/Luna, 3 Gemini, DeepSeek). Provider plugins route to OpenAI SDK (OpenAI + DeepSeek) or Google GenAI (Gemini). No auth, no automatic failover.

## Done

- Registry + provider plugin architecture (`VISION_MODELS`, `VISION_PROVIDERS` in `config/vision_defaults.py`)
- Providers: `openai_responses` (OpenAI + DeepSeek), `gemini`
- Model pre-check on dropdown change (`GET /api/model-status/<id>/`) and on submit
- Greenfield `ImageAnalysis` schema: `vision_model_id`, `provider`, `api_model`, provider-neutral metadata fields
- Prompt presets + `compose_eval_text()`
- Views: history `/`, new `/new/`, settings `/settings/`, detail `/analysis/<uuid>/`
- Runtime vision params via `/settings/` → `config/vision_runtime.json` (overrides `vision_defaults.py`)
- API keys in `.env`: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`
- Unit tests in `image_is_versatile/tests/`

## Not done

- Streaming / TTFB
- Auth, production deploy
- Per-model API parameter overrides (shared runtime params only)
- Re-run on detail page (`/new/` is the re-run path)
- Automatic failover between models

## Commands

```bash
source .venv/bin/activate
cp .env.example .env
rm -f db.sqlite3
python manage.py migrate
python manage.py runserver
.venv/bin/python manage.py test image_is_versatile.tests
```
