from datetime import datetime
from random import randint, choice
from django import template
from django.template.loader import get_template
from django.utils import timezone

from stregsystem.caffeine import caffeine_mg_to_coffee_cups

register = template.Library()


@register.filter
def caffeine_emoji_render(caffeine: int):
    return "☕" * caffeine_mg_to_coffee_cups(caffeine)


@register.filter
def money(value):
    if value is None:
        value = 0
    return "{0:.2f}".format(value / 100.0)


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def product_id_and_alias_string(product_id):
    from stregsystem.models import NamedProduct
    from random import choice

    # get aliases for id
    aliases = NamedProduct.objects.filter(product__exact=product_id)

    if aliases.exists():
        res = str(product_id) + " / "
        if aliases.count() > 1:
            # pick random alias

            alias: NamedProduct = choice(aliases)
            return res + str(alias)
        else:
            # else we've got one alias
            return res + str(aliases.first())
    else:
        #
        return str(product_id)


@register.simple_tag
def day_of_month():
    return datetime.now().day


@register.simple_tag
def fractional_day_of_month():
    now = datetime.now()
    return now.day - 1 + (now.hour / 24) + (now.minute / 1440) + (now.second / 86400)


@register.simple_tag
def random(min, max):
    return randint(min, max)


@register.simple_tag
def random_choice(str1, str2):
    return choice([str1, str2])


@register.filter
def to_range(value):
    return range(value)
