# Generated by Django 3.2.25 on 2025-04-18 11:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inspections', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspection',
            name='inspector',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_inspections', to=settings.AUTH_USER_MODEL, verbose_name='المعاين'),
        ),
    ]
