from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from ..models import DynamicPricing, Order
from ..services.pricing_service import PricingService

@shared_task
def update_dynamic_prices():
    """تحديث الأسعار الديناميكية لجميع الطلبات النشطة"""
    now = timezone.now()
    active_orders = Order.objects.filter(
        Q(status__in=['pending', 'processing']) &
        Q(created_at__gte=now - timezone.timedelta(days=30))
    )
    
    updated_count = 0
    for order in active_orders:
        new_price = PricingService.calculate_dynamic_price(order)
        if new_price != order.final_price:
            order.final_price = new_price
            order.save()
            updated_count += 1
            
    return f"تم تحديث {updated_count} طلب"

@shared_task
def cleanup_expired_pricing_rules():
    """تنظيف قواعد التسعير منتهية الصلاحية"""
    now = timezone.now()
    expired_rules = DynamicPricing.objects.filter(
        Q(end_date__lt=now) & Q(is_active=True)
    )
    
    for rule in expired_rules:
        rule.is_active = False
        rule.save()
        
    return f"تم تعطيل {expired_rules.count()} قواعد منتهية الصلاحية"

@shared_task
def notify_price_changes():
    """إرسال إشعارات بتغيرات الأسعار"""
    now = timezone.now()
    recent_changes = Order.objects.filter(
        modified_at__gte=now - timezone.timedelta(hours=1),
        price_changed=True
    )
    
    if recent_changes.exists():
        # سيتم تنفيذ الإشعارات عند تطوير نظام الإشعارات
        pass
        
    return f"تم العثور على {recent_changes.count()} تغييرات في الأسعار"