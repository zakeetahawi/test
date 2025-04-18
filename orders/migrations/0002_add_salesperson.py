from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Salesperson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='اسم البائع')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salespersons', to='accounts.Branch', verbose_name='الفرع')),
            ],
            options={
                'verbose_name': 'بائع',
                'verbose_name_plural': 'البائعون',
                'unique_together': {('name', 'branch')},
            },
        ),
        migrations.AddField(
            model_name='order',
            name='salesperson',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='orders.Salesperson', verbose_name='البائع'),
        ),
    ]
