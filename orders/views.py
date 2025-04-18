from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Order, OrderItem, Payment
from .forms import OrderForm, OrderItemFormSet, PaymentForm
from accounts.models import Branch

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
        from inspections.models import Inspection
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
    if request.method == 'POST':
        # Print request.POST for debugging
        print("POST data:", request.POST)
        
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        
        # تحقق من صحة النموذج قبل الحفظ
        if not form.is_valid():
            messages.error(request, 'حدث خطأ في البيانات المدخلة. يرجى مراجعة الحقول المطلوبة.')
            print('Form errors:', form.errors)
            return render(request, 'orders/order_form.html', {'form': form, 'formset': formset, 'title': 'إنشاء طلب جديد'})
        if not formset.is_valid():
            messages.error(request, 'حدث خطأ في تفاصيل المنتجات. يرجى مراجعة البيانات.')
            print('Formset errors:', formset.errors)
            return render(request, 'orders/order_form.html', {'form': form, 'formset': formset, 'title': 'إنشاء طلب جديد'})
        # إذا كان النموذج صالحاً، أكمل الحفظ
        if form.is_valid() and formset.is_valid():
            try:
                # Save order
                order = form.save(commit=False)
                order.created_by = request.user
                print("Creating order for user:", request.user.username)
                
                # Set customer if not provided
                if not order.customer_id and request.POST.get('customer'):
                    from customers.models import Customer
                    try:
                        customer_id = request.POST.get('customer')
                        customer = Customer.objects.get(id=customer_id)
                        order.customer = customer
                    except (Customer.DoesNotExist, ValueError):
                        pass
                
                # Handle delivery options
                delivery_option = request.POST.get('delivery_option')
                if delivery_option == 'home':
                    order.delivery_type = 'home'
                    order.delivery_address = request.POST.get('delivery_address', '')
                elif delivery_option == 'branch':
                    order.delivery_type = 'branch'
                    # Branch is already set in the form
                
                # Set branch to user's branch if not provided
                if not order.branch:
                    order.branch = request.user.branch
                
                # Handle order type field
                order_type = request.POST.get('order_type_hidden', '')
                if order_type:
                    order.order_type = order_type
                else:
                    # Fallback to radio button value
                    order_type = request.POST.get('order_type', '')
                    if order_type:
                        order.order_type = order_type
                
                # Handle service_types field
                if order_type == 'service':
                    service_types = request.POST.get('service_types_hidden', '')
                    if service_types:
                        service_types = [st.strip() for st in service_types.split(',') if st.strip()]
                        order.service_types = service_types
                
                # Set default values for required fields if not provided
                if not order.tracking_status:
                    order.tracking_status = 'pending'
                
                # Set default branch if not provided
                if not order.branch and hasattr(request.user, 'branch'):
                    order.branch = request.user.branch
                
                order.save()
                
                # --- دعم طلب المعاينة فقط بدون منتجات ---
                if order_type == 'inspection':
                    # إنشاء سجل معاينة جديد
                    from inspections.models import Inspection
                    from datetime import date, timedelta
                    inspection = Inspection.objects.create(
                        customer=order.customer,
                        branch=order.branch,
                        request_date=date.today(),
                        scheduled_date=date.today() + timedelta(days=3),
                        status='pending',
                        notes=f'تم إنشاء هذه المعاينة من طلب رقم {order.order_number}',
                        created_by=request.user
                    )
                    # ربط الطلب بالمعاينة (لو فيه حقل مناسب)
                    # order.inspection = inspection
                    # order.save()
                    # إرسال إشعار لقسم المعاينات
                    from accounts.models import Notification, Department
                    dept = Department.objects.filter(code='inspections').first()
                    if dept:
                        Notification.objects.create(
                            title='طلب معاينة جديد',
                            message=f'تم إنشاء طلب معاينة جديد للعميل {order.customer.name} بواسطة {request.user.username} من فرع {order.branch.name if order.branch else "-"}',
                            department=dept,
                            created_by=request.user
                        )
                    # لا داعي لإنشاء منتجات أو formset
                else:
                    # Handle product types
                    product_types = request.POST.get('product_types_hidden', '')
                    if order_type == 'product' and product_types:
                        product_types = [pt.strip() for pt in product_types.split(',') if pt.strip()]
                    
                    # Handle product selection for product orders
                    selected_products_json = request.POST.get('selected_products', '')
                    if selected_products_json:
                        import json
                        try:
                            selected_products = json.loads(selected_products_json)
                            
                            # Create order items for each selected product
                            from inventory.models import Product
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
                                    print(f"Created order item for product {product.name} with quantity {quantity}")
                                except (Product.DoesNotExist, ValueError) as e:
                                    print(f"Error processing product {product_id}: {str(e)}")
                        except json.JSONDecodeError as e:
                            print(f"Error decoding selected products JSON: {str(e)}")
                            print(f"Raw JSON: {selected_products_json}")
                    
                    # Save order items from formset (if any)
                    formset.instance = order
                    formset.save()
                
                # --- نهاية دعم طلب المعاينة فقط ---
                
                # Calculate total amount
                total_amount = sum(item.quantity * item.unit_price for item in order.items.all())
                order.total_amount = total_amount
                order.save()
                
                # Create notifications based on service types
                from accounts.models import Notification, Department
                from datetime import datetime

                # Get sender's department
                sender_department = None
                if hasattr(request.user, 'departments') and request.user.departments.exists():
                    sender_department = request.user.departments.first()

                # Process service types
                if order.order_type == 'service':
                    service_types = order.service_types
                    
                    # Create notifications for each service type
                    for service_type in service_types:
                        if service_type == 'inspection':
                            dept = Department.objects.filter(code='inspections').first()
                            title = 'طلب معاينة جديد'
                            message = f'تم إنشاء طلب معاينة جديد للعميل {order.customer.name}'
                            
                            # Create inspection record
                            try:
                                from inspections.models import Inspection
                                from datetime import date, timedelta
                                
                                # Create a new inspection
                                inspection = Inspection(
                                    customer=order.customer,
                                    branch=order.branch,
                                    request_date=date.today(),
                                    scheduled_date=date.today() + timedelta(days=3),  # Schedule for 3 days later
                                    status='pending',
                                    notes=f'تم إنشاء هذه المعاينة من طلب رقم {order.order_number}',
                                    created_by=request.user
                                )
                                inspection.save()
                                
                                print(f"Created inspection record for order {order.order_number}")
                            except Exception as inspection_error:
                                print(f"Error creating inspection record: {inspection_error}")
                                
                        elif service_type == 'installation':
                            dept = Department.objects.filter(code='installations').first()
                            title = 'طلب تركيب جديد'
                            message = f'تم إنشاء طلب تركيب جديد للعميل {order.customer.name}'
                        elif service_type == 'transport':
                            dept = Department.objects.filter(code='transport').first()
                            title = 'طلب نقل جديد'
                            message = f'تم إنشاء طلب نقل جديد للعميل {order.customer.name}'
                        else:
                            continue
                            
                        if dept:
                            try:
                                Notification.objects.create(
                                    title=title,
                                    message=message,
                                    priority='high',
                                    sender=request.user,
                                    target_department=dept,
                                    target_branch=order.branch,
                                    sender_department=sender_department
                                )
                                # Update last notification date
                                order.last_notification_date = datetime.now()
                                order.save()
                            except Exception as notification_error:
                                print(f"Error creating {service_type} notification: {notification_error}")

                # Process product items
                if order.order_type == 'product' and order.items.exists():
                    # Create notification for inventory department
                    inventory_dept = Department.objects.filter(code='inventory').first()
                    if inventory_dept:
                        try:
                            # Create notification data
                            notification_data = {
                                'title': 'طلب جديد يحتاج للتحقق من المخزون',
                                'message': f'تم إنشاء طلب جديد رقم {order.order_number} ويحتاج للتحقق من توفر المنتجات في المخزون',
                                'priority': 'medium',
                                'sender': request.user,
                                'target_department': inventory_dept,
                                'target_branch': order.branch,
                            }
                            
                            # Add sender department if exists
                            if sender_department:
                                notification_data['sender_department'] = sender_department
                            
                            # Create notification
                            Notification.objects.create(**notification_data)
                            
                            # Update last notification date
                            order.last_notification_date = datetime.now()
                            order.save()
                            
                            # Process items based on type
                            for item in order.items.all():
                                # Set processing status based on item type and order details
                                if item.item_type == 'fabric':
                                    if order.contract_number:
                                        # Send to warehouse then factory
                                        item.processing_status = 'warehouse'
                                    elif order.invoice_number:
                                        # Cut and send to branch
                                        item.processing_status = 'cutting'
                                    else:
                                        item.processing_status = 'pending'
                                elif item.item_type == 'accessory':
                                    # Same logic for accessories
                                    if order.contract_number:
                                        item.processing_status = 'warehouse'
                                    elif order.invoice_number:
                                        item.processing_status = 'cutting'
                                    else:
                                        item.processing_status = 'pending'
                                
                                item.save()
                                
                        except Exception as notification_error:
                            # Log the error but don't prevent order creation
                            print(f"Error creating notification: {notification_error}")
                
                messages.success(request, 'تم إنشاء الطلب بنجاح.')
                print("Redirecting to order detail page:", order.pk)
                return redirect('orders:order_detail', pk=order.pk)
            except Exception as e:
                print("Error saving order:", str(e))
                messages.error(request, f'حدث خطأ أثناء حفظ الطلب: {str(e)}')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
        
        # Set default branch to user's branch
        if not request.user.is_superuser:
            form.fields['branch'].initial = request.user.branch
            form.fields['branch'].queryset = Branch.objects.filter(id=request.user.branch.id)
    
    # Get customer ID from query parameter if available
    customer_id = request.GET.get('customer_id')
    customer = None
    last_order = None
    
    if customer_id:
        from customers.models import Customer
        try:
            customer = Customer.objects.get(id=customer_id)
            # Get the last order for this customer
            last_order = Order.objects.filter(customer=customer).order_by('-created_at').first()
            
            # Set the customer in the form
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
                            from inspections.models import Inspection
                            from datetime import date, timedelta
                            
                            # Create a new inspection
                            inspection = Inspection(
                                customer=order.customer,
                                branch=order.branch,
                                request_date=date.today(),
                                scheduled_date=date.today() + timedelta(days=3),  # Schedule for 3 days later
                                status='pending',
                                notes=f'تم إنشاء هذه المعاينة من طلب رقم {order.order_number}',
                                created_by=request.user
                            )
                            inspection.save()
                            
                            print(f"Created inspection record for updated order {order.order_number}")
                            
                            # Create notification for inspection department
                            from accounts.models import Notification, Department
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
                        from inventory.models import Product
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
            from accounts.models import Notification, Department
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

# Views for accessory items and fabric orders are now integrated into the main Order model
