from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, PurchaseOrder, SupplyOrder, Category, Supplier, Warehouse

class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        from collections import Counter
        context = super().get_context_data(**kwargs)
        # المنتجات
        products = Product.objects.all()
        context['total_products'] = products.count()
        context['low_stock_count'] = sum(1 for p in products if p.current_stock <= p.minimum_stock and p.current_stock > 0)
        context['recent_products'] = products.order_by('-created_at')[:10]
        # الفئات
        categories = Category.objects.all()
        context['total_categories'] = categories.count()
        # توزيع المنتجات حسب الفئة
        category_labels = []
        category_counts = []
        for cat in categories:
            category_labels.append(cat.name)
            category_counts.append(products.filter(category=cat).count())
        context['category_labels'] = category_labels
        context['category_counts'] = category_counts
        # الموردين
        suppliers = Supplier.objects.all()
        context['total_suppliers'] = suppliers.count()
        context['recent_suppliers'] = suppliers.order_by('-id')[:5]
        # المخازن
        warehouses = Warehouse.objects.all()
        context['total_warehouses'] = warehouses.count()
        # أوامر الشراء
        purchase_orders = PurchaseOrder.objects.all()
        context['purchase_orders_count'] = purchase_orders.count()
        context['recent_purchase_orders'] = purchase_orders.order_by('-created_at')[:5]
        # توزيع أوامر الشراء حسب الحالة
        po_status_labels = []
        po_status_counts = []
        po_status_counter = Counter(purchase_orders.values_list('status', flat=True))
        for status, count in po_status_counter.items():
            po_status_labels.append(status)
            po_status_counts.append(count)
        context['po_status_labels'] = po_status_labels
        context['po_status_counts'] = po_status_counts
        # أوامر التوريد
        supply_orders = SupplyOrder.objects.all()
        context['supply_orders_count'] = supply_orders.count()
        context['recent_supply_orders'] = supply_orders.order_by('-created_at')[:5]
        return context
