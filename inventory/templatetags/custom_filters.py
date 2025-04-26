"""
فلاتر مخصصة لتطبيق المخزون (inventory)
فلتر get_range: استخدمه في القالب هكذا:
{% load custom_filters %}
...
{% for i in items|length|get_range:20 %}
    ...
{% endfor %}
"""
from django import template

register = template.Library()

# فلتر get_range (استخدمه: value|get_range:end)
@register.filter
def get_range(value, arg):
    return range(value, arg)

# فلتر index: لإرجاع العنصر في القائمة حسب الفهرس
@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError, KeyError):
        return ''
