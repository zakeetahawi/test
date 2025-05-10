from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Installation, InstallationTeam, InstallationStep, InstallationQualityCheck, InstallationIssue

class InstallationDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'installations/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        
        # Get all installations for the current user or all if superuser
        if self.request.user.is_superuser:
            installations = Installation.objects.all()
        else:
            installations = Installation.objects.filter(team__members=self.request.user)
        
        # Count installations by status
        context['pending_installations_count'] = installations.filter(status='pending').count()
        context['completed_installations_count'] = installations.filter(status='completed').count()
        context['in_progress_installations_count'] = installations.filter(status='in_progress').count()
        context['overdue_installations_count'] = installations.filter(
            status__in=['pending', 'in_progress'],
            scheduled_date__lt=today.date()
        ).count()
        
        # Get recent installations and quality checks
        context['recent_installations'] = installations.order_by('-created_at')[:10]
        context['recent_quality_checks'] = InstallationQualityCheck.objects.filter(
            installation__in=installations
        ).order_by('-created_at')[:5]
        
        return context

class InstallationListView(LoginRequiredMixin, ListView):
    model = Installation
    template_name = 'installations/installation_list.html'
    context_object_name = 'installations'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Installation.objects.all()
        return Installation.objects.filter(team__members=self.request.user)

class InstallationCreateView(LoginRequiredMixin, CreateView):
    model = Installation
    template_name = 'installations/installation_form.html'
    fields = ['order', 'inspection', 'team', 'scheduled_date', 'notes']
    success_url = reverse_lazy('installations:dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'تم إنشاء طلب التركيب بنجاح')
        return super().form_valid(form)

class InstallationDetailView(LoginRequiredMixin, DetailView):
    model = Installation
    template_name = 'installations/installation_detail.html'
    context_object_name = 'installation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['steps'] = self.object.steps.all().order_by('order')
        context['quality_checks'] = self.object.quality_checks.all().order_by('-created_at')
        context['issues'] = self.object.issues.all().order_by('-created_at')
        return context

class InstallationUpdateView(LoginRequiredMixin, UpdateView):
    model = Installation
    template_name = 'installations/installation_form.html'
    fields = ['team', 'scheduled_date', 'status', 'quality_rating', 'notes']
    success_url = reverse_lazy('installations:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث طلب التركيب بنجاح')
        return super().form_valid(form)

class InstallationDeleteView(LoginRequiredMixin, DeleteView):
    model = Installation
    template_name = 'installations/installation_confirm_delete.html'
    success_url = reverse_lazy('installations:dashboard')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف طلب التركيب بنجاح')
        return super().delete(request, *args, **kwargs)
