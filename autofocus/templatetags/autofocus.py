from django import template
from django.utils.html import format_html
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def autofocus_js():
    return format_html('<script src="{}"></script>', static("autofocus.js"))
