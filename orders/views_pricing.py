from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import DynamicPricing, Order
from .services.pricing_service import PricingService
from .serializers import DynamicPricingSerializer
from django.db.models import Q

class DynamicPricingViewSet(viewsets.ModelViewSet):
    """
    واجهة برمجة للتحكم بقواعد التسعير الديناميكي
    """
    queryset = DynamicPricing.objects.all()
    serializer_class = DynamicPricingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DynamicPricing.objects.all()
        if self.action == 'list':
            is_active = self.request.query_params.get('is_active', None)
            rule_type = self.request.query_params.get('rule_type', None)
            
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            if rule_type:
                queryset = queryset.filter(rule_type=rule_type)
                
        return queryset.order_by('-priority', '-created_at')
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """تفعيل/تعطيل قاعدة التسعير"""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        return Response({
            'status': 'success',
            'is_active': rule.is_active
        })
    
    @action(detail=True, methods=['get'])
    def affected_orders(self, request, pk=None):
        """عرض الطلبات المتأثرة بقاعدة التسعير"""
        rule = self.get_object()
        now = timezone.now()
        
        affected_orders = Order.objects.filter(
            Q(status__in=['pending', 'processing']) &
            Q(created_at__gte=now - timezone.timedelta(days=30))
        )
        
        orders_data = []
        for order in affected_orders:
            if rule.is_applicable_to_order(order):
                current_price = order.final_price or 0
                new_price = PricingService.calculate_dynamic_price(order)
                price_diff = new_price - current_price
                
                orders_data.append({
                    'order_number': order.order_number,
                    'current_price': current_price,
                    'new_price': new_price,
                    'price_difference': price_diff,
                    'customer': order.customer.name,
                    'created_at': order.created_at
                })
        
        return Response(orders_data)
    
    @action(detail=False, methods=['post'])
    def apply_to_orders(self, request):
        """تطبيق قواعد التسعير على الطلبات المحددة"""
        order_ids = request.data.get('order_ids', [])
        if not order_ids:
            return Response(
                {'error': 'يجب تحديد طلب واحد على الأقل'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        orders = Order.objects.filter(id__in=order_ids)
        updated_orders = []
        
        for order in orders:
            old_price = order.final_price
            new_price = PricingService.calculate_dynamic_price(order)
            if new_price != old_price:
                order.final_price = new_price
                order.save()
                updated_orders.append({
                    'order_number': order.order_number,
                    'old_price': old_price,
                    'new_price': new_price
                })
                
        return Response({
            'status': 'success',
            'updated_orders': updated_orders
        })
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get pricing analytics and reports"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = timezone.datetime.fromisoformat(start_date)
        if end_date:
            end_date = timezone.datetime.fromisoformat(end_date)
            
        report = PricingService.generate_pricing_report(start_date, end_date)
        suggestions = PricingService.suggest_price_adjustments()
        
        return Response({
            'report': report,
            'suggestions': suggestions
        })

    @action(detail=True, methods=['get'])
    def effectiveness(self, request, pk=None):
        """Get effectiveness analysis for a specific pricing rule"""
        date_range = int(request.query_params.get('date_range', 30))
        analysis = PricingService.analyze_rule_effectiveness(
            rule_id=pk,
            date_range=date_range
        )
        return Response(analysis)

    @action(detail=True, methods=['post'])
    def apply_suggestion(self, request, pk=None):
        """Apply a suggested price adjustment"""
        rule = self.get_object()
        suggested_discount = request.data.get('suggested_discount')
        
        if suggested_discount is None:
            return Response(
                {'error': 'نسبة الخصم المقترحة مطلوبة'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        rule.discount_percentage = suggested_discount
        rule.save()
        
        return Response({
            'status': 'success',
            'message': 'تم تطبيق التعديل المقترح بنجاح'
        })

    @action(detail=False, methods=['post'])
    def test_rule(self, request):
        """اختبار قاعدة تسعير على طلب تجريبي"""
        order_id = request.data.get('order_id')
        rule_data = request.data.get('rule')
        
        if not order_id:
            return Response(
                {'error': 'معرف الطلب مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'الطلب غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # إنشاء قاعدة تسعير مؤقتة للاختبار
        if rule_data:
            temp_rule = DynamicPricing(**rule_data)
            # لا نحفظ القاعدة، نستخدمها فقط للاختبار
            current_price = order.final_price or order.total_amount
            if temp_rule.is_applicable_to_order(order):
                test_price = current_price * (1 - temp_rule.discount_percentage / 100)
                return Response({
                    'is_applicable': True,
                    'current_price': current_price,
                    'test_price': test_price,
                    'discount_amount': current_price - test_price
                })
            return Response({
                'is_applicable': False,
                'reason': 'القاعدة غير منطبقة على هذا الطلب'
            })
            
        return Response(
            {'error': 'بيانات قاعدة التسعير مطلوبة'},
            status=status.HTTP_400_BAD_REQUEST
        )