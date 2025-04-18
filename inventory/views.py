from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Sum
from .models import Product, Category, PurchaseOrder

# لوحة تحكم المخزون الرئيسية
class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        # احسب المنتجات منخفضة المخزون يدويًا لأن current_stock خاصية وليست حقل قاعدة بيانات
        products = Product.objects.all()
        context['low_stock_count'] = sum(1 for p in products if p.current_stock <= p.minimum_stock and p.current_stock > 0)
        context['purchase_orders_count'] = PurchaseOrder.objects.filter(status='ordered').count()
        context['inventory_value'] = sum(p.current_stock * p.price for p in products)
        context['recent_products'] = Product.objects.order_by('-created_at')[:10]
        return context

# عرض قائمة المنتجات مع الترقيم
@login_required
def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'inventory/product_list.html', {'page_obj': page_obj})

# إضافة منتج جديد
@login_required
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        minimum_stock = request.POST.get('minimum_stock')
        category = get_object_or_404(Category, id=category_id)
        Product.objects.create(
            name=name,
            code=code,
            category=category,
            description=description,
            price=price,
            minimum_stock=minimum_stock
        )
        messages.success(request, 'تم إضافة المنتج بنجاح.')
        return redirect('product_list')
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {'categories': categories})

# تعديل منتج
@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.code = request.POST.get('code')
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, id=category_id)
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.minimum_stock = request.POST.get('minimum_stock')
        product.save()
        messages.success(request, 'تم تعديل المنتج بنجاح.')
        return redirect('product_list')
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {'product': product, 'categories': categories})

# حذف منتج
@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'تم حذف المنتج بنجاح.')
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

# عرض تفاصيل منتج
@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'inventory/product_detail.html', {'product': product})

# إنشاء معاملة (فارغة مؤقتاً)
@login_required
def transaction_create(request, product_pk):
    # يمكنك لاحقاً إضافة منطق إنشاء معاملة مخزون هنا
    return render(request, 'inventory/transaction_form.html', {'product_pk': product_pk})

# API: تفاصيل منتج
from django.http import JsonResponse
@login_required
def product_api_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
        data = {
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'category': str(product.category),
            'description': product.description,
            'price': product.price,
            'minimum_stock': product.minimum_stock,
            'current_stock': product.current_stock,
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

# API: قائمة المنتجات
@login_required
def product_api_list(request):
    products = Product.objects.all()
    data = [
        {
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'category': str(p.category),
            'description': p.description,
            'price': p.price,
            'minimum_stock': p.minimum_stock,
            'current_stock': p.current_stock,
        }
        for p in products
    ]
    return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        context['low_stock_count'] = sum(1 for p in Product.objects.all() if p.current_stock <= p.minimum_stock and p.current_stock > 0)
        context['purchase_orders_count'] = PurchaseOrder.objects.filter(status='ordered').count()
        context['inventory_value'] = sum(p.current_stock * p.price for p in Product.objects.all())
        context['recent_products'] = Product.objects.order_by('-created_at')[:10]
        return context
