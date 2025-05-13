from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    """بدء تشغيل جدولة المهام"""
    try:
        # إنشاء جدولة المهام
        scheduler = BackgroundScheduler(settings.SCHEDULER_CONFIG)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # إضافة مهمة تنظيف الجلسات
        if hasattr(settings, 'SESSION_CLEANUP_SCHEDULE'):
            config = settings.SESSION_CLEANUP_SCHEDULE
            days = config.get('days', 1)
            fix_users = config.get('fix_users', True)
            frequency = config.get('frequency', 'daily')
            hour = config.get('hour', 3)
            minute = config.get('minute', 0)
            
            # تحديد وقت التنفيذ
            if frequency == 'daily':
                # إضافة المهمة للتنفيذ اليومي
                scheduler.add_job(
                    cleanup_sessions_job,
                    'cron',
                    hour=hour,
                    minute=minute,
                    id='cleanup_sessions',
                    replace_existing=True,
                    kwargs={
                        'days': days,
                        'fix_users': fix_users
                    }
                )
                logger.info(f"تمت جدولة مهمة تنظيف الجلسات للتنفيذ يوميًا في الساعة {hour}:{minute}")
            elif frequency == 'hourly':
                # إضافة المهمة للتنفيذ كل ساعة
                scheduler.add_job(
                    cleanup_sessions_job,
                    'interval',
                    hours=1,
                    id='cleanup_sessions',
                    replace_existing=True,
                    kwargs={
                        'days': days,
                        'fix_users': fix_users
                    }
                )
                logger.info("تمت جدولة مهمة تنظيف الجلسات للتنفيذ كل ساعة")
        
        # بدء تشغيل الجدولة
        scheduler.start()
        logger.info("تم بدء تشغيل جدولة المهام بنجاح")
        
        return scheduler
    except Exception as e:
        logger.error(f"حدث خطأ أثناء بدء تشغيل جدولة المهام: {str(e)}")
        return None

def cleanup_sessions_job(days=1, fix_users=True):
    """مهمة تنظيف الجلسات"""
    try:
        logger.info(f"بدء تنفيذ مهمة تنظيف الجلسات (days={days}, fix_users={fix_users})")
        
        # تنفيذ أمر تنظيف الجلسات
        args = ['--days', str(days)]
        if fix_users:
            args.append('--fix-users')
        
        call_command('cleanup_sessions', *args)
        
        logger.info("تم تنفيذ مهمة تنظيف الجلسات بنجاح")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تنفيذ مهمة تنظيف الجلسات: {str(e)}")
