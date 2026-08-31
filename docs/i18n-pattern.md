# Image-is-versatile — Dual-language UI (EN + pt-PT)

> **Audience:** developers extending this app or replicating the same bilingual setup elsewhere.
>
> **Last updated:** 31 August 2026.

This document describes how **image-is-versatile** implements **English + Portuguese (Portugal)** in the web UI. Translation lives in **vanilla JavaScript dictionaries** applied at runtime in the browser. Django gettext `.po` files are not used for UI copy.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, **Django 5**, SQLite (dev) |
| Frontend | Django HTML templates + **plain JavaScript** |
| UI i18n | `app_i18n.js` dictionary + `data-i18n*` attributes |
| Preference storage | Browser `localStorage` key `iiv-lang` |

`USE_I18N = True` and `LANGUAGE_CODE = "en-gb"` are set in [`config/settings/base.py`](../config/settings/base.py), but **server-rendered pages do not switch locale**. Templates ship English fallback text; JavaScript replaces visible strings after load.

---

## Supported languages

| UI code | Meaning | `document.documentElement.lang` |
|---------|---------|----------------------------------|
| `en` | English (default) | `en` |
| `pt` | Portuguese (Portugal) | `pt-PT` |

The header `<select id="pref-language">` stores `en` or `pt`. Readers normalize any value starting with `pt` to `pt`.

Console dictionaries are keyed as `"pt-PT"`. An alias is set so both codes work:

```javascript
APP_I18N.pt = APP_I18N["pt-PT"];
```

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  Header (all pages)                                          │
│  <select id="pref-language">  →  localStorage["iiv-lang"]     │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    history.html       new.html          settings.html
         │                 │                 │
         └──────── app_i18n.js + i18n.js ───┘
                           │
              data-i18n / data-flash-msg / apiErrorMessage()
```

On language change, `preferences.js` dispatches `iiv-lang-changed`. All pages listen and re-run `applyStaticI18n()`.

---

## localStorage keys

| Key | Values | Purpose |
|-----|--------|---------|
| `iiv-lang` | `en` \| `pt` | Active UI language |

Always read/write through `safeGet` / `safeSet` in [`i18n.js`](../image_is_versatile/static/image_is_versatile/js/i18n.js) — storage may be blocked.

---

## Reference files

| Role | Path |
|------|------|
| Dictionary (EN + pt-PT) | [`image_is_versatile/static/image_is_versatile/js/app_i18n.js`](../image_is_versatile/static/image_is_versatile/js/app_i18n.js) |
| `t()`, `applyStaticI18n()`, `apiErrorMessage()` | [`image_is_versatile/static/image_is_versatile/js/i18n.js`](../image_is_versatile/static/image_is_versatile/js/i18n.js) |
| Language selector | [`image_is_versatile/static/image_is_versatile/js/preferences.js`](../image_is_versatile/static/image_is_versatile/js/preferences.js) |
| Busy overlay | [`image_is_versatile/static/image_is_versatile/js/busy.js`](../image_is_versatile/static/image_is_versatile/js/busy.js) |
| Model-status fetch (new page) | [`image_is_versatile/static/image_is_versatile/js/new_analysis.js`](../image_is_versatile/static/image_is_versatile/js/new_analysis.js) |
| English server fallbacks | [`image_is_versatile/i18n.py`](../image_is_versatile/i18n.py) |
| Flash message template filter | [`image_is_versatile/templatetags/i18n_flash.py`](../image_is_versatile/templatetags/i18n_flash.py) |
| Base template + early `<head>` script | [`image_is_versatile/templates/image_is_versatile/base.html`](../image_is_versatile/templates/image_is_versatile/base.html) |

---

## Implementation recipe for new UI copy

### 1. Add keys to `app_i18n.js`

Add the same key to both `en` and `"pt-PT"` blocks. Use `{name}` placeholders for interpolation.

### 2. Mark up the template

```html
<h2 data-i18n="pageTitle">My page</h2>
```

Supported attributes: `data-i18n` (textContent), `data-i18n-placeholder`, `data-i18n-aria`, `data-i18n-title` (on `<body>` for `document.title`).

### 3. API / flash messages

Server returns stable **snake_case codes** plus English `message` fallback. Client maps via `apiErrorMessage()` or `data-flash-msg` (JSON payload for messages with variables).

```python
from image_is_versatile.i18n import en, flash_payload

messages.success(request, flash_payload("analysis_completed"))
messages.error(request, flash_payload("analysis_failed", detail=str(exc)))
```

### 4. Bump cache buster

After editing any static JS file, bump `?v=` in every template that references it.

---

## Checklist — new bilingual screen

- [ ] Keys in `app_i18n.js` (`en` + `pt-PT` + `.pt` alias)
- [ ] Template English fallbacks + `data-i18n*`
- [ ] Server codes in `image_is_versatile/i18n.py` if returned from API or flash
- [ ] Early `<head>` script already in `base.html` (inherits all pages)
- [ ] Page scripts in `{% block extra_js %}` **after** `i18n.js` (that block is at the end of `base.html`)
- [ ] `node --check` on edited JS files
- [ ] `.venv/bin/python manage.py test image_is_versatile.tests`

---

## Vision API prompts

Preset instruction bodies live in [`config/vision_defaults.py`](../config/vision_defaults.py) as `text.en` / `text.pt`. When the user submits an analysis with `ui_lang=pt` (synced from `iiv-lang` on the new-analysis form), `compose_eval_text()` selects the Portuguese preset text and appends `Responda em português de Portugal.`

---

## What this pattern does not do

- No Django `{% trans %}` for UI chrome
- No `.po` / `locale/` catalogue for the web UI
- No per-user server-side locale — preference is per-browser via `localStorage`
- No automatic translation — every string is hand-authored in both languages
- Stored analysis **responses** and provider error payloads are not re-translated on display

---

## Related docs

- [`docs/handoff.md`](handoff.md) — project status and commands
