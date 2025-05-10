from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F
from datetime import datetime, timedelta, date
from django.utils import timezone

from .models import Report, SavedReport, ReportSchedule
from orders.models import Order, Payment, OrderItem
from factory.models import ProductionOrder
from inventory.models import Product
from customers.models import Customer

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

class ReportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Get reports accessible by the user
        reports = Report.objects.all()

        # Basic statistics
        context['total_reports'] = reports.count()
        context['recent_reports'] = reports.order_by('-created_at')[:10]
        context['scheduled_reports'] = ReportSchedule.objects.filter(is_active=True).count()

        # Report statistics by type
        report_types = {
            'sales': _('تقارير المبيعات'),
            'inspection': _('تقارير المعاينات'),
            'production': _('تقارير الإنتاج'),
            'inventory': _('تقارير المخزون'),
            'financial': _('تقارير مالية'),
        }
        
        type_counts = {}
        for report_type, label in report_types.items():
            count = reports.filter(report_type=report_type).count()
            type_counts[label] = count
        
        context['report_type_counts'] = type_counts
        
        return context

class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'

    @method_decorator(permission_required('reports.view_report', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        # عرض جميع التقارير للجميع ممن لديهم الصلاحية
        return Report.objects.all()

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
    
    def get_template_names(self):
        """تحديد قالب العرض بناءً على نوع التقرير"""
        report = self.get_object()
        if report.report_type == 'analytics':
            return ['reports/includes/analytics_report_enhanced.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Get saved results for this report
        context['saved_results'] = report.saved_results.all()
        
        # Get initial report data
        context['report_data'] = self.get_initial_report_data(report)
        
        # Add additional context for enhanced analytics
        if report.report_type == 'analytics':
            context.update({
                'date_ranges': [
                    {'value': '7', 'label': 'آخر 7 أيام'},
                    {'value': '30', 'label': 'آخر 30 يوم'},
                    {'value': '90', 'label': 'آخر 3 شهور'},
                    {'value': '180', 'label': 'آخر 6 شهور'},
                    {'value': '365', 'label': 'آخر سنة'},
                ],
                'grouping_options': [
                    {'value': 'day', 'label': 'يومي'},
                    {'value': 'week', 'label': 'أسبوعي'},
                    {'value': 'month', 'label': 'شهري'},
                    {'value': 'quarter', 'label': 'ربع سنوي'},
                ],
                'analysis_types': [
                    {'value': 'trend', 'label': 'تحليل الاتجاه'},
                    {'value': 'comparison', 'label': 'تحليل مقارن'},
                    {'value': 'forecast', 'label': 'التنبؤ'},
                ]
            })
        
        return context
        
    def get_initial_report_data(self, report):
        """جلب البيانات الأولية للتقرير"""
        if report.report_type == 'sales':
            return self.generate_sales_report(report)
        elif report.report_type == 'inspection':
            return self.generate_inspection_report(report)
        elif report.report_type == 'production':
            return self.generate_production_report(report)
        elif report.report_type == 'inventory':
            return self.generate_inventory_report(report)
        elif report.report_type == 'financial':
            return self.generate_financial_report(report)
        elif report.report_type == 'analytics':
            return self.generate_analytics_report(report)
        return None
    
    def generate_inspection_report(self, report):
        """تقرير إحصائي للمعاينات"""
        from inspections.models import Inspection
        date_range = report.parameters.get('date_range', 30)
        start_date = datetime.now() - timedelta(days=date_range)
        inspections = Inspection.objects.filter(request_date__gte=start_date)
        data = {
            'total_inspections': inspections.count(),
            'successful_inspections': inspections.filter(result='passed').count(),
            'pending_inspections': inspections.filter(status='pending').count(),
            'cancelled_inspections': inspections.filter(status='cancelled').count(),
        }
        return data
    
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
                issues__isnull=False
            ).distinct().count()
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

    def generate_analytics_report(self, report):
        """توليد التقرير التحليلي المتقدم"""
        from django.db.models import Avg, StdDev, Count, Case, When, F, Sum, FloatField
        from django.db.models.functions import TruncMonth, ExtractHour, ExtractWeekDay
        
        date_range = report.parameters.get('date_range', 30)
        start_date = timezone.now() - timedelta(days=date_range)
        
        # تحليلات المبيعات المتقدمة
        orders = Order.objects.filter(created_at__gte=start_date)
        monthly_sales = orders.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_sales=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount'),
            sales_growth=F('total_sales') / Window(
                expression=Sum('total_sales'),
                partition_by=[],
                order_by=F('month').asc()
            ) * 100 - 100
        ).order_by('month')

        # تحليل نمط المبيعات اليومي
        daily_patterns = orders.annotate(
            weekday=ExtractWeekDay('created_at')
        ).values('weekday').annotate(
            avg_sales=Avg('total_amount'),
            order_count=Count('id')
        ).order_by('weekday')

        # مؤشرات الأداء الرئيسية
        kpi_data = {
            'sales_growth': orders.aggregate(
                growth=Sum(Case(
                    When(created_at__gte=start_date, then='total_amount'),
                    default=0,
                    output_field=FloatField()
                )) / Sum('total_amount') * 100 - 100
            )['growth'] or 0,
            'customer_retention': self.calculate_customer_retention(start_date),
            'avg_fulfillment_time': self.calculate_avg_fulfillment_time(orders),
            'profit_margin': self.calculate_profit_margin(orders)
        }

        # تحليل سلوك العملاء
        customer_analysis = orders.values('customer').annotate(
            total_spent=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount'),
            last_order_date=Max('created_at')
        ).order_by('-total_spent')

        # تحليل التدفق النقدي
        cash_flow = Payment.objects.filter(
            date__gte=start_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            inflow=Sum(Case(
                When(type='income', then='amount'),
                default=0,
                output_field=FloatField()
            )),
            outflow=Sum(Case(
                When(type='expense', then='amount'),
                default=0,
                output_field=FloatField()
            )),
            net_flow=F('inflow') - F('outflow')
        ).order_by('month')

        return {
            'sales_analysis': {
                'monthly_trends': list(monthly_sales),
                'daily_patterns': list(daily_patterns),
                'total_orders': orders.count(),
                'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
                'avg_order_value': orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
            },
            'kpi_metrics': kpi_data,
            'customer_insights': {
                'top_customers': list(customer_analysis[:10]),
                'customer_segments': self.analyze_customer_segments(customer_analysis),
                'retention_rate': kpi_data['customer_retention']
            },
            'financial_health': {
                'cash_flow': list(cash_flow),
                'profit_margin': kpi_data['profit_margin'],
                'revenue_growth': kpi_data['sales_growth']
            }
        }

    def calculate_fulfillment_rate(self, orders):
        """حساب معدل إكمال الطلبات"""
        if not orders.exists():
            return 0
        completed = orders.filter(status='completed').count()
        return (completed / orders.count()) * 100

    def calculate_inventory_turnover(self):
        """حساب معدل دوران المخزون"""
        from django.db.models import F
        sold_items = OrderItem.objects.filter(
            order__created_at__year=timezone.now().year
        ).aggregate(
            total_sold=Sum(F('quantity') * F('price'))
        )['total_sold'] or 0
        
        avg_inventory = Product.objects.aggregate(
            total_value=Sum(F('current_stock') * F('price'))
        )['total_value'] or 0
        
        if avg_inventory == 0:
            return 0
            
        return round(sold_items / avg_inventory, 2)

    def calculate_customer_retention(self, start_date):
        """حساب معدل الاحتفاظ بالعملاء"""
        from django.db.models.functions import TruncMonth
        
        # حساب العملاء النشطين في الشهر الحالي
        current_customers = Customer.objects.filter(
            customer_orders__created_at__gte=start_date
        ).distinct().count()
        
        # حساب العملاء النشطين في الشهر السابق
        previous_start = start_date - timedelta(days=30)
        previous_customers = Customer.objects.filter(
            customer_orders__created_at__range=[previous_start, start_date]
        ).distinct().count()
        
        if previous_customers == 0:
            return 0
            
        return (current_customers / previous_customers) * 100

    def calculate_avg_fulfillment_time(self, orders):
        """حساب متوسط وقت إتمام الطلبات"""
        completed_orders = orders.filter(
            status='completed',
            completion_date__isnull=False
        ).annotate(
            fulfillment_time=F('completion_date') - F('created_at')
        ).aggregate(
            avg_time=Avg('fulfillment_time')
        )['avg_time']
        
        return completed_orders.total_seconds() / 3600 if completed_orders else 0

    def calculate_profit_margin(self, orders):
        """حساب هامش الربح"""
        total_revenue = orders.aggregate(
            revenue=Sum('total_amount')
        )['revenue'] or 0
        
        # حساب التكاليف
        total_costs = OrderItem.objects.filter(
            order__in=orders
        ).annotate(
            item_cost=F('quantity') * F('product__cost_price')
        ).aggregate(
            total=Sum('item_cost')
        )['total'] or 0
        
        if total_revenue == 0:
            return 0
            
        return ((total_revenue - total_costs) / total_revenue) * 100

    def analyze_customer_segments(self, customer_analysis):
        """تحليل شرائح العملاء"""
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        
        if not customer_analysis:
            return []
            
        # تحضير البيانات للتحليل
        data = np.array([[c['total_spent'], c['order_count']] for c in customer_analysis])
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        
        # تقسيم العملاء إلى شرائح
        segments = {
            'vip': [],
            'regular': [],
            'occasional': []
        }
        
        for i, customer in enumerate(customer_analysis):
            score = scaled_data[i].mean()
            if score > 0.5:
                segments['vip'].append(customer)
            elif score > -0.5:
                segments['regular'].append(customer)
            else:
                segments['occasional'].append(customer)
        
        return {
            'segments': segments,
            'summary': {
                'vip_count': len(segments['vip']),
                'regular_count': len(segments['regular']),
                'occasional_count': len(segments['occasional'])
            }
        }

def save_report_result(request, pk):
    """Save the current report result"""
    if request.method == 'POST':
        report = get_object_or_404(Report, pk=pk, created_by=request.user)
        name = request.POST.get('name')
        
        # Get the report data
        if report.report_type == 'sales':
            data = ReportDetailView.generate_sales_report(None, report)
        elif report.report_type == 'inspection':
            data = ReportDetailView.generate_inspection_report(None, report)
        
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
