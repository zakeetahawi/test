# Generated by Django 5.2 on 2025-05-18 11:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('installations', '0004_merge_0002_add_indexes_0003_auto_20250507_0639'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_installation_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_priority_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_status_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_reported_by_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_assigned_to_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_resolved_at_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationissue',
            name='issue_created_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationnotification',
            name='notif_installation_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationnotification',
            name='notif_type_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationnotification',
            name='notif_read_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationnotification',
            name='notif_created_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationqualitycheck',
            name='quality_installation_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationqualitycheck',
            name='quality_criteria_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationqualitycheck',
            name='quality_rating_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationqualitycheck',
            name='quality_checked_by_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationqualitycheck',
            name='quality_created_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationstep',
            name='step_installation_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationstep',
            name='step_completed_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationstep',
            name='step_completed_at_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationstep',
            name='step_completed_by_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationteam',
            name='team_name_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationteam',
            name='team_leader_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationteam',
            name='team_branch_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationteam',
            name='team_active_idx',
        ),
        migrations.RemoveIndex(
            model_name='installationteam',
            name='team_created_idx',
        ),
    ]
