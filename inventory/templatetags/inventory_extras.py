from django import template
register = template.Library()

# تم حذف فلتر get_range نهائيًا من هنا لتجنب التعارض مع custom_filters.py
# إذا احتجت استخدامه، استخدم فقط الموجود في custom_filters.py

