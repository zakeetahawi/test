from rest_framework import serializers
from .models import DynamicPricing, Order

class DynamicPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricing
        fields = [
            'id', 'name', 'rule_type', 'discount_percentage',
            'min_quantity', 'min_amount', 'customer_type',
            'start_date', 'end_date', 'is_active', 'priority',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """التحقق من صحة البيانات حسب نوع القاعدة"""
        rule_type = data.get('rule_type')
        
        if rule_type == 'quantity' and not data.get('min_quantity'):
            raise serializers.ValidationError({
                'min_quantity': 'الحد الأدنى للكمية مطلوب لقواعد التسعير بالكمية'
            })
            
        if rule_type == 'customer_type' and not data.get('customer_type'):
            raise serializers.ValidationError({
                'customer_type': 'نوع العميل مطلوب لقواعد التسعير حسب نوع العميل'
            })
            
        if rule_type == 'special_offer' and not data.get('min_amount'):
            raise serializers.ValidationError({
                'min_amount': 'الحد الأدنى للمبلغ مطلوب للعروض الخاصة'
            })
            
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
                })
                
        return data