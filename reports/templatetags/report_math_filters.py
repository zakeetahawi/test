from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """
    Divides the value by the argument
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument
    """
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def sub(value, arg):
    """
    Subtracts the argument from the value
    """
    try:
        return float(value) - float(arg)
    except ValueError:
        return 0

@register.filter
def add(value, arg):
    """
    Adds the argument to the value
    """
    try:
        return float(value) + float(arg)
    except ValueError:
        return 0

@register.filter
def sum_attr(value, attr=None):
    """
    Sums the attribute 'attr' for each item in the list 'value'
    If attr is None, sum the items directly
    """
    total = 0
    if not value:
        return total
        
    if attr is None:
        try:
            return float(sum(value))
        except (TypeError, ValueError):
            try:
                return sum(float(item) for item in value)
            except (TypeError, ValueError):
                return 0
    else:
        for item in value:
            try:
                # Try to get attribute
                attr_value = getattr(item, attr)
                total += float(attr_value)
            except (AttributeError, ValueError, TypeError):
                try:
                    # Try dictionary access
                    attr_value = item[attr]
                    total += float(attr_value)
                except (KeyError, ValueError, TypeError):
                    continue
        return total
