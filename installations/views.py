from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Installation, TransportRequest

class InstallationDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'installations/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        
        # Get all installations for the current user or all if superuser
        if self.request.user.is_superuser:
            installations = Installation.objects.all()
            transports = TransportRequest.objects.all()
        else:
            installations = Installation.objects.filter(team_leader=self.request.user)
            transports = TransportRequest.objects.filter(team_leader=self.request.user)
        
        # Count installations by status
        context['new_installations_count'] = installations.filter(status='new').count()
        context['completed_installations_count'] = installations.filter(status='completed').count()
        context['in_progress_installations_count'] = installations.filter(status='in_progress').count()
        context['overdue_installations_count'] = installations.filter(
            status__in=['new', 'in_progress'],
            scheduled_date__lt=today
        ).count()
        
        # Get transport requests count
        context['transport_requests_count'] = transports.filter(status='pending').count()
        
        # Get recent installations and transports
        context['recent_installations'] = installations.order_by('-created_at')[:10]
        context['recent_transports'] = transports.order_by('-created_at')[:5]
        
        return context

class InstallationListView(LoginRequiredMixin, ListView):
    model = Installation
    template_name = 'installations/installation_list.html'
    context_object_name = 'installations'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Installation.objects.all()
        return Installation.objects.filter(team_leader=self.request.user)

class InstallationCreateView(LoginRequiredMixin, CreateView):
    model = Installation
    template_name = 'installations/installation_form.html'
    fields = ['order', 'customer', 'branch', 'invoice_number', 'status', 'scheduled_date', 'notes']
    success_url = reverse_lazy('installations:dashboard')

    def form_valid(self, form):
        form.instance.team_leader = self.request.user
        if not form.instance.branch and hasattr(self.request.user, 'branch') and self.request.user.branch:
            form.instance.branch = self.request.user.branch
        messages.success(self.request, 'تم إنشاء طلب التركيب بنجاح')
        return super().form_valid(form)

class InstallationDetailView(LoginRequiredMixin, DetailView):
    model = Installation
    template_name = 'installations/installation_detail.html'
    context_object_name = 'installation'

class InstallationUpdateView(LoginRequiredMixin, UpdateView):
    model = Installation
    template_name = 'installations/installation_form.html'
    fields = ['order', 'customer', 'scheduled_date', 'notes', 'status']
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

# Transport Request Views
class TransportListView(LoginRequiredMixin, ListView):
    model = TransportRequest
    template_name = 'installations/transport_list.html'
    context_object_name = 'transports'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            return TransportRequest.objects.all()
        return TransportRequest.objects.filter(team_leader=self.request.user)

class TransportCreateView(LoginRequiredMixin, CreateView):
    model = TransportRequest
    template_name = 'installations/transport_form.html'
    fields = ['customer', 'scheduled_date', 'pickup_address', 'delivery_address', 'items', 'notes']
    success_url = reverse_lazy('installations:dashboard')

    def form_valid(self, form):
        form.instance.team_leader = self.request.user
        messages.success(self.request, 'تم إنشاء طلب النقل بنجاح')
        return super().form_valid(form)

class TransportDetailView(LoginRequiredMixin, DetailView):
    model = TransportRequest
    template_name = 'installations/transport_detail.html'
    context_object_name = 'transport'

class TransportUpdateView(LoginRequiredMixin, UpdateView):
    model = TransportRequest
    template_name = 'installations/transport_form.html'
    fields = ['customer', 'scheduled_date', 'pickup_address', 'delivery_address', 'items', 'notes', 'status']
    success_url = reverse_lazy('installations:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث طلب النقل بنجاح')
        return super().form_valid(form)

class TransportDeleteView(LoginRequiredMixin, DeleteView):
    model = TransportRequest
    template_name = 'installations/transport_confirm_delete.html'
    success_url = reverse_lazy('installations:dashboard')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف طلب النقل بنجاح')
        return super().delete(request, *args, **kwargs)
