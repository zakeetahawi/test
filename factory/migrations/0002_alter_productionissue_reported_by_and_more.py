# Generated by Django 4.2.9 on 2025-05-07 03:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('factory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productionissue',
            name='reported_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_production_issues', to=settings.AUTH_USER_MODEL, verbose_name='تم الإبلاغ بواسطة'),
        ),
        migrations.AlterField(
            model_name='productionissue',
            name='resolved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_production_issues', to=settings.AUTH_USER_MODEL, verbose_name='تم الحل بواسطة'),
        ),
    ]
