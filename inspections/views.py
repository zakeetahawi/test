from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Inspection, InspectionReport, InspectionNotification, InspectionEvaluation
from .forms import InspectionForm, InspectionReportForm, InspectionNotificationForm, InspectionEvaluationForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inspections/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Get all inspections for the current user or all if superuser
        if self.request.user.is_superuser:
            inspections = Inspection.objects.all()
        else:
            inspections = Inspection.objects.filter(
                Q(inspector=self.request.user) | Q(created_by=self.request.user)
            )
        
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
        
        # Get recent inspections
        context['recent_inspections'] = inspections.select_related(
            'customer', 'inspector', 'branch'
        ).order_by('-created_at')[:10]
        
        return context

class InspectionListView(LoginRequiredMixin, ListView):
    model = Inspection
    template_name = 'inspections/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 10

    def get_queryset(self):
        queryset = Inspection.objects.all() if self.request.user.is_superuser else Inspection.objects.filter(
            Q(inspector=self.request.user) | Q(created_by=self.request.user)
        )
        
        status = self.request.GET.get('status')
        overdue = self.request.GET.get('overdue')
        today = timezone.now().date()
        
        if status == 'new':
            queryset = queryset.filter(status='pending', scheduled_date__gt=today)
        elif status == 'in_progress':
            queryset = queryset.filter(status='pending', scheduled_date=today)
        elif status == 'completed':
            queryset = queryset.filter(status='completed')
        elif overdue == '1':
            queryset = queryset.filter(status='pending', scheduled_date__lt=today)
            
        return queryset.select_related('customer', 'inspector', 'branch')

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
        # Allow if user is superuser, created the inspection, or is assigned as inspector
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
        
        # If status is changing to completed, set completed_at
        if new_status == 'completed' and old_status != 'completed':
            inspection.completed_at = timezone.now()
        # If status is changing from completed to something else, clear completed_at
        elif new_status != 'completed' and old_status == 'completed':
            inspection.completed_at = None
            
        messages.success(self.request, 'تم تحديث المعاينة بنجاح')
        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, 'ليس لديك صلاحية لتعديل هذه المعاينة')
        return redirect('inspections:inspection_list')

class InspectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Inspection
    success_url = reverse_lazy('inspections:inspection_list')
    template_name = 'inspections/inspection_confirm_delete.html'

    def test_func(self):
        inspection = self.get_object()
        # Only allow superusers or the creator to delete
        return self.request.user.is_superuser or inspection.created_by == self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المعاينة بنجاح')
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(self.request, 'ليس لديك صلاحية لحذف هذه المعاينة')
        return redirect('inspections:inspection_list')

class EvaluationCreateView(LoginRequiredMixin, CreateView):
    model = InspectionEvaluation
    form_class = InspectionEvaluationForm
    template_name = 'inspections/evaluation_form.html'

    def form_valid(self, form):
        inspection = get_object_or_404(Inspection, pk=self.kwargs['inspection_pk'])
        form.instance.inspection = inspection
        form.instance.created_by = self.request.user
        messages.success(self.request, 'تم إضافة التقييم بنجاح')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('inspections:inspection_detail', kwargs={'pk': self.kwargs['inspection_pk']})

class NotificationListView(LoginRequiredMixin, ListView):
    model = InspectionNotification
    template_name = 'inspections/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        return InspectionNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

class NotificationCreateView(LoginRequiredMixin, CreateView):
    model = InspectionNotification
    form_class = InspectionNotificationForm
    template_name = 'inspections/notification_form.html'

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
