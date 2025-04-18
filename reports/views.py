from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Sum, Count
from datetime import datetime, timedelta

from .models import Report, SavedReport, ReportSchedule
from orders.models import Order, Payment
from factory.models import ProductionOrder
from inventory.models import Product
from customers.models import Customer

class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        return Report.objects.filter(created_by=self.request.user)

class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    template_name = 'reports/report_form.html'
    fields = ['title', 'report_type', 'description', 'parameters']
    success_url = reverse_lazy('reports:report_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إنشاء التقرير بنجاح'))
        return super().form_valid(form)

class ReportUpdateView(LoginRequiredMixin, UpdateView):
    model = Report
    template_name = 'reports/report_form.html'
    fields = ['title', 'report_type', 'description', 'parameters']
    success_url = reverse_lazy('reports:report_list')
    
    def get_queryset(self):
        return Report.objects.filter(created_by=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث التقرير بنجاح'))
        return super().form_valid(form)

class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    template_name = 'reports/report_confirm_delete.html'
    success_url = reverse_lazy('reports:report_list')
    
    def get_queryset(self):
        return Report.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف التقرير بنجاح'))
        return super().delete(request, *args, **kwargs)

class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    
    def get_queryset(self):
        return Report.objects.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Get saved results for this report
        context['saved_results'] = report.saved_results.all()
        
        # Get report data based on type
        if report.report_type == 'sales':
            context['report_data'] = self.generate_sales_report(report)
        elif report.report_type == 'production':
            context['report_data'] = self.generate_production_report(report)
        elif report.report_type == 'inventory':
            context['report_data'] = self.generate_inventory_report(report)
        elif report.report_type == 'financial':
            context['report_data'] = self.generate_financial_report(report)
        
        return context
    
    def generate_sales_report(self, report):
        """Generate sales report data"""
        # Get date range from parameters or default to last 30 days
        date_range = report.parameters.get('date_range', 30)
        start_date = datetime.now() - timedelta(days=date_range)
        
        orders = Order.objects.filter(
            order_date__gte=start_date
        ).select_related('customer')
        
        data = {
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'orders_by_status': orders.values('status').annotate(count=Count('id')).order_by('status'),
            'top_customers': Customer.objects.filter(
                customer_orders__in=orders
            ).annotate(
                total_orders=Count('customer_orders'),
                total_spent=Sum('customer_orders__total_amount')
            ).order_by('-total_spent')[:10]
        }
        return data
    
    def generate_production_report(self, report):
        """Generate production report data"""
        # Get date range from parameters or default to last 30 days
        date_range = report.parameters.get('date_range', 30)
        start_date = datetime.now() - timedelta(days=date_range)
        
        production_orders = ProductionOrder.objects.filter(
            created_at__gte=start_date
        )
        
        data = {
            'total_orders': production_orders.count(),
            'orders_by_status': production_orders.values('status').annotate(count=Count('id')).order_by('status'),
            'orders_by_line': production_orders.values(
                'production_line__name'
            ).annotate(count=Count('id')),
            'quality_issues': production_orders.filter(
                quality_checks__result='failed'
            ).count()
        }
        return data
    
    def generate_inventory_report(self, report):
        """Generate inventory report data"""
        products = Product.objects.all()
        
        # Get all products first
        all_products = list(products)
        
        data = {
            'total_items': len(all_products),
            'total_value': sum(product.current_stock * product.price for product in all_products),
            'low_stock_items': [product for product in all_products if product.needs_restock],
            'out_of_stock_items': [product for product in all_products if product.current_stock == 0],
            'items': all_products
        }
        return data
    
    def generate_financial_report(self, report):
        """Generate financial report data"""
        # Get date range from parameters or default to last 30 days
        date_range = report.parameters.get('date_range', 30)
        start_date = datetime.now() - timedelta(days=date_range)
        
        payments = Payment.objects.filter(payment_date__gte=start_date)
        orders = Order.objects.filter(order_date__gte=start_date)
        
        data = {
            'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'total_payments': payments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'payments_by_method': payments.values('payment_method').annotate(
                count=Count('id'),
                total=Sum('amount')
            ),
            'outstanding_balance': (
                orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            ) - (
                payments.aggregate(Sum('amount'))['amount__sum'] or 0
            )
        }
        return data

def save_report_result(request, pk):
    """Save the current report result"""
    if request.method == 'POST':
        report = get_object_or_404(Report, pk=pk, created_by=request.user)
        name = request.POST.get('name')
        
        # Get the report data
        if report.report_type == 'sales':
            data = ReportDetailView.generate_sales_report(None, report)
        elif report.report_type == 'production':
            data = ReportDetailView.generate_production_report(None, report)
        elif report.report_type == 'inventory':
            data = ReportDetailView.generate_inventory_report(None, report)
        elif report.report_type == 'financial':
            data = ReportDetailView.generate_financial_report(None, report)
        
        # Save the result
        SavedReport.objects.create(
            report=report,
            name=name,
            data=data,
            parameters_used=report.parameters,
            created_by=request.user
        )
        
        messages.success(request, _('تم حفظ نتيجة التقرير بنجاح'))
        return redirect('reports:report_detail', pk=pk)
    
    return redirect('reports:report_list')

class ReportScheduleCreateView(LoginRequiredMixin, CreateView):
    model = ReportSchedule
    template_name = 'reports/report_schedule_form.html'
    fields = ['name', 'frequency', 'parameters', 'recipients']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = get_object_or_404(Report, pk=self.kwargs['pk'])
        context['debug'] = True  # Enable debug information for creation form too
        return context
    
    def form_valid(self, form):
        form.instance.report = get_object_or_404(Report, pk=self.kwargs['pk'])
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إنشاء جدولة التقرير بنجاح'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('reports:report_detail', kwargs={'pk': self.kwargs['pk']})

class ReportScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = ReportSchedule
    template_name = 'reports/report_schedule_form.html'
    fields = ['name', 'frequency', 'parameters', 'recipients', 'is_active']
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object.report
        context['debug'] = True  # Enable debug information
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث جدولة التقرير بنجاح'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('reports:report_detail', kwargs={'pk': self.object.report.pk})

class ReportScheduleDeleteView(LoginRequiredMixin, DeleteView):
    model = ReportSchedule
    template_name = 'reports/report_schedule_confirm_delete.html'
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('تم حذف جدولة التقرير بنجاح'))
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('reports:report_detail', kwargs={'pk': self.object.report.pk})
