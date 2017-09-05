from django import template

register = template.Library()

def money(value):
    return "{0:.2f}".format(value/100.0)

register.filter('money', money)
