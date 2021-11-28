from django import template
from django.template.loader import get_template
from django.utils import timezone

register = template.Library()

@register.filter
def caffeine_emoji_render(caffeine: int):
    coffee_str = ""

    from stregsystem.caffeine import CAFFEINE_IN_COFFEE
    cups = int(caffeine / CAFFEINE_IN_COFFEE)
    for coffee_cup in range(cups):
        coffee_str += '☕'  # HTML-code for ☕
    return coffee_str



def money(value):
    if value is None:
        value = 0
    return "{0:.2f}".format(value / 100.0)


register.filter('money', money)


@register.inclusion_tag('stregsystem/adventcandle.html')
def show_candle():
    return {'date': timezone.now()}


t = get_template('stregsystem/adventcandle.html')
register.inclusion_tag(t)(show_candle)
