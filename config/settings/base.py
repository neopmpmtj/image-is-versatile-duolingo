"""Shared Django settings for image-is."""

from pathlib import Path

from decouple import config as env

from config.vision_defaults import (
    EVAL_PROMPT_DEFAULT_ID,
    EVAL_PROMPT_PRESETS,
    VISION_DEFAULT_MODEL_ID,
    VISION_IMAGE_DETAIL,
    VISION_MAX_OUTPUT_TOKENS,
    VISION_MODELS,
    VISION_PROVIDERS,
    VISION_REASONING_EFFORT,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "django-insecure-image-is-dev-only-change-in-production"

DEBUG = False

ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "image_is_versatile",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
DEEPSEEK_API_KEY = env("DEEPSEEK_API_KEY", default="")

VISION_MODELS = VISION_MODELS
VISION_PROVIDERS = VISION_PROVIDERS
VISION_DEFAULT_MODEL_ID = VISION_DEFAULT_MODEL_ID
VISION_MAX_OUTPUT_TOKENS = VISION_MAX_OUTPUT_TOKENS
VISION_REASONING_EFFORT = VISION_REASONING_EFFORT
VISION_IMAGE_DETAIL = VISION_IMAGE_DETAIL

EVAL_PROMPT_PRESETS = EVAL_PROMPT_PRESETS
EVAL_PROMPT_DEFAULT_ID = EVAL_PROMPT_DEFAULT_ID
