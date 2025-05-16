from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from accounts.models import Department

class Command(BaseCommand):
    help = 'Add Database Manager department to the system'

    def handle(self, *args, **options):
        # Define the Database Manager department
        db_manager_dept = {
            'name': 'إدارة قواعد البيانات',
            'code': 'db_manager',
            'icon': 'fas fa-database',
            'url_name': 'data_management:db_dashboard',
            'order': 8,  # After Reports
            'description': 'إدارة قواعد البيانات والنسخ الاحتياطية والاستيراد/التصدير'
        }

        # Create or update the department
        dept, created = Department.objects.update_or_create(
            code=db_manager_dept['code'],
            defaults={
                'name': db_manager_dept['name'],
                'icon': db_manager_dept['icon'],
                'url_name': db_manager_dept['url_name'],
                'order': db_manager_dept['order'],
                'description': db_manager_dept['description'],
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created department: {dept.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Updated department: {dept.name}'))

        # Check if Data Management department exists
        data_management_dept = Department.objects.filter(code='data_management').first()

        if not data_management_dept:
            # Create Data Management department
            data_management_dept = Department.objects.create(
                name='إدارة البيانات',
                code='data_management',
                icon='fas fa-database',
                url_name='data_management:index',
                order=9,  # After DB Manager
                description='إدارة البيانات واستيراد/تصدير البيانات والنسخ الاحتياطية',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created department: {data_management_dept.name}'))

            # Create child departments for Data Management
            child_departments = [
                {
                    'name': 'استيراد/تصدير البيانات',
                    'code': 'import_export',
                    'icon': 'fas fa-exchange-alt',
                    'url_name': 'data_management:dashboard',
                    'order': 1,
                    'description': 'استيراد وتصدير البيانات',
                    'parent': data_management_dept
                },
                {
                    'name': 'النسخ الاحتياطية',
                    'code': 'backup',
                    'icon': 'fas fa-save',
                    'url_name': 'data_management:db_backup_list',
                    'order': 2,
                    'description': 'إدارة النسخ الاحتياطية',
                    'parent': data_management_dept
                },
                {
                    'name': 'إدارة قواعد البيانات',
                    'code': 'db_manager_child',
                    'icon': 'fas fa-database',
                    'url_name': 'data_management:db_dashboard',
                    'order': 3,
                    'description': 'إدارة قواعد البيانات',
                    'parent': data_management_dept
                }
            ]

            for child_data in child_departments:
                child, created = Department.objects.update_or_create(
                    code=child_data['code'],
                    defaults={
                        'name': child_data['name'],
                        'icon': child_data['icon'],
                        'url_name': child_data['url_name'],
                        'order': child_data['order'],
                        'description': child_data['description'],
                        'is_active': True,
                        'parent': child_data['parent']
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created child department: {child.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Updated child department: {child.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully added Database Manager department to the system.'))
