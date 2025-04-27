from django.db import migrations, models
from django.utils.translation import gettext_lazy as _

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0004_add_product_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(
                choices=[
                    ('piece', _('قطعة')),
                    ('meter', _('متر')),
                    ('sqm', _('متر مربع')),
                    ('kg', _('كيلوجرام')),
                ],
                default='piece',
                max_length=20,
                verbose_name=_('الوحدة')
            ),
        ),
    ]
