from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Sum, Q
from .models import Product, Category, PurchaseOrder, StockTransaction, StockTransactionReason, Supplier, Warehouse, SupplyOrder, SupplyOrderItem, CustomerOrder, CustomerOrderItem
from customers.models import Customer
from .forms import CustomerOrderForm, CustomerOrderItemFormSet

class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # المنتجات
        products = Product.objects.all()
        context['total_products'] = products.count()
        # ORM does not support filtering on @property 'current_stock'. Use Python-side filtering:
        context['low_stock_products_count'] = sum(1 for p in products if p.current_stock <= p.minimum_stock)
        context['recent_products'] = products.order_by('-id')[:5]
        
        # الفئات
        context['total_categories'] = Category.objects.count()
        
        # الموردين
        context['total_suppliers'] = Supplier.objects.count()
        context['recent_suppliers'] = Supplier.objects.order_by('-id')[:5]
        
        # المخازن
        context['total_warehouses'] = Warehouse.objects.count()
        context['active_warehouses'] = Warehouse.objects.filter(is_active=True).count()
        
        # Additional statistics
        context['out_of_stock_count'] = sum(1 for p in products if p.current_stock == 0)
        context['total_value'] = sum(p.current_stock * p.price for p in products)
        
        # بيانات رسم بياني: توزيع المنتجات حسب الفئة
        from collections import Counter
        category_labels = []
        category_counts = []
        category_data = Product.objects.values_list('category__name', flat=True)
        cat_counter = Counter(category_data)
        for name, count in cat_counter.items():
            category_labels.append(name or 'غير مصنف')
            category_counts.append(count)
        context['category_labels'] = category_labels
        context['category_counts'] = category_counts

        # بيانات رسم بياني: توزيع أوامر الشراء حسب الحالة
        po_status_labels = []
        po_status_counts = []
        po_status_qs = PurchaseOrder.objects.values_list('status', flat=True)
        po_status_counter = Counter(po_status_qs)
        for status, count in po_status_counter.items():
            po_status_labels.append(status)
            po_status_counts.append(count)
        context['po_status_labels'] = po_status_labels
        context['po_status_counts'] = po_status_counts

        # بيانات الموردين والمخازن
        context['total_suppliers'] = context['total_suppliers']
        context['total_warehouses'] = context['total_warehouses']
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

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_products')
        if 'bulk_delete' in request.POST:
            if not user_is_inventory_manager(request.user):
                messages.error(request, 'ليس لديك صلاحية للحذف الجماعي.')
                return redirect('inventory:product_list')
            Product.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'تم حذف {len(selected_ids)} من المنتجات بنجاح.')
            return redirect('inventory:product_list')
        if 'bulk_export' in request.POST:
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'اسم المنتج', 'الصنف', 'المخزون', 'الحد الأدنى', 'السعر'])
            for p in Product.objects.filter(id__in=selected_ids):
                writer.writerow([p.id, p.name, p.category.name if p.category else '', p.stock, p.minimum_stock, p.price])
            return response

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
            unit = request.POST.get('unit')
            
            # Validation
            if not all([name, category_id, price, minimum_stock, unit]):
                raise ValueError("جميع الحقول المطلوبة يجب ملؤها")
            if not code:
                raise ValueError("كود المنتج مطلوب")
            if Product.objects.filter(code=code).exists():
                raise ValueError("كود المنتج مستخدم بالفعل. يرجى اختيار كود آخر.")

            category = get_object_or_404(Category, id=category_id)
            
            # Convert price and minimum_stock to correct types
            try:
                price = float(price)
            except Exception:
                raise ValueError("قيمة السعر غير صحيحة. يرجى إدخال رقم.")
            try:
                minimum_stock = int(minimum_stock)
            except Exception:
                raise ValueError("قيمة الحد الأدنى للمخزون غير صحيحة. يرجى إدخال رقم.")

            # Create product
            Product.objects.create(
                name=name,
                code=code,
                category=category,
                description=description,
                price=price,
                minimum_stock=minimum_stock,
                unit=unit
            )
            
            messages.success(request, 'تم إضافة المنتج بنجاح.')
            return redirect('inventory:product_list')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إضافة المنتج: {str(e)}')
    
    # Only allow leaf categories (categories with no children)
    categories = Category.objects.filter(children__isnull=True)
    unit_choices = Product.UNIT_CHOICES
    # Preserve entered values if error
    product_data = {
        'name': request.POST.get('name', ''),
        'code': request.POST.get('code', ''),
        'category_id': request.POST.get('category', ''),
        'description': request.POST.get('description', ''),
        'price': request.POST.get('price', ''),
        'minimum_stock': request.POST.get('minimum_stock', ''),
        'unit': request.POST.get('unit', ''),
    } if request.method == 'POST' else None
    return render(request, 'inventory/product_form.html', {'categories': categories, 'unit_choices': unit_choices, 'product': product_data})

