from .models import Department, CompanyInfo, SystemSettings
from .utils import get_user_notifications
from django.utils import timezone
from accounts.models import FooterSettings
from django.core.cache import cache

def departments(request):
    """
    Context processor to add departments to all templates in a hierarchical structure
    """
    # Get all active departments
    all_departments = Department.objects.filter(is_active=True).order_by('order')

    # Create hierarchical structure for parent/child departments
    parent_departments = all_departments.filter(parent__isnull=True)

    # Get user-accessible departments
    user_departments = []
    user_parent_departments = []

    if request.user.is_authenticated:
        if request.user.is_superuser:
            user_departments = all_departments
            user_parent_departments = parent_departments
        else:
            user_departments = request.user.departments.filter(is_active=True).order_by('order')
            # Get unique parent departments
            user_parent_ids = set()
            for dept in user_departments:
                if dept.parent:
                    user_parent_ids.add(dept.parent.id)
                else:
                    user_parent_ids.add(dept.id)

            user_parent_departments = Department.objects.filter(id__in=user_parent_ids, is_active=True).order_by('order')

    return {
        'all_departments': all_departments,
        'parent_departments': parent_departments,
        'user_departments': user_departments,
        'user_parent_departments': user_parent_departments,
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
    """توفير معلومات الشركة لجميع القوالب"""
    try:
        company = CompanyInfo.objects.first()
        if not company:
            # إنشاء كائن بقيم افتراضية إذا لم يكن موجوداً
            company = CompanyInfo(
                name="نظام الخواجه",
                address="",
                phone="",
                email="",
            )
            # نحن لا نحفظ الكائن في قاعدة البيانات، لكن نستخدمه فقط لتجنب الأخطاء
    except Exception:
        # في حالة حدوث أي خطأ، إنشاء كائن بقيم افتراضية
        company = CompanyInfo(
            name="نظام الخواجه",
            address="",
            phone="",
            email="",
        )
    return {'company_info': company}

def footer_settings(request):
    """توفير إعدادات التذييل لجميع القوالب"""
    try:
        footer_settings = FooterSettings.objects.first()
        if not footer_settings:
            footer_settings = FooterSettings.objects.create()
    except Exception:
        # في حالة حدوث أي خطأ، إنشاء كائن بقيم افتراضية
        footer_settings = FooterSettings()

    return {
        'footer_settings': footer_settings,
        'current_year': timezone.now().year
    }

def system_settings(request):
    """
    توفير إعدادات النظام لجميع القوالب
    """
    # محاولة الحصول على الإعدادات من الذاكرة المؤقتة
    settings = cache.get('system_settings')

    if not settings:
        try:
            # الحصول على الإعدادات أو إنشاؤها إذا لم تكن موجودة
            settings, created = SystemSettings.objects.get_or_create(pk=1)
            # تخزين في الذاكرة المؤقتة لمدة ساعة
            cache.set('system_settings', settings, 3600)
        except Exception:
            # إرجاع قيم افتراضية في حالة حدوث خطأ
            return {
                'system_settings': None,
                'currency_code': 'SAR',
                'currency_symbol': 'ر.س'
            }

    return {
        'system_settings': settings,
        'currency_code': settings.currency,
        'currency_symbol': settings.CURRENCY_SYMBOLS.get(settings.currency, settings.currency)
    }
