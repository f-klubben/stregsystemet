from django import template
from django.template.loader import get_template
from django.utils import timezone

from stregsystem.caffeine import caffeine_mg_to_coffee_cups

register = template.Library()


@register.filter
def caffeine_emoji_render(caffeine: int):
    return "☕" * caffeine_mg_to_coffee_cups(caffeine)


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


@register.filter
def product_id_and_alias_string(product_id):
    from stregsystem.models import NamedProduct
    from random import choice

    # get aliases for id
    aliases = NamedProduct.objects.filter(product__exact=product_id)

    if aliases.exists():
        if aliases.count() > 1:
            # pick random alias

            alias: NamedProduct = choice(aliases)
            return alias.map_str()
        else:
            # else we've got one alias
            return aliases.first().map_str()
    else:
        #
        return "N/A -> " + str(product_id)
