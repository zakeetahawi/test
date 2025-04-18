from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """Returns True if value ends with arg"""
    return str(value).endswith(arg)
