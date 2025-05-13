from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def currency(value):
    """تنسيق القيمة كعملة"""
    from django.template import RequestContext

    try:
        # الحصول على رمز العملة من السياق
        # ملاحظة: هذا الفلتر سيستخدم القيمة الافتراضية إذا لم يتم تمرير السياق
        # سيتم استخدام متغير السياق 'currency_symbol' الذي تم إضافته بواسطة context_processor

        # استخدام القيمة الافتراضية (ريال سعودي) إذا لم يتم العثور على رمز العملة في السياق
        from accounts.models import SystemSettings
        settings = SystemSettings.get_settings()
        currency_symbol = settings.currency_symbol

        return "{:,.2f} {}".format(float(value), currency_symbol)
    except (ValueError, TypeError):
        # القيمة الافتراضية في حالة حدوث خطأ
        return "0.00 ر.س"

@register.filter
def growth_class(value):
    """تحديد لون النمو بناءً على القيمة"""
    try:
        value = float(value)
        if value > 5:
            return 'text-success'
        elif value < -5:
            return 'text-danger'
        else:
            return 'text-warning'
    except (ValueError, TypeError):
        return ''

@register.filter
def retention_class(value):
    """تحديد لون معدل الاحتفاظ بناءً على القيمة"""
    try:
        value = float(value)
        if value >= 80:
            return 'text-success'
        elif value >= 60:
            return 'text-warning'
        else:
            return 'text-danger'
    except (ValueError, TypeError):
        return ''

@register.filter
def margin_class(value):
    """تحديد لون هامش الربح بناءً على القيمة"""
    try:
        value = float(value)
        if value >= 25:
            return 'text-success'
        elif value >= 15:
            return 'text-warning'
        else:
            return 'text-danger'
    except (ValueError, TypeError):
        return ''

@register.filter
def map(value, attr):
    """استخراج قيم محددة من قائمة كائنات"""
    try:
        return mark_safe(json.dumps([item[attr] for item in value]))
    except (KeyError, TypeError):
        return '[]'

@register.filter
def percentage(value, total):
    """حساب النسبة المئوية"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def trend_icon(value):
    """إرجاع أيقونة الاتجاه بناءً على القيمة"""
    try:
        value = float(value)
        if value > 0:
            return mark_safe('<i class="fas fa-arrow-up text-success"></i>')
        elif value < 0:
            return mark_safe('<i class="fas fa-arrow-down text-danger"></i>')
        else:
            return mark_safe('<i class="fas fa-minus text-warning"></i>')
    except (ValueError, TypeError):
        return ''

@register.filter
def format_frequency(value):
    """تنسيق معدل التكرار"""
    try:
        value = float(value)
        if value >= 1:
            return f"{value:.1f}x"
        else:
            return f"{value*100:.0f}%"
    except (ValueError, TypeError):
        return '0%'

@register.filter
def status_class(value):
    """تحديد لون الحالة"""
    status_classes = {
        'completed': 'success',
        'pending': 'warning',
        'cancelled': 'danger',
        'processing': 'info',
        'delayed': 'secondary'
    }
    return f"text-{status_classes.get(value, 'secondary')}"

@register.filter
def chart_color(index):
    """إرجاع لون للرسم البياني"""
    colors = [
        '#FF6384',  # أحمر
        '#36A2EB',  # أزرق
        '#FFCE56',  # أصفر
        '#4BC0C0',  # أخضر مائل للأزرق
        '#9966FF',  # بنفسجي
        '#FF9F40',  # برتقالي
        '#FF6384',  # وردي
        '#C9CBCF'   # رمادي
    ]
    return colors[index % len(colors)]

@register.filter
def format_time(minutes):
    """تنسيق الوقت من دقائق إلى ساعات ودقائق"""
    try:
        minutes = int(minutes)
        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours > 0 and remaining_minutes > 0:
            return f"{hours} ساعة و {remaining_minutes} دقيقة"
        elif hours > 0:
            return f"{hours} ساعة"
        else:
            return f"{remaining_minutes} دقيقة"
    except (ValueError, TypeError):
        return "0 دقيقة"

@register.filter
def format_number(value):
    """تنسيق الأرقام الكبيرة"""
    try:
        value = float(value)
        if value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.0f}"
    except (ValueError, TypeError):
        return "0"
