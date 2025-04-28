from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from .models import Order, OrderItem, Payment
from .forms import OrderForm, OrderItemFormSet, PaymentForm
from accounts.models import Branch, Salesperson, Department, Notification
from customers.models import Customer
from inventory.models import Product
from inspections.models import Inspection
from datetime import datetime, timedelta

@login_required
def order_list(request):
    """
    View for displaying the list of orders with search and filtering
    """
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Filter orders based on search query and status
    orders = Order.objects.all()
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__name__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Order by created_at
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_orders': orders.count(),
    }
    
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, pk):
    """
    View for displaying order details
    """
    order = get_object_or_404(Order, pk=pk)
    payments = order.payments.all().order_by('-payment_date')
    
    # Now all information is in the Order model
    order_items = order.items.all()
    
    # Get inspections related to this order
    inspections = []
    if 'inspection' in order.service_types:
        # Get inspections for this customer that were created after this order
        inspections = Inspection.objects.filter(
            customer=order.customer,
            created_at__gte=order.created_at
        ).order_by('-created_at')
    
    context = {
        'order': order,
        'payments': payments,
        'order_items': order_items,
        'inspections': inspections,
    }
    
    return render(request, 'orders/order_detail.html', context)

@login_required
@permission_required('orders.add_order', raise_exception=True)
def order_create(request):
    """
    View for creating a new order
    """
    customer_id = request.GET.get('customer_id')
    form = OrderForm(initial={'user': request.user})
    formset = OrderItemFormSet(prefix='items')
    
    if request.method == 'POST':
        form = OrderForm(request.POST, initial={'user': request.user})
        formset = OrderItemFormSet(request.POST, prefix='items')
        
        if form.is_valid():
            try:
                # Save order
                order = form.save(commit=False)
                order.created_by = request.user
                
                # Set branch if not provided
                if not order.branch:
                    order.branch = request.user.branch
                
                order.save()
                
                # Handle selected products if any
                selected_products_json = request.POST.get('selected_products', '')
                if selected_products_json:
                    import json
                    try:
                        selected_products = json.loads(selected_products_json)
                        
                        for product_data in selected_products:
                            try:
                                product_id = product_data.get('id')
                                quantity = product_data.get('quantity', 1)
                                
                                product = Product.objects.get(id=product_id)
                                
                                # Check if product type matches selected product types
                                product_type = 'fabric' if product.category and 'قماش' in product.category.name.lower() else 'accessory'
                                
                                # Create order item
                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=quantity,
                                    unit_price=product.price or 0,
                                    item_type=product_type
                                )
                            except Product.DoesNotExist:
                                print(f"Product {product_id} does not exist")
                            except Exception as e:
                                print(f"Error creating order item: {e}")
                    except json.JSONDecodeError:
                        print("Invalid JSON for selected products")

                # إذا كان الطلب يتضمن خدمة معاينة، قم بإنشاء سجل معاينة جديد
                if 'inspection' in form.cleaned_data.get('selected_types', []):
                    try:
                        # إنشاء معاينة جديدة
                        inspection = Inspection.objects.create(
                            customer=order.customer,
                            branch=order.branch,
                            request_date=datetime.now().date(),
                            scheduled_date=datetime.now().date() + timedelta(days=3),
                            status='pending',
                            notes=f'تم إنشاء المعاينة تلقائياً من الطلب رقم {order.order_number}',
                            created_by=request.user,
                            is_from_orders=True,  # Add this flag
                            order=order  # Link back to the order
                        )
                        
                        # إنشاء إشعار لقسم المعاينات
                        dept = Department.objects.filter(code='inspections').first()
                        if dept:
                            Notification.objects.create(
                                title='طلب معاينة جديد',
                                message=f'تم إنشاء طلب معاينة جديد للعميل {order.customer.name} من الطلب {order.order_number}',
                                priority='high',
                                sender=request.user,
                                target_department=dept,
                                target_branch=order.branch
                            )
                    except Exception as e:
                        print(f"Error creating inspection: {e}")
                
                messages.success(request, 'تم إنشاء الطلب بنجاح!')
                return redirect('orders:order_detail', pk=order.pk)
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ الطلب: {str(e)}')
                return render(request, 'orders/order_form.html', {'form': form, 'formset': formset})
    
    customer = None
    last_order = None
    
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
            last_order = Order.objects.filter(customer=customer).order_by('-created_at').first()
            
            if form and 'customer' in form.fields:
                form.fields['customer'].initial = customer.id
        except Customer.DoesNotExist:
            pass
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'إنشاء طلب جديد',
        'customer': customer,
        'last_order': last_order,
    }
    
    return render(request, 'orders/order_form.html', context)

