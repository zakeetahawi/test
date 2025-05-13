from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Order, OrderItem, Payment, ShippingDetails
from .forms import OrderForm, OrderItemFormSet, PaymentForm
from .services import ShippingService
from accounts.models import Branch, Salesperson, Department, Notification
from customers.models import Customer
from inventory.models import Product
from inspections.models import Inspection
from datetime import datetime, timedelta

class OrdersDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Get orders
        if self.request.user.is_superuser:
            orders = Order.objects.all()
        else:
            orders = Order.objects.filter(Q(created_by=self.request.user) | Q(salesperson=self.request.user))

        # Basic statistics
        context['total_orders'] = orders.count()
        context['pending_orders'] = orders.filter(status='pending').count()
        context['completed_orders'] = orders.filter(status='completed').count()
        context['recent_orders'] = orders.order_by('-created_at')[:10]

        # Sales statistics
        context['total_sales'] = orders.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['monthly_sales'] = orders.filter(created_at__month=today.month).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        return context

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
                    order.service_types = service_types

            order.save()

            # Save order items
            formset.save()

            messages.success(request, 'تم تحديث الطلب بنجاح!')
            return redirect('orders:order_detail', pk=order.pk)

    form = OrderForm(instance=order)
    formset = OrderItemFormSet(instance=order)

    context = {
        'form': form,
        'formset': formset,
        'title': f'تحديث الطلب: {order.order_number}',
        'order': order,
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
        try:
            order.delete()
            messages.success(request, 'تم حذف الطلب بنجاح.')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الطلب: {str(e)}')
        return redirect('orders:order_list')

    context = {
        'order': order,
        'title': f'حذف الطلب: {order.order_number}',
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
        'title': f'تسجيل دفعة جديدة للطلب: {order.order_number}'
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
        try:
            payment.delete()
            messages.success(request, 'تم حذف الدفعة بنجاح.')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الدفعة: {str(e)}')
        return redirect('orders:order_detail', pk=order.pk)

    context = {
        'payment': payment,
        'order': order,
        'title': f'حذف دفعة من الطلب: {order.order_number}'
    }

    return render(request, 'orders/payment_confirm_delete.html', context)

@login_required
def salesperson_list(request):
    """
    View for listing salespersons and their orders
    """
    salespersons = Salesperson.objects.all()

    # Add order statistics for each salesperson
    for sp in salespersons:
        sp.total_orders = Order.objects.filter(salesperson=sp).count()
        sp.completed_orders = Order.objects.filter(salesperson=sp, status='completed').count()
        sp.pending_orders = Order.objects.filter(salesperson=sp, status='pending').count()
        sp.total_sales = Order.objects.filter(salesperson=sp, status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'salespersons': salespersons,
        'title': 'قائمة مندوبي المبيعات'
    }

    return render(request, 'orders/salesperson_list.html', context)

@login_required
@permission_required('orders.change_order', raise_exception=True)
def update_order_status(request, order_id):
    """
    View for updating order status
    """
    order = get_object_or_404(Order, pk=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Order.STATUS_CHOICES).keys():
            try:
                order.status = new_status
                order.save()
                messages.success(request, 'تم تحديث حالة الطلب بنجاح.')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء تحديث حالة الطلب: {str(e)}')
        else:
            messages.error(request, 'حالة الطلب غير صالحة.')

    return redirect('orders:order_detail', pk=order_id)

@login_required
@permission_required('orders.change_order', raise_exception=True)
def shipping_details(request, order_id):
    """
    عرض تفاصيل الشحن للطلب
    """
    order = get_object_or_404(Order, pk=order_id)

    # التحقق من وجود تفاصيل شحن
    try:
        shipping = order.shipping_details
    except ShippingDetails.DoesNotExist:
        if order.delivery_type != 'home':
            messages.error(request, 'هذا الطلب ليس للتوصيل المنزلي')
            return redirect('orders:order_detail', pk=order_id)

        # إنشاء تفاصيل شحن جديدة
        shipping = ShippingService.create_shipping_details(order)

    # الحصول على الجدول الزمني للشحن
    timeline = ShippingService.get_shipping_timeline(order)

    context = {
        'order': order,
        'shipping': shipping,
        'timeline': timeline,
        'shipping_status_choices': ShippingDetails.SHIPPING_STATUS_CHOICES,
        'shipping_provider_choices': ShippingDetails.SHIPPING_PROVIDER_CHOICES,
    }

    return render(request, 'orders/shipping_details.html', context)

@login_required
@permission_required('orders.change_order', raise_exception=True)
def update_shipping_status(request, order_id):
    """
    تحديث حالة الشحن
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'يجب استخدام طريقة POST'}, status=400)

    order = get_object_or_404(Order, pk=order_id)
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    try:
        # تحديث حالة الشحن
        shipping = ShippingService.update_shipping_status(
            order,
            new_status,
            notes=notes,
            tracking_number=request.POST.get('tracking_number'),
            estimated_delivery_date=request.POST.get('estimated_delivery_date'),
            shipping_cost=request.POST.get('shipping_cost')
        )

        messages.success(request, 'تم تحديث حالة الشحن بنجاح')
        return JsonResponse({
            'success': True,
            'shipping_status': shipping.get_shipping_status_display(),
            'last_update': shipping.last_update.strftime('%Y-%m-%d %H:%M:%S')
        })

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'حدث خطأ: {str(e)}'}, status=500)

@login_required
@permission_required('orders.change_order', raise_exception=True)
def update_shipping_provider(request, order_id):
    """
    تحديث شركة الشحن
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'يجب استخدام طريقة POST'}, status=400)

    order = get_object_or_404(Order, pk=order_id)
    provider = request.POST.get('provider')

    try:
        # التحقق من صلاحية شركة الشحن
        ShippingService.validate_shipping_provider(provider)

        # تحديث شركة الشحن
        shipping = order.shipping_details
        shipping.shipping_provider = provider
        shipping.save()

        # حساب تكلفة الشحن الجديدة
        new_cost = ShippingService.get_shipping_cost(order, provider)
        shipping.shipping_cost = new_cost
        shipping.save()

        messages.success(request, 'تم تحديث شركة الشحن بنجاح')
        return JsonResponse({
            'success': True,
            'shipping_provider': shipping.get_shipping_provider_display(),
            'shipping_cost': float(shipping.shipping_cost)
        })

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'حدث خطأ: {str(e)}'}, status=500)

@login_required
def shipping_timeline(request, order_id):
    """
    عرض الجدول الزمني للشحن
    """
    order = get_object_or_404(Order, pk=order_id)
    timeline = ShippingService.get_shipping_timeline(order)

    return JsonResponse({
        'success': True,
        'timeline': timeline
    })
