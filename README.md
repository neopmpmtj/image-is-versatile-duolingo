# Image Analysis (Versatile)

Django app for **multi-provider single-image analysis**. Pick a vision model (OpenAI GPT-5.6, Google Gemini, or DeepSeek), upload an image, run one API call, and persist the full response and metadata in SQLite.

The web UI is **English + Portuguese (Portugal)**. Language is per-browser (`localStorage` key `iiv-lang`); see [`docs/i18n-pattern.md`](docs/i18n-pattern.md).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set API keys in `.env`:

```
OPENAI_API_KEY=your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
DEEPSEEK_API_KEY=your-deepseek-key-here
```

You can also add or replace keys in the UI at **/settings/api-keys/**. Values saved there override `.env`, persist across server restarts (`config/api_keys.json`, gitignored), and are never shown in full in the page.

Model catalog, provider routing, API defaults, and prompt presets live in `config/vision_defaults.py` and `config/settings/`.

## Run

```bash
rm -f db.sqlite3
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

| Path | Purpose |
|------|---------|
| `/` | History — past analyses |
| `/new/` | New analysis — model picker + upload + presets. Page load does not call the provider; the browser checks availability via the status API. |
| `/settings/` | Vision API parameters — reasoning effort, max tokens, image detail. **Reset to defaults** ignores invalid fields. |
| `/settings/api-keys/` | Provider API keys (OpenAI, Gemini, DeepSeek). Saved keys override `.env` and survive restarts. |
| `/api/model-status/<model_id>/` | Pre-check selected model availability (JSON). `?recheck=1` bypasses the session cache. |
| `/analysis/<uuid>/` | Detail — response + metadata |

## Models

Seven models are configured in `VISION_MODELS` (OpenAI Sol/Terra/Luna, three Gemini, DeepSeek). The dropdown always lists all models; availability is checked when you select one (and you can click the status panel to check again). No automatic failover — pick a different model if credits or rate limits block the current choice.

Provider calls time out (12s for model listing, 180s for analysis). While an analysis is running, **Cancel wait**, Escape, or a click outside the dialog dismisses the overlay so the UI is not stuck. If listing returns a dated revision (`gemini-2.0-flash-001`), it still counts as the catalog model.

## Prompt presets

On `/new/`:

| Control | Sent to API |
|---------|-------------|
| Vision model | Routes to the correct provider SDK |
| System instructions preset | Responses `instructions` (OpenAI/DeepSeek) or combined prompt (Gemini) |
| Omit system instructions | No `instructions`; additional text required as user prompt |
| Additional instructions | Appended to preset, or sole user text when omitted |
| UI language | Hidden `ui_lang` synced from the header; selects preset `text.en` / `text.pt` and appends a respond-in language line |
| Session description | Not sent — metadata only |

## Add a model or provider

**New model (existing provider):** append one entry to `VISION_MODELS` in `config/vision_defaults.py`.

**New provider:** add a `VISION_PROVIDERS` block + env key, implement `image_is_versatile/services/providers/<adapter>.py`, register in `provider_registry.py`, then add model entries.

## Tests

```bash
.venv/bin/python manage.py test image_is_versatile.tests
```

## Shared defaults

Factory defaults live in `config/vision_defaults.py`. Change active values at **/settings/** (saved to `config/vision_runtime.json`). Delete that file or use **Reset to defaults** on the settings page to revert.

API keys: `.env` is the fallback. **/settings/api-keys/** writes `config/api_keys.json` (not committed). Leave a field blank to keep the current key; **Clear saved keys** falls back to `.env`.

| Setting | Factory default |
|---------|-----------------|
| Default model | `deepseek_flash` |
| Reasoning effort | `low` |
| Max output tokens | `1600` |
| Image detail | `auto` |
