from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, PurchaseOrder
from .inventory_utils import (
    get_cached_stock_level,
    get_cached_product_list,
    get_cached_dashboard_stats,
    invalidate_product_cache
)

class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # استخدام التخزين المؤقت للإحصائيات
        stats = get_cached_dashboard_stats()
        context.update(stats)
        
        # الحصول على أحدث المنتجات من الذاكرة المؤقتة
        products = get_cached_product_list(include_stock=True)
        context['recent_products'] = products[:10]
        
        return context

@login_required
def product_list(request):
    # البحث والتصفية
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    filter_type = request.GET.get('filter', '')
    sort_by = request.GET.get('sort', '-created_at')

    # الحصول على المنتجات من الذاكرة المؤقتة
    products = get_cached_product_list(
        category_id=category_id if category_id else None,
        include_stock=True
    )

    # تطبيق البحث
    if search_query:
        products = [p for p in products if 
                   search_query.lower() in p.name.lower() or
                   search_query in str(p.code) or
                   search_query.lower() in p.description.lower()]

    # تطبيق فلتر المخزون
    if filter_type == 'low_stock':
        products = [p for p in products if 0 < p.current_stock_calc <= p.minimum_stock]
    elif filter_type == 'out_of_stock':
        products = [p for p in products if p.current_stock_calc <= 0]

    # تطبيق الترتيب
    if hasattr(Product, sort_by.lstrip('-')):
        products = sorted(products, 
                        key=lambda x: getattr(x, sort_by.lstrip('-')),
                        reverse=sort_by.startswith('-'))

    # الصفحات
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'search_query': search_query,
        'selected_category': category_id,
        'selected_filter': filter_type,
        'sort_by': sort_by
    }

    return render(request, 'inventory/product_list.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            code = request.POST.get('code')
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            price = request.POST.get('price')
            minimum_stock = request.POST.get('minimum_stock')
            
            if not all([name, category_id, price, minimum_stock]):
                raise ValueError("جميع الحقول المطلوبة يجب ملؤها")

            category = get_object_or_404(Category, id=category_id)
            
            product = Product.objects.create(
                name=name,
                code=code,
                category=category,
                description=description,
                price=price,
                minimum_stock=minimum_stock
            )
            
            # إعادة تحميل الذاكرة المؤقتة للمنتجات
            invalidate_product_cache(product.id)
            messages.success(request, 'تم إضافة المنتج بنجاح.')
            return redirect('inventory:product_list')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء إضافة المنتج.')
    
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {'categories': categories})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.code = request.POST.get('code')
            category_id = request.POST.get('category')
            product.category = get_object_or_404(Category, id=category_id)
            product.description = request.POST.get('description')
            product.price = request.POST.get('price')
            product.minimum_stock = request.POST.get('minimum_stock')
            
            # Validation
            if not all([product.name, product.category, product.price, product.minimum_stock]):
                raise ValueError("جميع الحقول المطلوبة يجب ملؤها")
            
            product.save()
            # إعادة تحميل الذاكرة المؤقتة للمنتجات
            invalidate_product_cache(product.id)
            messages.success(request, 'تم تحديث المنتج بنجاح.')
            return redirect('inventory:product_list')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء تحديث المنتج.')
    
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {
        'product': product,
        'categories': categories
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product.delete()
            # إعادة تحميل الذاكرة المؤقتة للمنتجات
            invalidate_product_cache(product.id)
            messages.success(request, 'تم حذف المنتج بنجاح.')
        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء حذف المنتج.')
        return redirect('inventory:product_list')
    
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # الحصول على مستوى المخزون من الذاكرة المؤقتة
    current_stock = get_cached_stock_level(product.id)
    
    # استخدام select_related للمعاملات الأخيرة
    recent_transactions = product.transactions.select_related(
        'created_by'
    ).order_by('-date')[:20]
    
    context = {
        'product': product,
        'current_stock': current_stock,
        'stock_status': (
            'نفذ من المخزون' if current_stock == 0
            else 'مخزون منخفض' if current_stock <= product.minimum_stock
            else 'متوفر'
        ),
        'transactions': recent_transactions
    }
    return render(request, 'inventory/product_detail.html', context)

@login_required
def transaction_create(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    if request.method == 'POST':
        # Transaction logic will be implemented later
        pass
    return render(request, 'inventory/transaction_form.html', {'product': product})

# API Endpoints
from django.http import JsonResponse

@login_required
def product_api_detail(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        current_stock = get_cached_stock_level(product.id)
        
        data = {
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'category': str(product.category),
            'description': product.description,
            'price': product.price,
            'minimum_stock': product.minimum_stock,
            'current_stock': current_stock,
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'المنتج غير موجود'}, status=404)

@login_required
def product_api_list(request):
    product_type = request.GET.get('type')
    
    # الحصول على المنتجات من الذاكرة المؤقتة
    products = get_cached_product_list(include_stock=True)
    
    # تطبيق الفلتر حسب النوع
    if product_type:
        if product_type == 'fabric':
            products = [p for p in products if p.category.name == 'أقمشة']
        elif product_type == 'accessory':
            products = [p for p in products if p.category.name == 'اكسسوارات']
    
    # تحويل إلى JSON
    data = [{
        'id': p.id,
        'name': p.name,
        'code': p.code,
        'category': str(p.category),
        'description': p.description,
        'price': p.price,
        'minimum_stock': p.minimum_stock,
        'current_stock': p.current_stock_calc,
    } for p in products]
    
    return JsonResponse(data, safe=False)

# New API View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import Product
from orders.models import Order
from customers.models import Customer
from installations.models import Installation
from accounts.models import ActivityLog

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    try:
        # Calculate statistics
        stats = {
            'totalCustomers': Customer.objects.count(),
            'totalOrders': Order.objects.count(),
            'inventoryValue': Product.objects.aggregate(
                total=Sum('price', default=0))['total'],
            'pendingInstallations': Installation.objects.filter(
                status='pending').count(),
        }

        # Get recent activities
        activities = ActivityLog.objects.select_related('user')\
            .order_by('-timestamp')[:10]\
            .values('id', 'type', 'description', 'timestamp')

        return Response({
            'stats': stats,
            'activities': list(activities)
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=500
        )