@login_required
def product_update(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لتعديل المنتجات.')
        return redirect('inventory:product_list')
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
    unit_choices = Product.UNIT_CHOICES
    return render(request, 'inventory/product_form.html', {
        'product': product,
        'categories': categories,
        'unit_choices': unit_choices
    })

@login_required
def product_delete(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لحذف المنتجات.')
        return redirect('inventory:product_list')
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

from django import forms

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['transaction_type', 'reason', 'quantity', 'reference', 'notes', 'warehouse']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'reason': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'required': True}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'warehouse': forms.Select(attrs={'class': 'form-select', 'required': True}),
        }

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        current_warehouse = kwargs.pop('current_warehouse', None)
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].label = 'نوع الحركة'
        self.fields['reason'].label = 'السبب'
        self.fields['quantity'].label = 'الكمية'
        self.fields['reference'].label = 'المرجع'
        self.fields['notes'].label = 'ملاحظات'
        # تخصيص خيارات المخزن عند التحويل
        if self.data.get('transaction_type') == 'transfer' or self.initial.get('transaction_type') == 'transfer':
            if current_warehouse:
                self.fields['warehouse'].queryset = self.fields['warehouse'].queryset.exclude(pk=current_warehouse.pk)
            self.fields['warehouse'].label = 'إلى'
        else:
            self.fields['warehouse'].label = 'المخزن'

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')
        product = self.product
        warehouse = cleaned_data.get('warehouse')
        if not warehouse:
            self.add_error('warehouse', 'يجب اختيار مخزن.')
        if transaction_type == 'out' and product and quantity:
            if quantity > product.current_stock:
                self.add_error('quantity', 'الكمية المطلوبة أكبر من المخزون المتاح.')
        return cleaned_data

@login_required
def transaction_create(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    if request.method == 'POST':
        # محاولة جلب المخزن الحالي من آخر حركة مخزون للمنتج
        last_in_tx = product.stock_transactions.filter(transaction_type__in=['in', 'transfer']).order_by('-date').first()
        current_warehouse = last_in_tx.warehouse if last_in_tx else None
        form = StockTransactionForm(request.POST, product=product, current_warehouse=current_warehouse)
        if form.is_valid():
            transaction = form.save(commit=False)
            import logging
            logging.warning(f"DEBUG: قبل التعيين، transaction.product = {getattr(transaction, 'product', None)}")
            transaction.product = product
            logging.warning(f"DEBUG: بعد التعيين، transaction.product = {getattr(transaction, 'product', None)}")
            transaction.created_by = request.user
            # طباعة جميع الحقول المهمة
            logging.warning(f"DEBUG: transaction fields: product={transaction.product}, warehouse={transaction.warehouse}, type={transaction.transaction_type}, qty={transaction.quantity}, ref={transaction.reference}")
            if not transaction.product:
                messages.error(request, 'خطأ: لم يتم تعيين المنتج للحركة!')
                return render(request, 'inventory/transaction_form.html', {
                    'product': product,
                    'form': form,
                })
            try:
                transaction.save()
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ الحركة: {e}')
                return render(request, 'inventory/transaction_form.html', {
                    'product': product,
                    'form': form,
                })
            messages.success(request, 'تم تسجيل حركة المخزون بنجاح.')
            return redirect('inventory:product_detail', pk=product.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.')
    else:
        last_in_tx = product.stock_transactions.filter(transaction_type__in=['in', 'transfer']).order_by('-date').first()
        current_warehouse = last_in_tx.warehouse if last_in_tx else None
        form = StockTransactionForm(product=product, current_warehouse=current_warehouse)
    return render(request, 'inventory/transaction_form.html', {
        'product': product,
        'form': form,
    })


# API Endpoints
from django.http import JsonResponse

from django.http import HttpResponse
import csv

@login_required
def transaction_list(request):
    transactions = StockTransaction.objects.select_related('product', 'reason').order_by('-date')
    products = Product.objects.all()
    reasons = StockTransactionReason.objects.all()
    transaction_types = StockTransaction.TRANSACTION_TYPES

    # Filters
    product_id = request.GET.get('product')
    reason_id = request.GET.get('reason')
    transaction_type = request.GET.get('transaction_type')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if product_id:
        transactions = transactions.filter(product_id=product_id)
    if reason_id:
        transactions = transactions.filter(reason_id=reason_id)
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    if search:
        transactions = transactions.filter(
            Q(product__name__icontains=search) |
            Q(reason__name__icontains=search) |
            Q(notes__icontains=search) |
            Q(reference__icontains=search)
        )

    # Export to CSV
    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stock_transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['التاريخ', 'نوع الحركة', 'المنتج', 'السبب', 'الكمية', 'الوحدة', 'المرجع', 'ملاحظات'])
        for t in transactions:
            writer.writerow([
                t.date.strftime('%Y-%m-%d %H:%M'),
                t.get_transaction_type_display(),
                t.product.name,
                t.reason.name,
                t.quantity,
                t.product.get_unit_display(),
                t.reference,
                t.notes
            ])
        return response

    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/transaction_list.html', {
        'transactions': page_obj,
        'products': products,
        'reasons': reasons,
        'transaction_types': transaction_types,
        'selected_product': product_id,
        'selected_reason': reason_id,
        'selected_type': transaction_type,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    })


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

