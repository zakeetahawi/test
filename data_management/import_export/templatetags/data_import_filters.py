from django import template

register = template.Library()

@register.filter
def data_endswith(value, arg):
    """Returns True if value ends with arg"""
    try:
        return str(value).endswith(str(arg))
    except (TypeError, AttributeError):
        return False

@register.filter
def data_startswith(value, arg):
    """Returns True if value starts with arg"""
    try:
        return str(value).startswith(str(arg))
    except (TypeError, AttributeError):
        return False

@register.filter
def data_get_item(dictionary, key):
    """Gets an item from a dictionary using key"""
    try:
        return dictionary.get(key)
    except (TypeError, AttributeError):
        return None

@register.filter
def data_format_date(value, format_string="%Y-%m-%d"):
    """Formats a date using the given format string"""
    try:
        if value:
            return value.strftime(format_string)
    except (TypeError, AttributeError):
        pass
    return ''
