from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('factory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productionline',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='اسم خط الإنتاج'),
        ),
    ]
