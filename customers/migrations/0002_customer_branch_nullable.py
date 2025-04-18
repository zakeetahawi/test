from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='branch',
            field=models.ForeignKey(
                to='accounts.Branch',
                on_delete=models.PROTECT,
                related_name='customers',
                verbose_name='الفرع',
                null=True,
                blank=True,
            ),
        ),
    ]
