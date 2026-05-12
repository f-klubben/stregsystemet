from django import template
from django.template.loader import get_template
from stregsystem.utils import mobilepay_launch_uri

register = template.Library()


@register.simple_tag
def mobilepay_link(username, amount=None):
    return mobilepay_launch_uri(username, amount)


@register.inclusion_tag('stregsystem/mobilepay_qr.html')
def mobilepay_qr(username, amount=None):
    return locals()


t = get_template('stregsystem/mobilepay_qr.html')
register.inclusion_tag(t)(mobilepay_qr)
