from django import template
from math import log

register = template.Library()

def compact_int(value):
    if type(value) is int:
        abs_value = value if value >= 0 else -value
        if abs_value < 10000:
            return value
        exp = int(log(abs_value) / log(1000))
        char = ' KMBTQ'[exp]
        return f'{value/1000**exp: .01f}{char}'.strip()
    return type(value)

register.filter('intcompact', compact_int)