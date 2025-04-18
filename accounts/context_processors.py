from .models import Department, CompanyInfo
from .utils import get_user_notifications

def departments(request):
    """
    Context processor to add departments to all templates
    """
    all_departments = Department.objects.filter(is_active=True).order_by('order')
    
    # Get user-accessible departments
    user_departments = []
    if request.user.is_authenticated:
        if request.user.is_superuser:
            user_departments = all_departments
        else:
            user_departments = request.user.departments.filter(is_active=True).order_by('order')
    
    return {
        'all_departments': all_departments,
        'user_departments': user_departments,
    }

def notifications(request):
    """
    Context processor to add notifications to all templates
    """
    unread_notifications = []
    recent_notifications = []
    notifications_count = 0
    
    if request.user.is_authenticated:
        # Get unread notifications for the user
        unread_notifications = get_user_notifications(request.user, unread_only=True, limit=5)
        notifications_count = unread_notifications.count()
        
        # Get recent notifications (both read and unread)
        recent_notifications = get_user_notifications(request.user, unread_only=False, limit=5)
    
    return {
        'unread_notifications': unread_notifications,
        'recent_notifications': recent_notifications,
        'notifications_count': notifications_count,
    }

def company_info(request):
    """
    Context processor to add company information to all templates
    """
    try:
        company_info = CompanyInfo.objects.first()
    except:
        company_info = None
    
    return {
        'company_info': company_info,
    }