# --------------------------
# Advanced Reports Views
# --------------------------
from django.contrib.auth.decorators import login_required

@login_required
def advanced_reports(request):
    return render(request, 'inventory/advanced_reports.html')

@login_required
def product_report(request):
    # Placeholder: يمكن لاحقاً إضافة بيانات تفصيلية
    return render(request, 'inventory/product_report.html')

@login_required
def supplier_report(request):
    # Placeholder: يمكن لاحقاً إضافة بيانات تفصيلية
    return render(request, 'inventory/supplier_report.html')

@login_required
def warehouse_report(request):
    # Placeholder: يمكن لاحقاً إضافة بيانات تفصيلية
    return render(request, 'inventory/warehouse_report.html')

# --------------------------
# Supply Order Report View
# --------------------------
from django.http import HttpResponse
import csv
from django.utils import timezone

@login_required
def supply_order_report(request):
    # Filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    supplier_id = request.GET.get('supplier')
    warehouse_id = request.GET.get('warehouse')
    status = request.GET.get('status')
    order_type = request.GET.get('order_type')

    orders = SupplyOrder.objects.select_related('supplier', 'from_warehouse', 'to_warehouse').prefetch_related('items__product')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)
    if warehouse_id:
        orders = orders.filter(
            models.Q(from_warehouse_id=warehouse_id) | models.Q(to_warehouse_id=warehouse_id)
        )
    if status:
        orders = orders.filter(status=status)
    if order_type:
        orders = orders.filter(order_type=order_type)
    orders = orders.order_by('-created_at')

    # Gather related stock transactions
    for order in orders:
        order.related_transactions = list(
            StockTransaction.objects.filter(reference=f"SupplyOrder:{order.order_number}")
        )

    # Export to Excel
    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="supply_order_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'رقم الطلب', 'التاريخ', 'المورد', 'من مخزن', 'إلى مخزن', 'الحالة', 'نوع الطلب',
            'المنتجات (الكمية المطلوبة/المستلمة)', 'حركات المخزون المرتبطة'
        ])
        for order in orders:
            items_str = "; ".join([
                f"{item.product} ({item.quantity}/{item.delivered_quantity})" for item in order.items.all()
            ])
            tx_str = "; ".join([
                f"{tx.get_transaction_type_display()} - {tx.product} ({tx.quantity}) - {tx.warehouse}" for tx in order.related_transactions
            ]) or 'لا توجد حركات'
            writer.writerow([
                order.order_number,
                order.created_at.strftime('%Y-%m-%d'),
                str(order.supplier) if order.supplier else '',
                str(order.from_warehouse) if order.from_warehouse else '',
                str(order.to_warehouse) if order.to_warehouse else '',
                order.get_status_display(),
                order.get_order_type_display(),
                items_str,
                tx_str
            ])
        return response

    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    context = {
        'orders': orders,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'date_from': date_from or '',
        'date_to': date_to or '',
        'selected_supplier': supplier_id or '',
        'selected_warehouse': warehouse_id or '',
        'selected_status': status or '',
        'selected_order_type': order_type or '',
        'request': request,
    }
    return render(request, 'inventory/supply_order_report.html', context)

# --------------------------
# Category CRUD
# --------------------------
from .models import Category, Supplier, Warehouse, WarehouseLocation, PurchaseOrder, PurchaseOrderItem
from accounts.models import Branch, User
from .utils import user_is_inventory_manager

