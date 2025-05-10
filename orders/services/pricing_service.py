from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from typing import Optional, List, Dict
from ..models import DynamicPricing, Order, OrderItem

class PricingService:
    @staticmethod
    def calculate_dynamic_price(order: Order) -> Decimal:
        """حساب السعر النهائي للطلب باستخدام قواعد التسعير الديناميكي"""
        # حساب السعر الأساسي
        base_price = sum(item.quantity * item.unit_price for item in order.items.all())
        
        # البحث عن قواعد التسعير النشطة والمنطبقة
        now = timezone.now()
        active_rules = DynamicPricing.objects.filter(
            Q(is_active=True) &
            (Q(start_date__isnull=True) | Q(start_date__lte=now)) &
            (Q(end_date__isnull=True) | Q(end_date__gte=now))
        ).order_by('-priority')
        
        # تطبيق القواعد المنطبقة
        final_price = base_price
        applied_rule = None
        max_discount = 0
        
        for rule in active_rules:
            if rule.is_applicable_to_order(order):
                discount = base_price * (rule.discount_percentage / 100)
                if discount > max_discount:
                    max_discount = discount
                    applied_rule = rule
        
        if applied_rule:
            final_price = base_price - max_discount
            # تحديث القاعدة المطبقة والإشارة إلى تغيير السعر
            if order.dynamic_pricing_rule != applied_rule or order.final_price != final_price:
                order.dynamic_pricing_rule = applied_rule
                order.price_changed = True
        
        return final_price

    @staticmethod
    def check_price_changes() -> List[Order]:
        """
        فحص التغييرات في الأسعار للطلبات النشطة
        """
        active_orders = Order.objects.filter(
            status__in=['pending', 'processing'],
            dynamic_pricing_rule__isnull=False
        )
        
        updated_orders = []
        for order in active_orders:
            new_price = PricingService.calculate_dynamic_price(order)
            if new_price != order.final_price:
                order.final_price = new_price
                order.save()
                updated_orders.append(order)
                
        return updated_orders

    @staticmethod
    def analyze_rule_effectiveness(rule_id: int, date_range: int = 30) -> Dict:
        """تحليل فعالية قاعدة التسعير"""
        start_date = timezone.now() - timedelta(days=date_range)
        rule = DynamicPricing.objects.get(id=rule_id)
        
        affected_orders = Order.objects.filter(
            dynamic_pricing_rule=rule,
            created_at__gte=start_date
        )
        
        total_discount = sum(
            order.total_amount - order.final_price 
            for order in affected_orders if order.final_price
        )
        
        conversion_rate = affected_orders.filter(
            status__in=['processing', 'ready', 'delivered']
        ).count() / affected_orders.count() if affected_orders.exists() else 0
        
        return {
            'rule_name': rule.name,
            'orders_count': affected_orders.count(),
            'total_discount': total_discount,
            'conversion_rate': conversion_rate,
            'avg_order_value': affected_orders.aggregate(
                avg_value=Avg('final_price')
            )['avg_value'] or 0
        }

    @staticmethod
    def generate_pricing_report(start_date: datetime = None, 
                              end_date: datetime = None) -> Dict:
        """إنشاء تقرير عن التسعير الديناميكي"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
            
        orders = Order.objects.filter(
            created_at__range=(start_date, end_date),
            dynamic_pricing_rule__isnull=False
        )
        
        rules_summary = {}
        for order in orders:
            rule = order.dynamic_pricing_rule
            if rule.id not in rules_summary:
                rules_summary[rule.id] = {
                    'name': rule.name,
                    'orders_count': 0,
                    'total_discount': 0,
                    'total_revenue': 0
                }
            
            rules_summary[rule.id]['orders_count'] += 1
            if order.final_price:
                discount = order.total_amount - order.final_price
                rules_summary[rule.id]['total_discount'] += discount
                rules_summary[rule.id]['total_revenue'] += order.final_price
        
        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(
                total=Sum('final_price')
            )['total'] or 0,
            'total_discount': orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0 - orders.aggregate(
                total=Sum('final_price')
            )['total'] or 0,
            'rules_summary': rules_summary
        }

    @staticmethod
    def suggest_price_adjustments() -> List[Dict]:
        """اقتراح تعديلات على قواعد التسعير بناءً على البيانات التاريخية"""
        suggestions = []
        rules = DynamicPricing.objects.filter(is_active=True)
        
        for rule in rules:
            effectiveness = PricingService.analyze_rule_effectiveness(rule.id)
            
            if effectiveness['conversion_rate'] < 0.3:  # معدل تحويل منخفض
                if effectiveness['orders_count'] > 10:  # عينة كافية
                    suggestions.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'suggestion': 'زيادة نسبة الخصم',
                        'reason': 'معدل التحويل منخفض',
                        'current_discount': rule.discount_percentage,
                        'suggested_discount': min(
                            rule.discount_percentage + 5, 
                            50  # الحد الأقصى للخصم
                        )
                    })
            
            if effectiveness['orders_count'] < 5 and rule.created_at < timezone.now() - timedelta(days=14):
                suggestions.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'suggestion': 'مراجعة شروط القاعدة',
                    'reason': 'عدد الطلبات المتأثرة منخفض جداً'
                })
        
        return suggestions