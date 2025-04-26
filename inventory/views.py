from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Sum, Q
from .models import Product, Category, PurchaseOrder

class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all products
        products = Product.objects.all()
        
        # Basic statistics
        context['total_products'] = products.count()
        context['total_categories'] = Category.objects.count()
        
        # Low stock products
        low_stock_products = [p for p in products if p.current_stock <= p.minimum_stock and p.current_stock > 0]
        context['low_stock_products_count'] = len(low_stock_products)
        
        # Recent products with all related data
        context['recent_products'] = products.select_related('category').order_by('-created_at')[:10]
        
        # Additional statistics
        context['out_of_stock_count'] = sum(1 for p in products if p.current_stock == 0)
        context['total_value'] = sum(p.current_stock * p.price for p in products)
        
        return context

@login_required
def product_list(request):
    # Base queryset
    products = Product.objects.all().select_related('category')
    categories = Category.objects.all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Category filter
    category_id = request.GET.get('category', '')
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
        except ValueError:
            pass

    # Stock status filter
    filter_type = request.GET.get('filter', '')
    if filter_type == 'low_stock':
        products = [p for p in products if p.current_stock <= p.minimum_stock and p.current_stock > 0]
    elif filter_type == 'out_of_stock':
        products = [p for p in products if p.current_stock == 0]

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if hasattr(Product, sort_by.lstrip('-')):
        products = sorted(products, 
                        key=lambda x: getattr(x, sort_by.lstrip('-')),
                        reverse=sort_by.startswith('-'))

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
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
            
            # Validation
            if not all([name, category_id, price, minimum_stock]):
                raise ValueError("جميع الحقول المطلوبة يجب ملؤها")

            category = get_object_or_404(Category, id=category_id)
            
            # Create product
            Product.objects.create(
                name=name,
                code=code,
                category=category,
                description=description,
                price=price,
                minimum_stock=minimum_stock
            )
            
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
            messages.success(request, 'تم حذف المنتج بنجاح.')
        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء حذف المنتج.')
        return redirect('inventory:product_list')
    
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
        'stock_status': (
            'نفذ من المخزون' if product.current_stock == 0
            else 'مخزون منخفض' if product.current_stock <= product.minimum_stock
            else 'متوفر'
        )
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
        return JsonResponse({'error': 'المنتج غير موجود'}, status=404)

@login_required
def product_api_list(request):
    products = Product.objects.all()
    data = [{
        'id': p.id,
        'name': p.name,
        'code': p.code,
        'category': str(p.category),
        'description': p.description,
        'price': p.price,
        'minimum_stock': p.minimum_stock,
        'current_stock': p.current_stock,
    } for p in products]
    return JsonResponse(data, safe=False)