@login_required
def category_list(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_categories')
        if 'bulk_delete' in request.POST:
            if not user_is_inventory_manager(request.user):
                messages.error(request, 'ليس لديك صلاحية للحذف الجماعي.')
                return redirect('inventory:category_list')
            Category.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'تم حذف {len(selected_ids)} من الفئات بنجاح.')
            return redirect('inventory:category_list')
        if 'bulk_export' in request.POST:
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="categories_export.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'الاسم', 'الوصف', 'الفئة الأب'])
            for c in Category.objects.filter(id__in=selected_ids):
                writer.writerow([c.id, c.name, c.description, c.parent.name if c.parent else ''])
            return response
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        parent = Category.objects.filter(id=parent_id).first() if parent_id else None
        Category.objects.create(name=name, description=description, parent=parent)
        messages.success(request, 'تم إضافة الفئة بنجاح.')
        return redirect('inventory:category_list')
    categories = Category.objects.all()
    return render(request, 'inventory/category_form.html', {'categories': categories})

@login_required
def category_update(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لتعديل الفئات.')
        return redirect('inventory:category_list')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        category.parent = Category.objects.filter(id=parent_id).first() if parent_id else None
        category.save()
        messages.success(request, 'تم تحديث الفئة بنجاح.')
        return redirect('inventory:category_list')
    categories = Category.objects.exclude(pk=pk)
    return render(request, 'inventory/category_form.html', {'category': category, 'categories': categories})

@login_required
def category_delete(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لحذف الفئات.')
        return redirect('inventory:category_list')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'تم حذف الفئة بنجاح.')
        return redirect('inventory:category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})

# --------------------------
# Supplier CRUD
# --------------------------
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_suppliers')
        if 'bulk_delete' in request.POST:
            if not user_is_inventory_manager(request.user):
                messages.error(request, 'ليس لديك صلاحية للحذف الجماعي.')
                return redirect('inventory:supplier_list')
            Supplier.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'تم حذف {len(selected_ids)} من الموردين بنجاح.')
            return redirect('inventory:supplier_list')
        if 'bulk_export' in request.POST:
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="suppliers_export.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'الاسم', 'الشخص المسؤول', 'الهاتف', 'البريد الإلكتروني'])
            for s in Supplier.objects.filter(id__in=selected_ids):
                writer.writerow([s.id, s.name, s.contact_person, s.phone, s.email])
            return response
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        tax_number = request.POST.get('tax_number')
        notes = request.POST.get('notes')
        Supplier.objects.create(
            name=name, contact_person=contact_person, phone=phone, email=email,
            address=address, tax_number=tax_number, notes=notes)
        messages.success(request, 'تم إضافة المورد بنجاح.')
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/supplier_form.html')

@login_required
def supplier_update(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لتعديل الموردين.')
        return redirect('inventory:supplier_list')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.contact_person = request.POST.get('contact_person')
        supplier.phone = request.POST.get('phone')
        supplier.email = request.POST.get('email')
        supplier.address = request.POST.get('address')
        supplier.tax_number = request.POST.get('tax_number')
        supplier.notes = request.POST.get('notes')
        supplier.save()
        messages.success(request, 'تم تحديث المورد بنجاح.')
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/supplier_form.html', {'supplier': supplier})

@login_required
def supplier_delete(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لحذف الموردين.')
        return redirect('inventory:supplier_list')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'تم حذف المورد بنجاح.')
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/supplier_confirm_delete.html', {'supplier': supplier})

# --------------------------
# Warehouse CRUD
# --------------------------
@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_warehouses')
        if 'bulk_delete' in request.POST:
            if not user_is_inventory_manager(request.user):
                messages.error(request, 'ليس لديك صلاحية للحذف الجماعي.')
                return redirect('inventory:warehouse_list')
            Warehouse.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'تم حذف {len(selected_ids)} من المخازن بنجاح.')
            return redirect('inventory:warehouse_list')
        if 'bulk_export' in request.POST:
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="warehouses_export.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'الاسم', 'الكود', 'الفرع', 'العنوان', 'المدير', 'الحالة'])
            for w in Warehouse.objects.filter(id__in=selected_ids):
                writer.writerow([w.id, w.name, w.code, w.branch.name if w.branch else '', w.address, w.manager.get_full_name() if w.manager else '', 'نشط' if w.is_active else 'غير نشط'])
            return response
    return render(request, 'inventory/warehouse_list.html', {'warehouses': warehouses})

@login_required
def warehouse_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        branch_id = request.POST.get('branch')
        address = request.POST.get('address')
        manager_id = request.POST.get('manager')
        is_active = bool(request.POST.get('is_active'))
        notes = request.POST.get('notes')
        branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
        manager = User.objects.filter(id=manager_id).first() if manager_id else None
        Warehouse.objects.create(
            name=name, code=code, branch=branch, address=address,
            manager=manager, is_active=is_active, notes=notes)
        messages.success(request, 'تم إضافة المخزن بنجاح.')
        return redirect('inventory:warehouse_list')
    branches = Branch.objects.all()
    managers = User.objects.all()
    return render(request, 'inventory/warehouse_form.html', {'branches': branches, 'managers': managers})

@login_required
def warehouse_update(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لتعديل المخازن.')
        return redirect('inventory:warehouse_list')
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.name = request.POST.get('name')
        warehouse.code = request.POST.get('code')
        branch_id = request.POST.get('branch')
        warehouse.branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
        warehouse.address = request.POST.get('address')
        manager_id = request.POST.get('manager')
        warehouse.manager = User.objects.filter(id=manager_id).first() if manager_id else None
        warehouse.is_active = bool(request.POST.get('is_active'))
        warehouse.notes = request.POST.get('notes')
        warehouse.save()
        messages.success(request, 'تم تحديث المخزن بنجاح.')
        return redirect('inventory:warehouse_list')
    branches = Branch.objects.all()
    managers = User.objects.all()
    return render(request, 'inventory/warehouse_form.html', {'warehouse': warehouse, 'branches': branches, 'managers': managers})

@login_required
def warehouse_delete(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لحذف المخازن.')
        return redirect('inventory:warehouse_list')
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
        messages.success(request, 'تم حذف المخزن بنجاح.')
        return redirect('inventory:warehouse_list')
    return render(request, 'inventory/warehouse_confirm_delete.html', {'warehouse': warehouse})

# --------------------------
# PurchaseOrder CRUD
# --------------------------

from .models import SupplyOrder, SupplyOrderItem

@login_required
def supply_order_list(request):
    qs = SupplyOrder.objects.select_related('supplier', 'customer', 'from_warehouse', 'to_warehouse', 'created_by')
    order_type = request.GET.get('order_type')
    status = request.GET.get('status')
    warehouse_id = request.GET.get('warehouse')
    supplier_id = request.GET.get('supplier')
    customer_id = request.GET.get('customer')
    if order_type:
        qs = qs.filter(order_type=order_type)
    if status:
        qs = qs.filter(status=status)
    if warehouse_id:
        qs = qs.filter(models.Q(from_warehouse_id=warehouse_id) | models.Q(to_warehouse_id=warehouse_id))
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    qs = qs.order_by('-created_at')
    return render(request, 'inventory/supply_order_list.html', {'orders': qs})

@login_required
def supply_order_detail(request, pk):
    order = get_object_or_404(SupplyOrder, pk=pk)
    items = order.items.select_related('product').all()
    can_execute = order.status == 'pending'
    from .models import StockTransaction
    # جلب الحركات المرتبطة بهذا الطلب
    transactions = StockTransaction.objects.filter(reference=f"SupplyOrder:{order.order_number}")
    # التحقق من الصلاحية
    user_can_execute = request.user.is_superuser or request.user.has_perm('inventory.can_execute_supplyorder')
    if request.method == 'POST' and 'execute_order' in request.POST and can_execute:
        if not user_can_execute:
            messages.error(request, 'ليس لديك صلاحية تنفيذ طلبات التوريد. يرجى التواصل مع مدير النظام.')
            return render(request, 'inventory/supply_order_detail.html', {
    'order': order,
    'items': items,
    'can_execute': can_execute,
    'transactions': transactions,
    'user_can_execute': user_can_execute
})
        # تحقق من توفر الكمية الكافية قبل التنفيذ
        insufficient = []
        for item in items:
            if (order.order_type == 'customer' or order.order_type == 'transfer') and order.from_warehouse:
                # احسب الكمية المتوفرة في المخزن المصدر
                stock = item.product.current_stock_in_warehouse(order.from_warehouse)
                if stock < item.quantity:
                    insufficient.append({'product': item.product, 'required': item.quantity, 'available': stock})
        if insufficient:
            msg = 'لا يمكن تنفيذ الطلب لعدم توفر الكمية الكافية في المخزن لبعض الأصناف:\n'
            for entry in insufficient:
                msg += f"- {entry['product']} (المتوفر: {entry['available']}، المطلوب: {entry['required']})\n"
            messages.error(request, msg)
            return render(request, 'inventory/supply_order_detail.html', {
    'order': order,
    'items': items,
    'can_execute': can_execute,
    'transactions': transactions,
    'user_can_execute': user_can_execute
})
        # تنفيذ الطلب: تغيير الحالة وإنشاء حركات مخزون
        for item in items:
            if order.order_type == 'purchase' and order.to_warehouse:
                StockTransaction.objects.create(
                    product=item.product,
                    transaction_type='in',
                    reason=None,
                    quantity=item.quantity,
                    warehouse=order.to_warehouse,
                    reference=f"SupplyOrder:{order.order_number}",
                    notes='توريد من مورد',
                    created_by=request.user
                )
            elif order.order_type == 'customer' and order.from_warehouse:
                StockTransaction.objects.create(
                    product=item.product,
                    transaction_type='out',
                    reason=None,
                    quantity=item.quantity,
                    warehouse=order.from_warehouse,
                    reference=f"SupplyOrder:{order.order_number}",
                    notes='توريد لعميل',
                    created_by=request.user
                )
            elif order.order_type == 'transfer' and order.from_warehouse and order.to_warehouse:
                # خروج من المخزن المصدر
                StockTransaction.objects.create(
                    product=item.product,
                    transaction_type='out',
                    reason=None,
                    quantity=item.quantity,
                    warehouse=order.from_warehouse,
                    reference=f"SupplyOrder:{order.order_number}",
                    notes='تحويل بين مخازن (خروج)',
                    created_by=request.user
                )
                # دخول للمخزن المستلم
                StockTransaction.objects.create(
                    product=item.product,
                    transaction_type='in',
                    reason=None,
                    quantity=item.quantity,
                    warehouse=order.to_warehouse,
                    reference=f"SupplyOrder:{order.order_number}",
                    notes='تحويل بين مخازن (دخول)',
                    created_by=request.user
                )
        order.status = 'accepted'
        order.save()
        messages.success(request, 'تم تنفيذ طلب التوريد وإنشاء حركات المخزون بنجاح.')
        return redirect('inventory:supply_order_detail', pk=order.pk)
    return render(request, 'inventory/supply_order_detail.html', {
    'order': order,
    'items': items,
    'can_execute': can_execute,
    'transactions': transactions,
    'user_can_execute': user_can_execute
})

@login_required
def supply_order_update(request, pk):
    order = get_object_or_404(SupplyOrder, pk=pk)
    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    customers = Customer.objects.all()
    products = Product.objects.all()
    items = order.items.select_related('product').all()
    if request.method == 'POST':
        order_type = request.POST.get('order_type')
        order_number = request.POST.get('order_number')
        supplier_id = request.POST.get('supplier') or None
        customer_id = request.POST.get('customer') or None
        from_warehouse_id = request.POST.get('from_warehouse') or None
        to_warehouse_id = request.POST.get('to_warehouse') or None
        notes = request.POST.get('notes')
        order.order_type = order_type
        order.order_number = order_number
        order.supplier_id = supplier_id
        order.customer_id = customer_id
        order.from_warehouse_id = from_warehouse_id
        order.to_warehouse_id = to_warehouse_id
        order.notes = notes
        order.save()
        # حذف العناصر القديمة
        order.items.all().delete()
        # إضافة العناصر الجديدة
        for i in range(1, 21):
            product_id = request.POST.get(f'product_{i}')
            quantity = request.POST.get(f'quantity_{i}')
            if product_id and quantity:
                SupplyOrderItem.objects.create(
                    supply_order=order,
                    product_id=product_id,
                    quantity=quantity
                )
        # سجل التدقيق
        log_audit_action(
            user=request.user,
            action='update',
            object_type='SupplyOrder',
            object_id=order.pk,
            description=f'تعديل طلب توريد رقم {order.order_number}'
        )
        messages.success(request, 'تم تحديث طلب التوريد بنجاح.')
        return redirect('inventory:supply_order_detail', pk=order.pk)
    return render(request, 'inventory/supply_order_form.html', {
        'suppliers': suppliers,
        'warehouses': warehouses,
        'customers': customers,
        'products': products,
        'order': order,
        'items': items,
        'is_update': True
    })

@login_required
def supply_order_delete(request, pk):
    order = get_object_or_404(SupplyOrder, pk=pk)
    if request.method == "POST":
        order_number = order.order_number
        order_id = order.pk
        order.delete()
        # سجل التدقيق
        log_audit_action(
            user=request.user,
            action='delete',
            object_type='SupplyOrder',
            object_id=order_id,
            description=f'حذف طلب توريد رقم {order_number}'
        )
        messages.success(request, 'تم حذف طلب التوريد بنجاح.')
        return redirect('inventory:supply_order_list')
    return render(request, 'inventory/supply_order_confirm_delete.html', {'order': order})

@login_required
def supply_order_create(request):
    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    customers = Customer.objects.all()
    products = Product.objects.all()
    if request.method == 'POST':
        order_type = request.POST.get('order_type')
        order_number = request.POST.get('order_number')
        supplier_id = request.POST.get('supplier') or None
        customer_id = request.POST.get('customer') or None
        from_warehouse_id = request.POST.get('from_warehouse') or None
        to_warehouse_id = request.POST.get('to_warehouse') or None
        notes = request.POST.get('notes')
        order = SupplyOrder.objects.create(
            order_type=order_type,
            order_number=order_number,
            supplier_id=supplier_id,
            customer_id=customer_id,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            notes=notes,
            created_by=request.user
        )
        # إضافة العناصر
        for i in range(1, 21):
            product_id = request.POST.get(f'product_{i}')
            quantity = request.POST.get(f'quantity_{i}')
            if product_id and quantity:
                SupplyOrderItem.objects.create(
                    supply_order=order,
                    product_id=product_id,
                    quantity=quantity
                )
        # سجل التدقيق
        log_audit_action(
            user=request.user,
            action='create',
            object_type='SupplyOrder',
            object_id=order.pk,
            description=f'إنشاء طلب توريد رقم {order.order_number}'
        )
        messages.success(request, 'تم إنشاء طلب التوريد بنجاح.')
        return redirect('inventory:supply_order_detail', pk=order.pk)
    return render(request, 'inventory/supply_order_form.html', {
        'suppliers': suppliers,
        'warehouses': warehouses,
        'customers': customers,
        'products': products,
        'is_update': False
    })

@login_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.all()
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_orders')
        if 'bulk_delete' in request.POST:
            if not user_is_inventory_manager(request.user):
                messages.error(request, 'ليس لديك صلاحية للحذف الجماعي.')
                return redirect('inventory:purchase_order_list')
            PurchaseOrder.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'تم حذف {len(selected_ids)} من أوامر الشراء بنجاح.')
            return redirect('inventory:purchase_order_list')
        if 'bulk_export' in request.POST:
            import csv
            from django.http import HttpResponse
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="purchase_orders_export.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'رقم الطلب', 'المورد', 'المخزن', 'تاريخ الإنشاء', 'تاريخ متوقع', 'الحالة'])
            for o in PurchaseOrder.objects.filter(id__in=selected_ids):
                writer.writerow([o.id, o.order_number, o.supplier.name if o.supplier else '', o.warehouse.name if o.warehouse else '', o.created_at, o.expected_date, o.status])
            return response
    return render(request, 'inventory/purchase_order_list.html', {'orders': orders})

@login_required
def purchase_order_create(request):
    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        order_number = request.POST.get('order_number')
        expected_date = request.POST.get('expected_date')
        notes = request.POST.get('notes')
        if not supplier_id or not warehouse_id:
            messages.error(request, 'يجب اختيار مورد ومخزن.')
            return render(request, 'inventory/purchase_order_form.html', {'suppliers': suppliers, 'warehouses': warehouses})
        try:
            supplier_id = int(supplier_id)
            warehouse_id = int(warehouse_id)
        except ValueError:
            messages.error(request, 'يجب إدخال قيمة صحيحة للمورد والمخزن.')
            return render(request, 'inventory/purchase_order_form.html', {'suppliers': suppliers, 'warehouses': warehouses})
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except (Supplier.DoesNotExist, Warehouse.DoesNotExist):
            messages.error(request, 'المورد أو المخزن المحدد غير موجود.')
            return render(request, 'inventory/purchase_order_form.html', {'suppliers': suppliers, 'warehouses': warehouses})
        po = PurchaseOrder.objects.create(
            supplier=supplier, warehouse=warehouse, order_number=order_number,
            expected_date=expected_date, notes=notes, created_by=request.user)
        messages.success(request, 'تم إنشاء طلب الشراء بنجاح.')
        return redirect('inventory:purchase_order_list')
    return render(request, 'inventory/purchase_order_form.html', {'suppliers': suppliers, 'warehouses': warehouses})

@login_required
def purchase_order_update(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لتعديل أوامر الشراء.')
        return redirect('inventory:purchase_order_list')
    order = get_object_or_404(PurchaseOrder, pk=pk)
    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        if not supplier_id or not warehouse_id:
            messages.error(request, 'يجب اختيار مورد ومخزن.')
            return render(request, 'inventory/purchase_order_form.html', {'order': order, 'suppliers': suppliers, 'warehouses': warehouses})
        try:
            order.supplier = Supplier.objects.get(id=supplier_id)
            order.warehouse = Warehouse.objects.get(id=warehouse_id)
        except (Supplier.DoesNotExist, Warehouse.DoesNotExist, ValueError):
            messages.error(request, 'المورد أو المخزن المحدد غير موجود.')
            return render(request, 'inventory/purchase_order_form.html', {'order': order, 'suppliers': suppliers, 'warehouses': warehouses})
        order.order_number = request.POST.get('order_number')
        order.expected_date = request.POST.get('expected_date')
        order.notes = request.POST.get('notes')
        order.save()
        messages.success(request, 'تم تحديث طلب الشراء بنجاح.')
        return redirect('inventory:purchase_order_list')
    return render(request, 'inventory/purchase_order_form.html', {'order': order, 'suppliers': suppliers, 'warehouses': warehouses})

@login_required
def purchase_order_delete(request, pk):
    if not user_is_inventory_manager(request.user):
        messages.error(request, 'ليس لديك صلاحية لحذف أوامر الشراء.')
        return redirect('inventory:purchase_order_list')
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'تم حذف طلب الشراء بنجاح.')
        return redirect('inventory:purchase_order_list')
    return render(request, 'inventory/purchase_order_confirm_delete.html', {'order': order})

# --------------------------
# CustomerOrder CRUD
# --------------------------
from django.forms import modelformset_factory
from django.urls import reverse

@login_required
def customer_order_list(request):
    orders = CustomerOrder.objects.select_related('customer').prefetch_related('items').order_by('-order_date')
    context = {'orders': orders}
    return render(request, 'inventory/customer_order_list.html', context)

from .utils import log_audit_action

@login_required
def customer_order_create(request):
    if request.method == 'POST':
        form = CustomerOrderForm(request.POST)
        formset = CustomerOrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            formset.instance = order
            formset.save()
            # Audit log
            log_audit_action(
                user=request.user,
                action='create',
                object_type='CustomerOrder',
                object_id=order.id,
                description=f'إنشاء طلب عميل رقم {order.order_number}'
            )
            messages.success(request, 'تم إنشاء طلب العميل بنجاح.')
            return redirect('inventory:customer_order_detail', order.id)
    else:
        form = CustomerOrderForm()
        formset = CustomerOrderItemFormSet()
    context = {'form': form, 'formset': formset}
    return render(request, 'inventory/customer_order_form.html', context)

@login_required
def customer_order_update(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    if request.method == 'POST':
        form = CustomerOrderForm(request.POST, instance=order)
        formset = CustomerOrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            # Audit log
            log_audit_action(
                user=request.user,
                action='update',
                object_type='CustomerOrder',
                object_id=order.id,
                description=f'تعديل طلب عميل رقم {order.order_number}'
            )
            messages.success(request, 'تم تحديث الطلب بنجاح.')
            return redirect('inventory:customer_order_detail', order.id)
    else:
        form = CustomerOrderForm(instance=order)
        formset = CustomerOrderItemFormSet(instance=order)
    context = {'form': form, 'formset': formset, 'order': order}
    return render(request, 'inventory/customer_order_form.html', context)

@login_required
def customer_order_detail(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    context = {'order': order}
    return render(request, 'inventory/customer_order_detail.html', context)

@login_required
def customer_order_delete(request, pk):
    order = get_object_or_404(CustomerOrder, pk=pk)
    if request.method == 'POST':
        order_number = order.order_number
        order_id = order.id
        order.delete()
        # Audit log
        log_audit_action(
            user=request.user,
            action='delete',
            object_type='CustomerOrder',
            object_id=order_id,
            description=f'حذف طلب عميل رقم {order_number}'
        )
        messages.success(request, 'تم حذف الطلب بنجاح.')
        return redirect('inventory:customer_order_list')
    context = {'order': order}
    return render(request, 'inventory/confirm_delete.html', context)

# --------------------------
# Main Inventory Home (redirect to dashboard)
# --------------------------
@login_required
def inventory_home(request):
    return redirect('inventory:dashboard')
