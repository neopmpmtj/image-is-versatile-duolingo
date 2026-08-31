import json

from django import template

register = template.Library()


@register.filter
def json_pretty(value):
    if value in (None, ""):
        return "{}"
    try:
        return json.dumps(value, indent=2, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(value)
