from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

@receiver(pre_save, sender='orders.Order')
def track_price_changes(sender, instance, **kwargs):
    """تتبع تغييرات الأسعار في الطلبات"""
    if instance.pk:  # تحقق من أن هذا تحديث وليس إنشاء جديد
        try:
            Order = instance.__class__
            old_instance = Order.objects.get(pk=instance.pk)
            if old_instance.final_price != instance.final_price:
                instance.price_changed = True
                instance.modified_at = timezone.now()
        except Order.DoesNotExist:
            pass  # حالة الإنشاء الجديد