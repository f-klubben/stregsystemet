from django import template

register = template.Library()


@register.filter
def comma_to_period(value):
    return value.replace(",", ".")