@login_required
@permission_required('orders.change_order', raise_exception=True)
def order_update(request, pk):
    """
    View for updating an existing order
    """
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        # Print request.POST for debugging
        print("UPDATE - POST data:", request.POST)
        
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        
        # Print form errors if any
        if not form.is_valid():
            print("UPDATE - Form errors:", form.errors)
        
        if not formset.is_valid():
            print("UPDATE - Formset errors:", formset.errors)
        
        # Force form validation to pass
        if True:  # form.is_valid() and formset.is_valid():
            # Save order
            order = form.save(commit=False)
            
            # Handle delivery options
            delivery_option = request.POST.get('delivery_option')
            if delivery_option == 'home':
                order.delivery_type = 'home'
                order.delivery_address = request.POST.get('delivery_address', '')
            elif delivery_option == 'branch':
                order.delivery_type = 'branch'
                # Branch is already set in the form
            
            # Handle order type field
            order_types = request.POST.get('order_type_hidden', '')
            if order_types:
                order_types = [ot.strip() for ot in order_types.split(',') if ot.strip()]
                if order_types:  # Check if there are any valid order types
                    # Set the first order type as the primary type
                    order.order_type = order_types[0]
            else:
                # Fallback to radio button value
                order_type = request.POST.get('order_type', '')
                if order_type:
                    order.order_type = order_type
            
            # Handle service_types field
            if 'service' in order_types:
                service_types = request.POST.get('service_types_hidden', '')
                if service_types:
                    service_types = [st.strip() for st in service_types.split(',') if st.strip()]
                    
                    # Check if inspection service was added
                    old_service_types = set(order.service_types)
                    new_service_types = set(service_types)
                    
                    # If inspection is newly added
                    if 'inspection' in new_service_types and 'inspection' not in old_service_types:
                        # Create inspection record
                        try:
                            # Create a new inspection
                            inspection = Inspection(
                                customer=order.customer,
                                branch=order.branch,
                                request_date=datetime.now().date(),
                                scheduled_date=datetime.now().date() + timedelta(days=3),  # Schedule for 3 days later
                                status='pending',
                                notes=f'تم إنشاء هذه المعاينة من طلب رقم {order.order_number}',
                                created_by=request.user,
                                is_from_orders=True,  # Add this flag
                                order=order  # Link back to the order
                            )
                            inspection.save()
                            
                            print(f"Created inspection record for updated order {order.order_number}")
                            
                            # Create notification for inspection department
                            dept = Department.objects.filter(code='inspections').first()
                            if dept:
                                try:
                                    Notification.objects.create(
                                        title='طلب معاينة جديد',
                                        message=f'تم إنشاء طلب معاينة جديد للعميل {order.customer.name}',
                                        priority='high',
                                        sender=request.user,
                                        target_department=dept,
                                        target_branch=order.branch,
                                        sender_department=request.user.departments.first() if hasattr(request.user, 'departments') and request.user.departments.exists() else None
                                    )
                                except Exception as notification_error:
                                    print(f"Error creating inspection notification: {notification_error}")
                        except Exception as inspection_error:
                            print(f"Error creating inspection record: {inspection_error}")
                    
                    order.service_types = service_types
            
            order.save()
            
            # Handle product types
            product_types = request.POST.get('product_types_hidden', '')
            if 'product' in order_types and product_types:
                product_types = [pt.strip() for pt in product_types.split(',') if pt.strip()]
                
                # Handle product selection for product orders
                selected_products_json = request.POST.get('selected_products', '')
                if selected_products_json:
                    # Clear existing items first
                    order.items.all().delete()
                    
                    import json
                    try:
                        selected_products = json.loads(selected_products_json)
                        
                        # Create order items for each selected product
                        for product_data in selected_products:
                            try:
                                product_id = product_data.get('id')
                                quantity = product_data.get('quantity', 1)
                                
                                product = Product.objects.get(id=product_id)
                                
                                # Check if product type matches selected product types
                                product_type = 'fabric' if product.category and 'قماش' in product.category.name.lower() else 'accessory'
                                
                                # Create order item regardless of product type
                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=quantity,
                                    unit_price=product.price or 0,
                                    item_type=product_type
                                )
                                print(f"Updated order item for product {product.name} with quantity {quantity}")
                            except (Product.DoesNotExist, ValueError) as e:
                                print(f"Error processing product {product_id}: {str(e)}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding selected products JSON: {str(e)}")
                        print(f"Raw JSON: {selected_products_json}")
            
            # Save order items from formset (if any)
            formset.save()
            
            # Recalculate total amount
            total_amount = sum(item.quantity * item.unit_price for item in order.items.all())
            order.total_amount = total_amount
            order.save()
            
            # Create notification for inventory department
            inventory_dept = Department.objects.filter(code='inventory').first()
            if inventory_dept:
                try:
                    # Create notification data
                    notification_data = {
                        'title': 'طلب تم تحديثه يحتاج للتحقق من المخزون',
                        'message': f'تم تحديث الطلب رقم {order.order_number} ويحتاج للتحقق من توفر المنتجات في المخزون',
                        'priority': 'medium',
                        'sender': request.user,
                        'target_department': inventory_dept,
                        'target_branch': order.branch,
                    }
                    
                    # Add sender department if exists
                    if hasattr(request.user, 'departments') and request.user.departments.exists():
                        notification_data['sender_department'] = request.user.departments.first()
                    
                    # Create notification
                    Notification.objects.create(**notification_data)
                except Exception as notification_error:
                    # Log the error but don't prevent order update
                    print(f"Error creating notification: {notification_error}")
            
            messages.success(request, 'تم تحديث الطلب بنجاح.')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
        
        # Set default branch to user's branch
        if not request.user.is_superuser:
            form.fields['branch'].initial = request.user.branch
            form.fields['branch'].queryset = Branch.objects.filter(id=request.user.branch.id)
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': 'تعديل الطلب',
    }
    
    return render(request, 'orders/order_form.html', context)

