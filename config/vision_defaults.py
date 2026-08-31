"""Vision model defaults, provider registry, and eval prompt presets (not loaded from .env)."""

DEFAULT_EVAL_PROMPT = (
    "Describe this image carefully. Identify the main objects, their relationships, "
    "any visible text, and anything uncertain."
)

EVAL_PROMPT_DEFAULT_ID = "describe"

EVAL_PROMPT_PRESETS = {
    "describe": {
        "label": "Describe (default)",
        "text": DEFAULT_EVAL_PROMPT,
    },
    "ocr": {
        "label": "OCR / text extraction",
        "text": (
            "Transcribe all visible text in this image. Preserve layout where helpful. "
            "Note language, handwriting or print, and anything unreadable or uncertain."
        ),
    },
    "inventory": {
        "label": "Object inventory",
        "text": (
            "List the main objects in this image. Include counts where possible and "
            "describe spatial relationships between them."
        ),
    },
    "uncertainty": {
        "label": "Uncertainty focus",
        "text": (
            "Describe this image, emphasizing what is occluded, ambiguous, low resolution, "
            "or otherwise uncertain. Do not guess beyond what the image supports."
        ),
    },
}

VISION_MAX_OUTPUT_TOKENS = 1600
VISION_REASONING_EFFORT = "low"
VISION_IMAGE_DETAIL = "auto"

VISION_DEFAULT_MODEL_ID = "deepseek_flash"

VISION_PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "adapter": "openai_responses",
        "base_url": None,
    },
    "deepseek": {
        "label": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "adapter": "openai_responses",
        "base_url": "https://api.deepseek.com",
    },
    "gemini": {
        "label": "Google Gemini",
        "env_key": "GEMINI_API_KEY",
        "adapter": "gemini",
    },
}

VISION_MODELS = [
    {
        "id": "openai_sol",
        "label": "GPT-5.6 Sol",
        "provider": "openai",
        "api_model": "gpt-5.6-sol",
    },
    {
        "id": "openai_terra",
        "label": "GPT-5.6 Terra",
        "provider": "openai",
        "api_model": "gpt-5.6-terra",
    },
    {
        "id": "openai_luna",
        "label": "GPT-5.6 Luna",
        "provider": "openai",
        "api_model": "gpt-5.6-luna",
    },
    {
        "id": "gemini_flash",
        "label": "Gemini 2.0 Flash",
        "provider": "gemini",
        "api_model": "gemini-2.0-flash",
    },
    {
        "id": "gemini_pro",
        "label": "Gemini 2.5 Pro",
        "provider": "gemini",
        "api_model": "gemini-2.5-pro",
    },
    {
        "id": "gemini_flash_lite",
        "label": "Gemini 2.0 Flash Lite",
        "provider": "gemini",
        "api_model": "gemini-2.0-flash-lite",
    },
    {
        "id": "deepseek_flash",
        "label": "DeepSeek V4 Flash Vision",
        "provider": "deepseek",
        "api_model": "deepseek-v4-flash-vision-exp",
    },
]
