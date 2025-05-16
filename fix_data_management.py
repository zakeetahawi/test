"""
سكريبت لإصلاح قسم إدارة البيانات في قاعدة البيانات
"""

import os
import django

# إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from accounts.models import Department

def fix_data_management_department():
    """
    تعديل قسم إدارة البيانات ليكون بدون صفحات متعددة وتوجيه مباشر إلى الصفحة الرئيسية
    """
    # البحث عن قسم إدارة البيانات
    data_mgmt_dept = Department.objects.filter(name__contains='إدارة البيانات').first()
    if not data_mgmt_dept:
        data_mgmt_dept = Department.objects.filter(url_name__contains='data_management').first()
    
    if data_mgmt_dept:
        print(f'Found department: {data_mgmt_dept.name}, url_name: {data_mgmt_dept.url_name}, has_pages: {data_mgmt_dept.has_pages}')
        
        # تعديل القسم ليكون بدون صفحات متعددة
        data_mgmt_dept.has_pages = False
        data_mgmt_dept.url_name = 'data_management:index'
        data_mgmt_dept.save()
        
        print('Updated successfully')
        
        # تعديل الأقسام الفرعية لإدارة البيانات
        for child in data_mgmt_dept.children.all():
            print(f'Found child department: {child.name}, url_name: {child.url_name}')
            # إلغاء تنشيط الأقسام الفرعية
            child.is_active = False
            child.save()
            print(f'Deactivated child department: {child.name}')
    else:
        print('Department not found')

if __name__ == '__main__':
    fix_data_management_department()
