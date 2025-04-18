from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

from .models import Notification, CompanyInfo, FormField
from .utils import get_user_notifications
from .forms import CompanyInfoForm, FormFieldForm

def login_view(request):
    """
    View for user login
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'مرحباً بك {username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
                # Add CSS classes to form fields
                form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'اسم المستخدم'})
                form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'كلمة المرور'})
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
            # Add CSS classes to form fields
            form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'اسم المستخدم'})
            form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'كلمة المرور'})
    else:
        form = AuthenticationForm()
        # Add CSS classes to form fields
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'اسم المستخدم'})
        form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'كلمة المرور'})
    
    context = {
        'form': form,
        'title': 'تسجيل الدخول',
    }
    
    return render(request, 'accounts/login.html', context)

def logout_view(request):
    """
    View for user logout
    """
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('home')

@login_required
def profile_view(request):
    """
    View for user profile
    """
    context = {
        'user': request.user,
        'title': 'الملف الشخصي',
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def notifications_list(request):
    """
    View for listing all notifications
    """
    # Get filter parameters
    filter_type = request.GET.get('filter', 'all')
    
    # Get all notifications for the user
    all_notifications = get_user_notifications(request.user)
    
    # Filter notifications based on read status
    if filter_type == 'unread':
        notifications = all_notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = all_notifications.filter(is_read=True)
    else:  # 'all'
        notifications = all_notifications
    
    # Paginate notifications
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'title': 'الإشعارات',
    }
    return render(request, 'accounts/notifications.html', context)

@login_required
def notification_detail(request, notification_id):
    """
    View for notification detail
    """
    # Get notification
    notification = get_object_or_404(Notification, id=notification_id)
    
    # Check if user has access to this notification
    user_notifications = get_user_notifications(request.user)
    if notification not in user_notifications:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذا الإشعار.')
        return redirect('accounts:notifications')
    
    # Mark notification as read
    if not notification.is_read:
        notification.mark_as_read(request.user)
    
    context = {
        'notification': notification,
        'title': notification.title,
    }
    return render(request, 'accounts/notification_detail.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """
    View for marking notification as read
    """
    if request.method == 'POST':
        # Get notification
        notification = get_object_or_404(Notification, id=notification_id)
        
        # Check if user has access to this notification
        user_notifications = get_user_notifications(request.user)
        if notification not in user_notifications:
            return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية للوصول إلى هذا الإشعار.'})
        
        # Mark notification as read
        notification.mark_as_read(request.user)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'طريقة غير صالحة.'})

@login_required
def mark_all_notifications_read(request):
    """
    View for marking all notifications as read
    """
    if request.method == 'POST':
        # Get all unread notifications for the user
        unread_notifications = get_user_notifications(request.user, unread_only=True)
        
        # Mark all as read
        for notification in unread_notifications:
            notification.mark_as_read(request.user)
        
        return JsonResponse({'success': True, 'count': unread_notifications.count()})
    
    return JsonResponse({'success': False, 'message': 'طريقة غير صالحة.'})

@login_required
def company_info_view(request):
    try:
        if not request.user.is_superuser:
            messages.error(request, 'هذه الصفحة متاحة فقط لمديري النظام.')
            return redirect('home')
        """
        View for managing company information
        """
        # Get or create company info
        company, created = CompanyInfo.objects.get_or_create(
            defaults={
                'name': 'شركة الخواجه',
                'address': 'العنوان',
                'phone': '01234567890',
                'email': 'info@example.com',
            }
        )
        
        if request.method == 'POST':
            form = CompanyInfoForm(request.POST, request.FILES, instance=company)
            if form.is_valid():
                form.save()
                messages.success(request, 'تم تحديث معلومات الشركة بنجاح.')
                return redirect('accounts:company_info')
        else:
            form = CompanyInfoForm(instance=company)
        
        context = {
            'form': form,
            'company': company,
            'title': 'معلومات الشركة',
        }
        
        return render(request, 'accounts/company_info.html', context)
    except Exception as e:
        import traceback
        print("[CompanyInfo Error]", e)
        traceback.print_exc()
        messages.error(request, 'حدث خطأ غير متوقع أثناء معالجة معلومات الشركة. يرجى مراجعة الدعم الفني.')
        return redirect('home')

@staff_member_required
def form_field_list(request):
    """
    View for listing form fields
    """
    form_type = request.GET.get('form_type', '')
    
    # Filter form fields
    if form_type:
        form_fields = FormField.objects.filter(form_type=form_type)
    else:
        form_fields = FormField.objects.all()
    
    # Paginate form fields
    paginator = Paginator(form_fields, 10)  # Show 10 form fields per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form_type': form_type,
        'form_types': dict(FormField.FORM_CHOICES),
        'title': 'إدارة حقول النماذج',
    }
    
    return render(request, 'accounts/form_field_list.html', context)

@staff_member_required
def form_field_create(request):
    """
    View for creating a new form field
    """
    if request.method == 'POST':
        form = FormFieldForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الحقل بنجاح.')
            return redirect('accounts:form_field_list')
    else:
        # Pre-fill form type if provided in GET parameters
        form_type = request.GET.get('form_type', '')
        form = FormFieldForm(initial={'form_type': form_type})
    
    context = {
        'form': form,
        'title': 'إضافة حقل جديد',
    }
    
    return render(request, 'accounts/form_field_form.html', context)

@staff_member_required
def form_field_update(request, pk):
    """
    View for updating a form field
    """
    form_field = get_object_or_404(FormField, pk=pk)
    
    if request.method == 'POST':
        form = FormFieldForm(request.POST, instance=form_field)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الحقل بنجاح.')
            return redirect('accounts:form_field_list')
    else:
        form = FormFieldForm(instance=form_field)
    
    context = {
        'form': form,
        'form_field': form_field,
        'title': 'تعديل الحقل',
    }
    
    return render(request, 'accounts/form_field_form.html', context)

@staff_member_required
def form_field_delete(request, pk):
    """
    View for deleting a form field
    """
    form_field = get_object_or_404(FormField, pk=pk)
    
    if request.method == 'POST':
        form_field.delete()
        messages.success(request, 'تم حذف الحقل بنجاح.')
        return redirect('accounts:form_field_list')
    
    context = {
        'form_field': form_field,
        'title': 'حذف الحقل',
    }
    
    return render(request, 'accounts/form_field_confirm_delete.html', context)

@staff_member_required
def toggle_form_field(request, pk):
    """
    View for toggling a form field's enabled status via AJAX
    """
    if request.method == 'POST':
        form_field = get_object_or_404(FormField, pk=pk)
        form_field.enabled = not form_field.enabled
        form_field.save()
        
        return JsonResponse({
            'success': True, 
            'enabled': form_field.enabled,
            'field_id': form_field.id
        })
    
    return JsonResponse({'success': False, 'message': 'طريقة غير صالحة.'})
