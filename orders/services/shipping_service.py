"""
خدمة إدارة الشحن والتوصيل
"""
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from accounts.utils import send_notification
from ..models import Order, ShippingDetails

class ShippingService:
    """خدمة إدارة عمليات الشحن والتوصيل"""

    @staticmethod
    def create_shipping_details(order, shipping_provider='internal', **kwargs):
        """
        إنشاء تفاصيل شحن جديدة للطلب
        """
        if not order.delivery_type == 'home':
            raise ValidationError(_('لا يمكن إنشاء تفاصيل شحن لطلب استلام من الفرع'))

        if hasattr(order, 'shipping_details'):
            raise ValidationError(_('الطلب لديه تفاصيل شحن بالفعل'))

        shipping_details = ShippingDetails.objects.create(
            order=order,
            shipping_provider=shipping_provider,
            recipient_name=kwargs.get('recipient_name', order.customer.name),
            recipient_phone=kwargs.get('recipient_phone', order.customer.phone),
            shipping_notes=kwargs.get('shipping_notes', ''),
            estimated_delivery_date=kwargs.get('estimated_delivery_date'),
            shipping_cost=kwargs.get('shipping_cost')
        )
        return shipping_details

    @staticmethod
    def update_shipping_status(order, new_status, **kwargs):
        """
        تحديث حالة الشحن
        """
        if not hasattr(order, 'shipping_details'):
            raise ValidationError(_('الطلب ليس لديه تفاصيل شحن'))

        shipping = order.shipping_details
        old_status = shipping.shipping_status
        shipping.shipping_status = new_status

        # تحديث البيانات الإضافية
        if kwargs.get('tracking_number'):
            shipping.tracking_number = kwargs['tracking_number']
        if kwargs.get('estimated_delivery_date'):
            shipping.estimated_delivery_date = kwargs['estimated_delivery_date']
        if kwargs.get('shipping_notes'):
            shipping.shipping_notes = kwargs['shipping_notes']
        if kwargs.get('shipping_cost'):
            shipping.shipping_cost = kwargs['shipping_cost']

        # تحديث تاريخ التسليم الفعلي عند اكتمال التوصيل
        if new_status == 'delivered':
            shipping.actual_delivery_date = timezone.now()
            order.tracking_status = 'delivered'
            order.save()

        shipping.save()

        # إرسال إشعار بتحديث حالة الشحن
        ShippingService._send_shipping_notification(
            order,
            old_status,
            new_status,
            kwargs.get('notes', '')
        )

        return shipping

    @staticmethod
    def get_shipping_cost(order, shipping_provider='internal'):
        """
        حساب تكلفة الشحن (يمكن تخصيص هذه الدالة حسب منطق العمل)
        """
        # هنا يمكن إضافة منطق حساب تكلفة الشحن حسب:
        # - المسافة
        # - وزن/حجم الطلب
        # - نوع الخدمة
        # - شركة الشحن
        # مثال بسيط:
        base_cost = 50  # تكلفة أساسية
        
        # زيادة التكلفة حسب عدد المنتجات
        items_count = order.items.count()
        cost_per_item = 5
        items_cost = items_count * cost_per_item

        # زيادة للشحن السريع
        if shipping_provider != 'internal':
            base_cost *= 1.5

        total_cost = base_cost + items_cost
        return total_cost

    @staticmethod
    def validate_shipping_provider(provider):
        """
        التحقق من صلاحية شركة الشحن
        """
        valid_providers = [choice[0] for choice in ShippingDetails.SHIPPING_PROVIDER_CHOICES]
        if provider not in valid_providers:
            raise ValidationError(_('شركة الشحن غير صالحة'))
        return True

    @staticmethod
    def _send_shipping_notification(order, old_status, new_status, notes=''):
        """
        إرسال إشعار بتحديث حالة الشحن
        """
        status_messages = {
            'pending': _('الطلب في انتظار الشحن'),
            'scheduled': _('تم جدولة شحن الطلب'),
            'picked_up': _('تم استلام الطلب من المستودع'),
            'in_transit': _('الطلب في الطريق'),
            'out_for_delivery': _('الطلب في طريقه للتوصيل'),
            'delivered': _('تم توصيل الطلب'),
            'failed': _('فشل توصيل الطلب'),
        }

        title = _('تحديث حالة شحن الطلب #{}'.format(order.order_number))
        message = _('{}\nتم تغيير حالة الشحن من {} إلى {}'.format(
            status_messages.get(new_status, ''),
            dict(ShippingDetails.SHIPPING_STATUS_CHOICES).get(old_status, ''),
            dict(ShippingDetails.SHIPPING_STATUS_CHOICES).get(new_status, '')
        ))

        if notes:
            message += f'\nملاحظات: {notes}'

        if hasattr(order, 'shipping_details') and order.shipping_details.tracking_number:
            message += f'\nرقم التتبع: {order.shipping_details.tracking_number}'

        # إرسال الإشعار
        send_notification(
            title=title,
            message=message,
            sender=order.created_by,
            sender_department_code='shipping',
            target_department_code='customers',
            target_branch=order.branch,
            priority='high' if new_status in ['delivered', 'failed'] else 'medium',
            related_object=order
        )

    @staticmethod
    def get_shipping_timeline(order):
        """
        الحصول على الجدول الزمني للشحن
        """
        if not hasattr(order, 'shipping_details'):
            return []

        shipping = order.shipping_details
        timeline = []

        # إضافة تواريخ الحالات المختلفة
        if shipping.created_at:
            timeline.append({
                'status': 'pending',
                'date': shipping.created_at,
                'description': _('تم إنشاء طلب الشحن')
            })

        # إضافة تاريخ الجدولة إذا تم تحديده
        if shipping.shipping_status != 'pending' and shipping.estimated_delivery_date:
            timeline.append({
                'status': 'scheduled',
                'date': shipping.estimated_delivery_date,
                'description': _('تم جدولة موعد التوصيل')
            })

        # إضافة تاريخ التسليم الفعلي إذا تم التوصيل
        if shipping.shipping_status == 'delivered' and shipping.actual_delivery_date:
            timeline.append({
                'status': 'delivered',
                'date': shipping.actual_delivery_date,
                'description': _('تم توصيل الطلب')
            })

        return sorted(timeline, key=lambda x: x['date'])