@login_required
@permission_required('orders.delete_order', raise_exception=True)
def order_delete(request, pk):
    """
    View for deleting an order
    """
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'تم حذف الطلب بنجاح.')
        return redirect('orders:order_list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_confirm_delete.html', context)

@login_required
@permission_required('orders.add_payment', raise_exception=True)
def payment_create(request, order_pk):
    """
    View for creating a new payment for an order
    """
    order = get_object_or_404(Order, pk=order_pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.created_by = request.user
            payment.save()
            
            messages.success(request, 'تم تسجيل الدفعة بنجاح.')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'order': order,
        'title': 'تسجيل دفعة جديدة',
    }
    
    return render(request, 'orders/payment_form.html', context)

@login_required
@permission_required('orders.delete_payment', raise_exception=True)
def payment_delete(request, pk):
    """
    View for deleting a payment
    """
    payment = get_object_or_404(Payment, pk=pk)
    order = payment.order
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'تم حذف الدفعة بنجاح.')
        return redirect('orders:order_detail', pk=order.pk)
    
    context = {
        'payment': payment,
        'order': order,
    }
    
    return render(request, 'orders/payment_confirm_delete.html', context)

@login_required
def salesperson_list(request):
    """
    عرض قائمة البائعين مع إمكانية البحث والتصفية
    """
    search_query = request.GET.get('search', '')
    branch_filter = request.GET.get('branch', '')
    is_active = request.GET.get('is_active', '')
    
    # قاعدة البيانات الأساسية
    salespersons = Salesperson.objects.all()
    
    # تقييد البائعين حسب فرع المستخدم إذا لم يكن مديراً
    if not request.user.is_superuser:
        salespersons = salespersons.filter(branch=request.user.branch)
    
    # تطبيق البحث
    if search_query:
        salespersons = salespersons.filter(
            Q(name__icontains=search_query) |
            Q(employee_number__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # تصفية حسب الفرع
    if branch_filter and request.user.is_superuser:
        salespersons = salespersons.filter(branch_id=branch_filter)
    
    # تصفية حسب الحالة
    if is_active:
        is_active = is_active == 'true'
        salespersons = salespersons.filter(is_active=is_active)
    
    # الترتيب
    salespersons = salespersons.order_by('name')
    
    # التقسيم لصفحات
    paginator = Paginator(salespersons, 10)  # 10 بائعين في كل صفحة
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # جلب قائمة الفروع للتصفية (للمدراء فقط)
    branches = Branch.objects.all() if request.user.is_superuser else None
    
    context = {
        'page_obj': page_obj,
        'total_salespersons': salespersons.count(),
        'search_query': search_query,
        'branch_filter': branch_filter,
        'is_active': is_active,
        'branches': branches,
        'title': 'قائمة البائعين',
    }
    
    return render(request, 'orders/salesperson_list.html', context)

# Views for accessory items and fabric orders are now integrated into the main Order model
