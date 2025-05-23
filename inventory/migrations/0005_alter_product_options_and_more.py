# Generated by Django 4.2.9 on 2025-05-06 23:21

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_auto_20250507_0218'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created_at'], 'verbose_name': 'منتج', 'verbose_name_plural': 'منتجات'},
        ),
        migrations.RemoveIndex(
            model_name='product',
            name='product_name_idx',
        ),
        migrations.RemoveIndex(
            model_name='product',
            name='product_code_idx',
        ),
        migrations.RemoveIndex(
            model_name='product',
            name='product_price_idx',
        ),
        migrations.RenameIndex(
            model_name='product',
            new_name='inventory_p_categor_607069_idx',
            old_name='product_category_idx',
        ),
        migrations.RenameIndex(
            model_name='product',
            new_name='inventory_p_created_081871_idx',
            old_name='product_created_at_idx',
        ),
        migrations.RemoveField(
            model_name='product',
            name='unit',
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='inventory.category', verbose_name='الفئة'),
        ),
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='رمز المنتج'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='السعر'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name', 'code'], name='inventory_p_name_af55cc_idx'),
        ),
    ]
