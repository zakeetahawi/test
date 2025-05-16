"""
تعريف الأقسام الأساسية للنظام
"""
from django.utils.translation import gettext_lazy as _

# قائمة الأقسام الرئيسية
CORE_DEPARTMENTS = [
    {
        'name': 'العملاء',
        'code': 'customers',
        'url_name': 'customers:customer_list',
        'department_type': 'department',
        'icon': 'fas fa-users',
        'order': 10,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'الطلبات',
        'code': 'orders',
        'url_name': 'orders:order_list',
        'department_type': 'department',
        'icon': 'fas fa-shopping-cart',
        'order': 20,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'المخزون',
        'code': 'inventory',
        'url_name': 'inventory:dashboard',
        'department_type': 'department',
        'icon': 'fas fa-boxes',
        'order': 30,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'المعاينات',
        'code': 'inspections',
        'url_name': 'inspections:inspection_list',
        'department_type': 'department',
        'icon': 'fas fa-clipboard-check',
        'order': 40,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'التركيبات',
        'code': 'installations',
        'url_name': 'installations:dashboard',
        'department_type': 'department',
        'icon': 'fas fa-tools',
        'order': 50,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'المصنع',
        'code': 'factory',
        'url_name': 'factory:factory_list',
        'department_type': 'department',
        'icon': 'fas fa-industry',
        'order': 60,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'التقارير',
        'code': 'reports',
        'url_name': 'reports:dashboard',
        'department_type': 'department',
        'icon': 'fas fa-chart-bar',
        'order': 70,
        'has_pages': False,
        'is_core': True,
        'children': []
    },
    {
        'name': 'إدارة البيانات',
        'code': 'data_management',
        'url_name': 'data_management:index',
        'department_type': 'department',
        'icon': 'fas fa-database',
        'order': 80,
        'has_pages': True,
        'is_core': True,
        'children': [
            {
                'name': 'مزامنة غوغل',
                'code': 'google_sync',
                'url_name': 'data_management:google_sync',
                'department_type': 'unit',
                'icon': 'fab fa-google',
                'order': 10,
                'has_pages': False,
                'is_core': True,
            },
            {
                'name': 'استيراد/تصدير إكسل',
                'code': 'excel_import_export',
                'url_name': 'data_management:excel_dashboard',
                'department_type': 'unit',
                'icon': 'fas fa-file-excel',
                'order': 20,
                'has_pages': False,
                'is_core': True,
            },
            {
                'name': 'النسخ الاحتياطي',
                'code': 'backup',
                'url_name': 'data_management:backup_list',
                'department_type': 'unit',
                'icon': 'fas fa-save',
                'order': 30,
                'has_pages': False,
                'is_core': True,
            },
            {
                'name': 'إدارة قواعد البيانات',
                'code': 'db_manager',
                'url_name': 'data_management:db_dashboard',
                'department_type': 'unit',
                'icon': 'fas fa-database',
                'order': 40,
                'has_pages': False,
                'is_core': True,
            }
        ]
    }
]

def create_core_departments():
    """
    إنشاء الأقسام الأساسية للنظام إذا لم تكن موجودة وتعطيل الأقسام غير الأساسية
    """
    from accounts.models import Department

    # الحصول على قائمة بأكواد الأقسام الأساسية
    core_dept_codes = [dept['code'] for dept in CORE_DEPARTMENTS]
    core_child_codes = []

    for dept in CORE_DEPARTMENTS:
        for child in dept.get('children', []):
            core_child_codes.append(child['code'])

    # إنشاء الأقسام الرئيسية
    for dept_data in CORE_DEPARTMENTS:
        children = dept_data.pop('children', [])

        # إنشاء القسم الرئيسي إذا لم يكن موجودًا
        dept, _ = Department.objects.update_or_create(
            code=dept_data['code'],
            defaults=dept_data
        )

        # إنشاء الأقسام الفرعية
        for child_data in children:
            child_data['parent'] = dept
            Department.objects.update_or_create(
                code=child_data['code'],
                defaults=child_data
            )

    # تعطيل الأقسام غير الأساسية
    Department.objects.filter(parent__isnull=True).exclude(code__in=core_dept_codes).update(is_active=False)
    Department.objects.filter(parent__isnull=False).exclude(code__in=core_child_codes).update(is_active=False)

    # تأكد من أن جميع الأقسام الأساسية نشطة
    Department.objects.filter(code__in=core_dept_codes).update(is_active=True, is_core=True)
    Department.objects.filter(code__in=core_child_codes).update(is_active=True, is_core=True)

    print(f"تم إنشاء {len(core_dept_codes)} قسم أساسي و {len(core_child_codes)} قسم فرعي أساسي")
