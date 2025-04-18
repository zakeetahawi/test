from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.files.base import ContentFile
from data_import_export.models import ImportTemplate
from data_import_export.utils import generate_multi_sheet_template

class Command(BaseCommand):
    help = 'Generate import templates for all importable models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate templates even if they already exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Define importable models
        importable_models = {
            'inventory': {
                'models': ['product', 'supplier'],
                'name': 'قالب استيراد المخزون',
                'description': 'قالب لاستيراد المنتجات والموردين',
            },
            'customers': {
                'models': ['customer'],
                'name': 'قالب استيراد العملاء',
                'description': 'قالب لاستيراد بيانات العملاء',
            },
            'orders': {
                'models': ['order', 'payment'],
                'name': 'قالب استيراد الطلبات',
                'description': 'قالب لاستيراد الطلبات والمدفوعات',
            },
        }
        
        # Generate templates
        for app, config in importable_models.items():
            # Check if template already exists
            template_name = config['name']
            template_exists = ImportTemplate.objects.filter(name=template_name).exists()
            
            if template_exists and not force:
                self.stdout.write(self.style.WARNING(f'Template "{template_name}" already exists. Use --force to regenerate.'))
                continue
            
            # Generate model names
            model_names = [f"{app}.{model}" for model in config['models']]
            
            # Generate template
            try:
                output = generate_multi_sheet_template(model_names)
                
                # Create or update template
                if template_exists:
                    template = ImportTemplate.objects.get(name=template_name)
                    template.description = config['description']
                    template.model_name = model_names[0]  # Use first model as primary
                    template.is_active = True
                    template.file.save(f"{app}_import_template.xlsx", ContentFile(output.read()), save=False)
                    template.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated template "{template_name}"'))
                else:
                    template = ImportTemplate(
                        name=template_name,
                        description=config['description'],
                        model_name=model_names[0],  # Use first model as primary
                        is_active=True
                    )
                    template.save()
                    template.file.save(f"{app}_import_template.xlsx", ContentFile(output.read()), save=True)
                    self.stdout.write(self.style.SUCCESS(f'Created template "{template_name}"'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error generating template for {app}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Done generating import templates'))
