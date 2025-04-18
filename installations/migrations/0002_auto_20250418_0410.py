# Generated by Django 3.2.25 on 2025-04-18 02:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('installations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='installation',
            name='team_leader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lead_installations', to=settings.AUTH_USER_MODEL, verbose_name='قائد الفريق'),
        ),
        migrations.AddField(
            model_name='transportrequest',
            name='team_leader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lead_transports', to=settings.AUTH_USER_MODEL, verbose_name='قائد الفريق'),
        ),
    ]
