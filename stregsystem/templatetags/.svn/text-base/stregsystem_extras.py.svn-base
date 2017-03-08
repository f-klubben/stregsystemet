from django import template

import fpformat

register = template.Library()

def money(value):
    return fpformat.fix(value/100.0,2)

register.filter('money', money)
