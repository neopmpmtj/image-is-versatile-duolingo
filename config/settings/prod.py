from .base import *  # noqa: F401,F403

from decouple import config as env

DEBUG = False

# Live test deployment (HTTP only, no domain yet):
#   URL:  http://169.58.240.120/image-is/
#   nginx strips the /image-is/ prefix before proxying to gunicorn, so Django
#   must re-attach it to every generated URL (reverse, static, media).
ALLOWED_HOSTS = env(
    "ALLOWED_HOSTS",
    default="169.58.240.120,127.0.0.1,localhost",
).split(",")

FORCE_SCRIPT_NAME = "/image-is/"

STATIC_URL = "/image-is/static/"
MEDIA_URL = "/image-is/media/"

# Uploads are real photos for vision analysis; Django's 2.5MB default would
# reject them. Raise the cap (nginx client_max_body_size must match).
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024

# Override the dev-only hardcoded key from .env when provided.
SECRET_KEY = env("SECRET_KEY", default=SECRET_KEY)
