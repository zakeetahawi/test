from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('installations', '0001_initial'),
    ]

    operations = [
        # إضافة فهارس لنموذج InstallationTeam
        migrations.AddIndex(
            model_name='installationteam',
            index=models.Index(fields=['name'], name='team_name_idx'),
        ),
        migrations.AddIndex(
            model_name='installationteam',
            index=models.Index(fields=['leader'], name='team_leader_idx'),
        ),
        migrations.AddIndex(
            model_name='installationteam',
            index=models.Index(fields=['branch'], name='team_branch_idx'),
        ),
        migrations.AddIndex(
            model_name='installationteam',
            index=models.Index(fields=['is_active'], name='team_active_idx'),
        ),
        migrations.AddIndex(
            model_name='installationteam',
            index=models.Index(fields=['created_at'], name='team_created_idx'),
        ),
        
        # إضافة فهارس لنموذج InstallationStep
        migrations.AddIndex(
            model_name='installationstep',
            index=models.Index(fields=['installation'], name='step_installation_idx'),
        ),
        migrations.AddIndex(
            model_name='installationstep',
            index=models.Index(fields=['is_completed'], name='step_completed_idx'),
        ),
        migrations.AddIndex(
            model_name='installationstep',
            index=models.Index(fields=['completed_at'], name='step_completed_at_idx'),
        ),
        migrations.AddIndex(
            model_name='installationstep',
            index=models.Index(fields=['completed_by'], name='step_completed_by_idx'),
        ),
        
        # إضافة فهارس لنموذج InstallationQualityCheck
        migrations.AddIndex(
            model_name='installationqualitycheck',
            index=models.Index(fields=['installation'], name='quality_installation_idx'),
        ),
        migrations.AddIndex(
            model_name='installationqualitycheck',
            index=models.Index(fields=['criteria'], name='quality_criteria_idx'),
        ),
        migrations.AddIndex(
            model_name='installationqualitycheck',
            index=models.Index(fields=['rating'], name='quality_rating_idx'),
        ),
        migrations.AddIndex(
            model_name='installationqualitycheck',
            index=models.Index(fields=['checked_by'], name='quality_checked_by_idx'),
        ),
        migrations.AddIndex(
            model_name='installationqualitycheck',
            index=models.Index(fields=['created_at'], name='quality_created_idx'),
        ),
        
        # إضافة فهارس لنموذج InstallationIssue
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['installation'], name='issue_installation_idx'),
        ),
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['priority'], name='issue_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['status'], name='issue_status_idx'),
        ),
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['reported_by'], name='issue_reported_by_idx'),
        ),
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['assigned_to'], name='issue_assigned_to_idx'),
        ),
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['resolved_at'], name='issue_resolved_at_idx'),
        ),
        migrations.AddIndex(
            model_name='installationissue',
            index=models.Index(fields=['created_at'], name='issue_created_idx'),
        ),
        
        # إضافة فهارس لنموذج InstallationNotification
        migrations.AddIndex(
            model_name='installationnotification',
            index=models.Index(fields=['installation'], name='notif_installation_idx'),
        ),
        migrations.AddIndex(
            model_name='installationnotification',
            index=models.Index(fields=['type'], name='notif_type_idx'),
        ),
        migrations.AddIndex(
            model_name='installationnotification',
            index=models.Index(fields=['is_read'], name='notif_read_idx'),
        ),
        migrations.AddIndex(
            model_name='installationnotification',
            index=models.Index(fields=['created_at'], name='notif_created_idx'),
        ),
    ]
