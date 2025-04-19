from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count
from django.contrib import messages
from customers.models import Customer
from orders.models import Order
from factory.models import ProductionOrder
from inventory.models import Product
import re

from django.http import HttpResponse

def home(request):
    """
    View for the home page
    """
    # Get counts for dashboard
    customers_count = Customer.objects.count()
    orders_count = Order.objects.count()
    production_count = ProductionOrder.objects.count()
    products_count = Product.objects.count()
    
    # Get recent orders
    recent_orders = Order.objects.select_related('customer').order_by('-order_date')[:5]
    
    # Get active production orders
    production_orders = ProductionOrder.objects.select_related(
        'order', 'production_line'
    ).exclude(
        status__in=['completed', 'cancelled']
    ).order_by('estimated_completion')[:5]
    
    # Get low stock products
    low_stock_products = [
        product for product in Product.objects.all()
        if product.needs_restock
    ][:10]
    
    context = {
        'customers_count': customers_count,
        'orders_count': orders_count,
        'production_count': production_count,
        'products_count': products_count,
        'recent_orders': recent_orders,
        'production_orders': production_orders,
        'low_stock_products': low_stock_products,
        'current_year': timezone.now().year,
    }
    
    return render(request, 'home.html', context)


def about(request):
    """
    View for the about page
    """
    context = {
        'title': 'عن النظام',
        'current_year': timezone.now().year,
    }
    return render(request, 'about.html', context)

def contact(request):
    """
    View for the contact page
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if not all([name, email, subject, message]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'يرجى إدخال بريد إلكتروني صحيح.')
        else:
            # Here you would typically send the email
            # For now, we'll just show a success message
            messages.success(request, 'تم إرسال رسالتك بنجاح. سنتواصل معك قريباً.')
            return redirect('contact')
    
    context = {
        'title': 'اتصل بنا',
        'current_year': timezone.now().year,
    }
    return render(request, 'contact.html', context)
