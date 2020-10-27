from django import template
from django.template.loader import get_template
from django.utils import timezone

register = template.Library()


def money(value):
    if value is None:
        value = 0
    return "{0:.2f}".format(value / 100.0)


register.filter('money', money)


def get_member_str_key(value):
    from stregsystem.models import Member
    try:
        m = Member.objects.get(pk=value)
        return f"({money(m.balance)} DKK) {m.username} | {m.firstname} {m.lastname}"
    except Member.DoesNotExist:
        return "<i>No member guess</i>"


register.filter('get_member_str_key', get_member_str_key)


@register.inclusion_tag('stregsystem/adventcandle.html')
def show_candle():
    return {'date': timezone.now()}

t = get_template('stregsystem/adventcandle.html')
register.inclusion_tag(t)(show_candle)
