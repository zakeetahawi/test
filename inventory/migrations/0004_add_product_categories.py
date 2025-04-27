from django.db import migrations

def create_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    
    # Create main categories if they don't exist
    Category.objects.get_or_create(
        name='أقمشة',
        defaults={'description': 'جميع أنواع الأقمشة'}
    )
    
    Category.objects.get_or_create(
        name='اكسسوارات',
        defaults={'description': 'جميع أنواع الإكسسوارات'}
    )

def remove_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    Category.objects.filter(name__in=['أقمشة', 'اكسسوارات']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0003_alter_stocktransaction_reason'),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]
