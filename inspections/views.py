from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Inspection, InspectionReport, InspectionNotification, InspectionEvaluation
from .forms import InspectionForm, InspectionReportForm, InspectionNotificationForm, InspectionEvaluationForm

from django.urls import reverse

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inspections/dashboard.html'

    def get_context_data(self, **kwargs):
        from accounts.models import Branch
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        branch_id = self.request.GET.get('branch')
        inspections = Inspection.objects.all()
        if branch_id:
            try:
                branch_id = int(branch_id)
                inspections = inspections.filter(branch_id=branch_id)
                context['selected_branch'] = branch_id
            except (ValueError, TypeError):
                context['selected_branch'] = None
        else:
            context['selected_branch'] = None
        
        # Count inspections by status
        pending_inspections = inspections.filter(status='pending')
        
        context['new_inspections_count'] = pending_inspections.filter(
            scheduled_date__gt=today
        ).count()
        context['completed_inspections_count'] = inspections.filter(
            status='completed'
        ).count()
        context['in_progress_inspections_count'] = pending_inspections.filter(
            scheduled_date=today
        ).count()
        context['overdue_inspections_count'] = pending_inspections.filter(
            scheduled_date__lt=today
        ).count()
        context['branches'] = Branch.objects.all()
        return context

class CompletedInspectionsDetailView(LoginRequiredMixin, ListView):
    model = Inspection
    template_name = 'inspections/completed_details.html'
    context_object_name = 'inspections'
    paginate_by = 20

    def get_queryset(self):
        queryset = Inspection.objects.filter(status='completed')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(inspector=self.request.user) | Q(created_by=self.request.user)
            )
        return queryset.select_related('customer', 'inspector', 'branch')

class CancelledInspectionsDetailView(LoginRequiredMixin, ListView):
    model = Inspection
    template_name = 'inspections/cancelled_details.html'
    context_object_name = 'inspections'
    paginate_by = 20

    def get_queryset(self):
        queryset = Inspection.objects.filter(status='cancelled')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(inspector=self.request.user) | Q(created_by=self.request.user)
            )
        return queryset.select_related('customer', 'inspector', 'branch')

class PendingInspectionsDetailView(LoginRequiredMixin, ListView):
    model = Inspection
    template_name = 'inspections/pending_details.html'
    context_object_name = 'inspections'
    paginate_by = 20

    def get_queryset(self):
        queryset = Inspection.objects.filter(status='pending')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(inspector=self.request.user) | Q(created_by=self.request.user)
            )
        return queryset.select_related('customer', 'inspector', 'branch')

class InspectionListView(LoginRequiredMixin, ListView):
    model = Inspection
    template_name = 'inspections/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 10

    def get_queryset(self):
        queryset = Inspection.objects.all() if self.request.user.is_superuser else Inspection.objects.filter(
            Q(inspector=self.request.user) | Q(created_by=self.request.user)
        )
        
        # Branch filter
        branch_id = self.request.GET.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        # Status and other filters
        status = self.request.GET.get('status')
        from_orders = self.request.GET.get('from_orders')
        today = timezone.now().date()
        
        if status == 'pending' and from_orders == '1':
            queryset = queryset.filter(status='pending', is_from_orders=True)
        elif status:
            queryset = queryset.filter(status=status)

        return queryset.select_related('customer', 'inspector', 'branch')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import Branch
        
        # Get base queryset for stats
        inspections = Inspection.objects.all()
        if not self.request.user.is_superuser:
            inspections = inspections.filter(
                Q(inspector=self.request.user) | Q(created_by=self.request.user)
            )
        
        # Branch filter for stats
        branch_id = self.request.GET.get('branch')
        if branch_id:
            inspections = inspections.filter(branch_id=branch_id)
        
        # Get counts for all inspection types
        context['dashboard'] = {
            'total_inspections': inspections.count(),
            'new_inspections': inspections.filter(status='pending').count(),
            'scheduled_inspections': inspections.filter(status='scheduled').count(),
            'successful_inspections': inspections.filter(status='completed').count(),
            'cancelled_inspections': inspections.filter(status='cancelled').count(),
        }
        
        # Add branches for filter
        context['branches'] = Branch.objects.all()
        return context

class InspectionCreateView(LoginRequiredMixin, CreateView):
    model = Inspection
    form_class = InspectionForm
    template_name = 'inspections/inspection_form.html'
    success_url = reverse_lazy('inspections:inspection_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if not form.instance.inspector:
            form.instance.inspector = self.request.user
        if not form.instance.branch and not self.request.user.is_superuser:
            form.instance.branch = self.request.user.branch
        messages.success(self.request, 'تم إنشاء المعاينة بنجاح')
        return super().form_valid(form)

class InspectionDetailView(LoginRequiredMixin, DetailView):
    model = Inspection
    template_name = 'inspections/inspection_detail.html'
    context_object_name = 'inspection'

    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'inspector', 'branch', 'created_by')

class InspectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Inspection
    form_class = InspectionForm
    template_name = 'inspections/inspection_form.html'
    success_url = reverse_lazy('inspections:inspection_list')

    def test_func(self):
        inspection = self.get_object()
        return (self.request.user.is_superuser or 
                inspection.created_by == self.request.user or 
                inspection.inspector == self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        inspection = form.instance
        old_status = self.get_object().status
        new_status = form.cleaned_data['status']
        
        # Save inspection first to ensure it exists
        response = super().form_valid(form)
        
        # Try to get order if it exists
        try:
            if inspection.order:
                if new_status == 'completed':
                    inspection.order.tracking_status = 'processing'
                elif new_status == 'scheduled':
                    inspection.order.tracking_status = 'processing'
                elif new_status == 'cancelled':
                    inspection.order.tracking_status = 'pending'
                else:  # pending
                    inspection.order.tracking_status = 'pending'
                
                inspection.order.save()
                messages.success(self.request, 'تم تحديث حالة المعاينة والطلب المرتبط')
                return redirect('orders:order_detail', inspection.order.pk)
        except AttributeError:
            # No order associated with this inspection
            pass
        
        # Handle completion status
        if new_status == 'completed' and old_status != 'completed':
            inspection.completed_at = timezone.now()
            inspection.save()
            if not hasattr(inspection, 'evaluation'):
                return redirect('inspections:evaluation_create', inspection_pk=inspection.pk)
        elif new_status != 'completed' and old_status == 'completed':
            inspection.completed_at = None
            inspection.save()
            
        messages.success(self.request, 'تم تحديث حالة المعاينة بنجاح')
        return response

    def handle_no_permission(self):
        messages.error(self.request, 'ليس لديك صلاحية لتعديل هذه المعاينة')
        return redirect('inspections:inspection_list')

class InspectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Inspection
    success_url = reverse_lazy('inspections:inspection_list')
    template_name = 'inspections/inspection_confirm_delete.html'

    def test_func(self):
        inspection = self.get_object()
        return self.request.user.is_superuser or inspection.created_by == self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المعاينة بنجاح')
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(self.request, 'ليس لديك صلاحية لحذف هذه المعاينة')
        return redirect('inspections:inspection_list')

class EvaluationCreateView(LoginRequiredMixin, CreateView):
    form_class = InspectionEvaluationForm
    template_name = 'inspections/evaluation_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def form_valid(self, form):
        inspection = get_object_or_404(Inspection, pk=self.kwargs['inspection_pk'])
        notes = form.cleaned_data.get('notes', '')
        user = self.request.user
        created = 0
        with transaction.atomic():
            for criteria in ['location', 'condition', 'suitability', 'safety', 'accessibility']:
                rating = form.cleaned_data.get(criteria)
                if rating:
                    InspectionEvaluation.objects.create(
                        inspection=inspection,
                        criteria=criteria,
                        rating=rating,
                        notes=notes,
                        created_by=user
                    )
                    created += 1
        if created:
            messages.success(self.request, f'تم إضافة {created} تقييمات للمعاينة بنجاح')
        else:
            messages.warning(self.request, 'لم يتم إضافة أي تقييمات')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('inspections:inspection_detail', kwargs={'pk': self.kwargs['inspection_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inspection'] = get_object_or_404(Inspection, pk=self.kwargs['inspection_pk'])
        return context

class InspectionReportCreateView(LoginRequiredMixin, CreateView):
    model = InspectionReport
    form_class = InspectionReportForm
    template_name = 'inspections/inspection_report_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.object.calculate_statistics()
        messages.success(self.request, 'تم إنشاء تقرير المعاينات بنجاح')
        return response

    def get_success_url(self):
        return reverse('inspections:inspection_list')

class NotificationListView(LoginRequiredMixin, ListView):
    model = InspectionNotification
    template_name = 'inspections/notifications/notification_list.html'  # Updated path
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        return InspectionNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

class NotificationCreateView(LoginRequiredMixin, CreateView):
    model = InspectionNotification
    form_class = InspectionNotificationForm
    template_name = 'inspections/notifications/notification_form.html'  # Updated path

    def form_valid(self, form):
        inspection = get_object_or_404(Inspection, pk=self.kwargs['inspection_pk'])
        form.instance.inspection = inspection
        form.instance.sender = self.request.user
        messages.success(self.request, 'تم إرسال الإشعار بنجاح')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('inspections:inspection_detail', kwargs={'pk': self.kwargs['inspection_pk']})

def mark_notification_read(request, pk):
    notification = get_object_or_404(InspectionNotification, pk=pk)
    if request.user == notification.recipient:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        messages.success(request, 'تم تحديث حالة الإشعار')
    return redirect('inspections:notification_list')
