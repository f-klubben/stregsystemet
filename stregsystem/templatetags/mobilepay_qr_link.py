from django import template
from django.template.loader import get_template

register = template.Library()


@register.inclusion_tag('stregsystem/mobilepay_qr_link.html')
def mobilepay_qr_link(username, amount=None):
    return locals()


t = get_template('stregsystem/mobilepay_qr_link.html')
register.inclusion_tag(t)(mobilepay_qr_link)
