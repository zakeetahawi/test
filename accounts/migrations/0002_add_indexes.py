from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # إضافة فهارس للحقول المستخدمة بكثرة في الاستعلامات
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='username_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='email_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active'], name='is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['is_read'], name='is_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['created_at'], name='notification_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['is_active'], name='department_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['is_core'], name='department_is_core_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['parent'], name='department_parent_idx'),
        ),
        migrations.AddIndex(
            model_name='branch',
            index=models.Index(fields=['is_active'], name='branch_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='branch',
            index=models.Index(fields=['is_main_branch'], name='branch_is_main_idx'),
        ),
    ]
