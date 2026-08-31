# Session handoff

Last updated: 2026-08-31

## Project

**Versatile** — multi-provider Django app for single-image vision analysis. User picks one model per run from a dropdown (7 models: GPT-5.6 Sol/Terra/Luna, 3 Gemini, DeepSeek). Provider plugins route to OpenAI SDK (OpenAI + DeepSeek) or Google GenAI (Gemini). No auth, no automatic failover.

EN + pt-PT UI is client-side (`localStorage` key `iiv-lang`). Pattern: [`docs/i18n-pattern.md`](i18n-pattern.md).

## Done

- Registry + provider plugin architecture (`VISION_MODELS`, `VISION_PROVIDERS` in `config/vision_defaults.py`)
- Providers: `openai_responses` (OpenAI + DeepSeek), `gemini`
- Dual-language UI (EN / pt-PT) via `app_i18n.js` + `data-i18n*` (not Django gettext)
- Model pre-check: `/new/` GET only checks that an API key exists (no network). Listing runs in the browser via `GET /api/model-status/<id>/` and again on submit
- Page scripts (`{% block extra_js %}`) load **after** `i18n.js` in `base.html` — required or Analyze stays disabled
- Provider timeouts: list 12s, analyze 180s; failed listings cached ~20s; successful lists ~5 min. Catalog ids match dated/numeric revisions (`-001`, `-YYYY-MM-DD`)
- Busy overlay: Cancel / Escape / backdrop click / 185s auto-hide. Model-status fetch aborts after 20s; click the status panel to recheck
- Settings **Reset to defaults** uses `formnovalidate` so invalid fields cannot block it
- Greenfield `ImageAnalysis` schema: `vision_model_id`, `provider`, `api_model`, provider-neutral metadata fields
- Prompt presets + `compose_eval_text()` (Portuguese preset text when `ui_lang=pt`)
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
- Worker-kill mid-request can still leave a row `in_progress` (detail page explains this; no poll/retry)

## Commands

```bash
source .venv/bin/activate
cp .env.example .env
rm -f db.sqlite3
python manage.py migrate
python manage.py runserver
.venv/bin/python manage.py test image_is_versatile.tests
```
