from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        # إضافة فهارس لنموذج Report
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['report_type'], name='report_type_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['created_by'], name='report_creator_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['created_at'], name='report_created_idx'),
        ),
        
        # إضافة فهارس لنموذج SavedReport
        migrations.AddIndex(
            model_name='savedreport',
            index=models.Index(fields=['report'], name='saved_report_idx'),
        ),
        migrations.AddIndex(
            model_name='savedreport',
            index=models.Index(fields=['created_by'], name='saved_report_creator_idx'),
        ),
        migrations.AddIndex(
            model_name='savedreport',
            index=models.Index(fields=['created_at'], name='saved_report_created_idx'),
        ),
        
        # إضافة فهارس لنموذج ReportSchedule
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['report'], name='schedule_report_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['frequency'], name='schedule_frequency_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['is_active'], name='schedule_active_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['created_by'], name='schedule_creator_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['created_at'], name='schedule_created_idx'),
        ),
    ]
