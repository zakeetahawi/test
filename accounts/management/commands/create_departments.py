from django.core.management.base import BaseCommand
from accounts.models import Department

class Command(BaseCommand):
    help = 'Create default departments'

    def handle(self, *args, **kwargs):
        # Map department codes to their data
        department_data = {
            'customers': {
                'name': 'العملاء',
                'url_name': 'customers:customer_list',
                'icon': 'fas fa-users'
            },
            'orders': {
                'name': 'الطلبات',
                'url_name': 'orders:order_list',
                'icon': 'fas fa-shopping-cart'
            },
            'inventory': {
                'name': 'المخزون',
                'url_name': 'inventory:inventory_list',
                'icon': 'fas fa-boxes'
            },
            'factory': {
                'name': 'المصنع',
                'url_name': 'factory:factory_list',
                'icon': 'fas fa-industry'
            },
            'inspections': {
                'name': 'المعاينات',
                'url_name': 'inspections:inspection_list',
                'icon': 'fas fa-clipboard-check'
            },
            'installations': {
                'name': 'التركيبات',
                'url_name': 'installations:installation_list',
                'icon': 'fas fa-tools'
            },
            'reports': {
                'name': 'التقارير',
                'url_name': 'reports:report_list',
                'icon': 'fas fa-chart-bar'
            }
        }
        
        for code, data in department_data.items():
            department, created = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': data['name'],
                    'url_name': data['url_name'],
                    'icon': data['icon']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {department.name}'))
            else:
                # Update existing departments
                department.name = data['name']
                department.url_name = data['url_name']
                department.icon = data['icon']
                department.save()
                self.stdout.write(self.style.SUCCESS(f'Updated department: {department.name}'))
