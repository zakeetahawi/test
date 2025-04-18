from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, PurchaseOrder

class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        context['low_stock_count'] = sum(1 for p in Product.objects.all() if p.current_stock <= p.minimum_stock and p.current_stock > 0)
        context['purchase_orders_count'] = PurchaseOrder.objects.filter(status='ordered').count()
        context['inventory_value'] = sum(p.current_stock * p.price for p in Product.objects.all())
        context['recent_products'] = Product.objects.order_by('-created_at')[:10]
        return context
