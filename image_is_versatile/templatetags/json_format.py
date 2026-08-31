import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def json_pretty(value):
    if value in (None, ""):
        return "{}"
    try:
        text = json.dumps(value, indent=2, sort_keys=True, default=str)
    except (TypeError, ValueError):
        text = str(value)
    return mark_safe(text)
