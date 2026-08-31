from django import template

from image_is_versatile.i18n import flash_fallback

register = template.Library()


@register.filter
def flash_display(message):
    return flash_fallback(message)
