# Image Analysis (Versatile)

Django app for **multi-provider single-image analysis**. Pick a vision model (OpenAI GPT-5.6, Google Gemini, or DeepSeek), upload an image, run one API call, and persist the full response and metadata in SQLite.

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
| `/new/` | New analysis — model picker + upload + presets |
| `/settings/` | Vision API parameters — reasoning effort, max tokens, image detail |
| `/api/model-status/<model_id>/` | Pre-check selected model availability (JSON) |
| `/analysis/<uuid>/` | Detail — response + metadata |

## Models

Seven models are configured in `VISION_MODELS` (OpenAI Sol/Terra/Luna, three Gemini, DeepSeek). The dropdown always lists all models; availability is checked when you select one. No automatic failover — pick a different model if credits or rate limits block the current choice.

## Prompt presets

On `/new/`:

| Control | Sent to API |
|---------|-------------|
| Vision model | Routes to the correct provider SDK |
| System instructions preset | Responses `instructions` (OpenAI/DeepSeek) or combined prompt (Gemini) |
| Omit system instructions | No `instructions`; additional text required as user prompt |
| Additional instructions | Appended to preset, or sole user text when omitted |
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

| Setting | Factory default |
|---------|-----------------|
| Default model | `deepseek_flash` |
| Reasoning effort | `low` |
| Max output tokens | `1600` |
| Image detail | `auto` |
