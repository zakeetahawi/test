from django.db import migrations

def create_sample_products(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    Product = apps.get_model('inventory', 'Product')
    
    # Get categories
    fabrics_category = Category.objects.filter(name='أقمشة').first()
    accessories_category = Category.objects.filter(name='اكسسوارات').first()
    
    if fabrics_category:
        # Create sample fabrics
        Product.objects.get_or_create(
            name='قماش قطن مصري',
            defaults={
                'code': 'FAB001',
                'category': fabrics_category,
                'unit': 'meter',
                'description': 'قماش قطن مصري 100%',
                'price': 50.00,
                'minimum_stock': 100
            }
        )
        Product.objects.get_or_create(
            name='قماش حرير طبيعي',
            defaults={
                'code': 'FAB002',
                'category': fabrics_category,
                'unit': 'meter',
                'description': 'قماش حرير طبيعي فاخر',
                'price': 150.00,
                'minimum_stock': 50
            }
        )
    
    if accessories_category:
        # Create sample accessories
        Product.objects.get_or_create(
            name='أزرار ذهبية',
            defaults={
                'code': 'ACC001',
                'category': accessories_category,
                'unit': 'piece',
                'description': 'أزرار ذهبية اللون',
                'price': 5.00,
                'minimum_stock': 200
            }
        )
        Product.objects.get_or_create(
            name='شريط زخرفة',
            defaults={
                'code': 'ACC002',
                'category': accessories_category,
                'unit': 'meter',
                'description': 'شريط زخرفة مطرز',
                'price': 15.00,
                'minimum_stock': 100
            }
        )

def remove_sample_products(apps, schema_editor):
    Product = apps.get_model('inventory', 'Product')
    Product.objects.filter(code__in=['FAB001', 'FAB002', 'ACC001', 'ACC002']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0005_alter_product_unit'),
    ]

    operations = [
        migrations.RunPython(create_sample_products, remove_sample_products),
    ]
