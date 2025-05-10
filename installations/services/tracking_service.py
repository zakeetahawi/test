"""
خدمة تتبع عمليات التركيب في الوقت الفعلي
"""
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from django.utils.translation import gettext as _
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import timedelta

from ..models import (
    Installation,
    InstallationStep,
    InstallationQualityCheck,
    InstallationIssue,
    InstallationNotification
)

class InstallationTrackingService:
    """خدمة تتبع وتحديث حالة التركيب"""

    @staticmethod
    def update_installation_status(installation, new_status, **kwargs):
        """تحديث حالة التركيب وإرسال الإشعارات"""
        old_status = installation.status
        installation.status = new_status

        # تحديث التواريخ حسب الحالة
        if new_status == 'in_progress':
            installation.actual_start_date = timezone.now()
        elif new_status == 'completed':
            installation.actual_end_date = timezone.now()

        # تحديث الملاحظات إذا وجدت
        if kwargs.get('notes'):
            installation.notes = kwargs['notes']

        installation.save()

        # إنشاء إشعار بتغيير الحالة
        InstallationTrackingService.create_status_notification(
            installation,
            old_status,
            new_status,
            kwargs.get('notes', '')
        )

        # إرسال التحديث في الوقت الفعلي
        InstallationTrackingService.send_realtime_update(
            installation,
            'status_update',
            {
                'status': new_status,
                'old_status': old_status,
                'notes': kwargs.get('notes', '')
            }
        )

    @staticmethod
    def update_step_status(step, is_completed, completed_by=None, notes=None, photo=None):
        """تحديث حالة خطوة التركيب"""
        step.is_completed = is_completed
        if is_completed:
            step.completed_at = timezone.now()
            step.completed_by = completed_by
        else:
            step.completed_at = None
            step.completed_by = None

        if notes:
            step.notes = notes
        if photo:
            step.photo = photo

        step.save()

        # تحديث نسبة الإكمال في الذاكرة المؤقتة
        InstallationTrackingService.update_completion_percentage(step.installation)

        # إرسال التحديث في الوقت الفعلي
        InstallationTrackingService.send_realtime_update(
            step.installation,
            'step_update',
            {
                'step_id': step.id,
                'is_completed': is_completed,
                'completion_percentage': InstallationTrackingService.get_completion_percentage(step.installation)
            }
        )

    @staticmethod
    def add_quality_check(installation, criteria, rating, checked_by, notes=None, photo=None):
        """إضافة فحص جودة جديد"""
        quality_check = InstallationQualityCheck.objects.create(
            installation=installation,
            criteria=criteria,
            rating=rating,
            checked_by=checked_by,
            notes=notes,
            photo=photo
        )

        # إنشاء إشعار بفحص الجودة
        InstallationNotification.objects.create(
            installation=installation,
            type='quality_check',
            title=_('فحص جودة جديد'),
            message=_(f'تم إضافة فحص جودة جديد: {quality_check.get_criteria_display()}')
        )

        # إرسال التحديث في الوقت الفعلي
        InstallationTrackingService.send_realtime_update(
            installation,
            'quality_check',
            {
                'criteria': criteria,
                'rating': rating,
                'quality_rating': installation.quality_rating
            }
        )

    @staticmethod
    def report_issue(installation, title, description, priority, reported_by):
        """الإبلاغ عن مشكلة في التركيب"""
        issue = InstallationIssue.objects.create(
            installation=installation,
            title=title,
            description=description,
            priority=priority,
            reported_by=reported_by
        )

        # إنشاء إشعار بالمشكلة
        InstallationNotification.objects.create(
            installation=installation,
            type='issue',
            title=_('مشكلة جديدة'),
            message=_(f'تم الإبلاغ عن مشكلة جديدة: {title}')
        )

        # إرسال التحديث في الوقت الفعلي
        InstallationTrackingService.send_realtime_update(
            installation,
            'issue_reported',
            {
                'issue_id': issue.id,
                'title': title,
                'priority': priority
            }
        )

        return issue

    @staticmethod
    def resolve_issue(issue, resolution, resolved_by):
        """حل مشكلة التركيب"""
        issue.status = 'resolved'
        issue.resolution = resolution
        issue.resolved_by = resolved_by
        issue.resolved_at = timezone.now()
        issue.save()

        # إنشاء إشعار بحل المشكلة
        InstallationNotification.objects.create(
            installation=issue.installation,
            type='issue',
            title=_('تم حل المشكلة'),
            message=_(f'تم حل المشكلة: {issue.title}')
        )

        # إرسال التحديث في الوقت الفعلي
        InstallationTrackingService.send_realtime_update(
            issue.installation,
            'issue_resolved',
            {
                'issue_id': issue.id,
                'resolution': resolution
            }
        )

    @staticmethod
    def get_completion_percentage(installation):
        """حساب نسبة إكمال التركيب"""
        cache_key = f'installation_completion_{installation.id}'
        percentage = cache.get(cache_key)

        if percentage is None:
            total_steps = installation.steps.count()
            if total_steps == 0:
                percentage = 0
            else:
                completed_steps = installation.steps.filter(is_completed=True).count()
                percentage = (completed_steps / total_steps) * 100
            cache.set(cache_key, percentage, 300)  # تخزين لمدة 5 دقائق

        return percentage

    @staticmethod
    def update_completion_percentage(installation):
        """تحديث نسبة الإكمال في الذاكرة المؤقتة"""
        total_steps = installation.steps.count()
        if total_steps > 0:
            completed_steps = installation.steps.filter(is_completed=True).count()
            percentage = (completed_steps / total_steps) * 100
            cache_key = f'installation_completion_{installation.id}'
            cache.set(cache_key, percentage, 300)
            return percentage
        return 0

    @staticmethod
    def get_installation_timeline(installation):
        """الحصول على الجدول الزمني للتركيب"""
        timeline = []

        # إضافة تاريخ الإنشاء
        timeline.append({
            'date': installation.created_at,
            'type': 'created',
            'description': _('تم إنشاء طلب التركيب')
        })

        # إضافة تواريخ تغيير الحالة
        notifications = installation.notifications.filter(
            type='status_change'
        ).order_by('created_at')
        for notification in notifications:
            timeline.append({
                'date': notification.created_at,
                'type': 'status_change',
                'description': notification.message
            })

        # إضافة الخطوات المكتملة
        completed_steps = installation.steps.filter(
            is_completed=True
        ).order_by('completed_at')
        for step in completed_steps:
            timeline.append({
                'date': step.completed_at,
                'type': 'step_completed',
                'description': _(f'تم إكمال خطوة: {step.name}')
            })

        # إضافة فحوصات الجودة
        quality_checks = installation.quality_checks.all().order_by('created_at')
        for check in quality_checks:
            timeline.append({
                'date': check.created_at,
                'type': 'quality_check',
                'description': _(f'فحص جودة: {check.get_criteria_display()}')
            })

        # إضافة المشاكل وحلولها
        issues = installation.issues.all().order_by('created_at')
        for issue in issues:
            timeline.append({
                'date': issue.created_at,
                'type': 'issue_reported',
                'description': _(f'تم الإبلاغ عن مشكلة: {issue.title}')
            })
            if issue.resolved_at:
                timeline.append({
                    'date': issue.resolved_at,
                    'type': 'issue_resolved',
                    'description': _(f'تم حل المشكلة: {issue.title}')
                })

        return sorted(timeline, key=lambda x: x['date'])

    @staticmethod
    def create_status_notification(installation, old_status, new_status, notes=''):
        """إنشاء إشعار بتغيير الحالة"""
        status_display = dict(Installation.STATUS_CHOICES)
        message = _(f'تم تغيير حالة التركيب من {status_display[old_status]} إلى {status_display[new_status]}')
        
        if notes:
            message += f'\nملاحظات: {notes}'

        InstallationNotification.objects.create(
            installation=installation,
            type='status_change',
            title=_('تغيير حالة التركيب'),
            message=message
        )

    @staticmethod
    def send_realtime_update(installation, update_type, data):
        """إرسال تحديث في الوقت الفعلي"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'installation_{installation.id}',
            {
                'type': 'installation_update',
                'update_type': update_type,
                'data': data
            }
        )

    @staticmethod
    def get_active_installations():
        """الحصول على عمليات التركيب النشطة"""
        return Installation.objects.filter(
            Q(status='scheduled') | Q(status='in_progress')
        ).select_related(
            'order',
            'team',
            'inspection'
        ).prefetch_related(
            'steps',
            'quality_checks',
            'issues'
        )

    @staticmethod
    def get_overdue_installations():
        """الحصول على عمليات التركيب المتأخرة"""
        today = timezone.now().date()
        return Installation.objects.filter(
            scheduled_date__lt=today,
            status__in=['pending', 'scheduled']
        ).select_related(
            'order',
            'team'
        )

    @staticmethod
    def get_upcoming_installations(days=7):
        """الحصول على عمليات التركيب القادمة"""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days)
        return Installation.objects.filter(
            scheduled_date__range=[start_date, end_date],
            status__in=['pending', 'scheduled']
        ).select_related(
            'order',
            'team'
        ).order_by('scheduled_date')

    @staticmethod
    def get_team_schedule(team, start_date=None, end_date=None):
        """الحصول على جدول فريق التركيب"""
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        return Installation.objects.filter(
            team=team,
            scheduled_date__range=[start_date, end_date],
            status__in=['scheduled', 'in_progress']
        ).select_related(
            'order',
            'inspection'
        ).order_by('scheduled_date')
