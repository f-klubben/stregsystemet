from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()


@register.inclusion_tag("hitmarker.html")
def hitmarker_js():
    return dict()
