import logging
from django_apscheduler.models import DjangoJobExecution
from django.conf import settings
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django_apscheduler import util

from .services.auto_sync_service import auto_sync_data
from .models import GoogleSheetsConfig

logger = logging.getLogger(__name__)


@util.close_old_connections
def perform_sync():
    """
    وظيفة تنفذ المزامنة التلقائية مع Google Sheets
    """
    logger.info("بدء المزامنة التلقائية في %s", datetime.now())
    try:
        success, count = auto_sync_data(force=False)
        if success:
            logger.info("اكتمال المزامنة التلقائية بنجاح. تمت مزامنة %s سجل.", count)
        else:
            logger.warning("لم تتم المزامنة، ربما بسبب انتهاء الفاصل الزمني.")
    except Exception as e:
        logger.error("حدث خطأ أثناء المزامنة التلقائية: %s", str(e))


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):  # 7 days
    """
    مهمة لحذف سجلات التنفيذ القديمة للمهام المجدولة
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start_scheduler():
    """
    بدء جدولة المهام للمزامنة التلقائية
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # الحصول على إعدادات المزامنة من قاعدة البيانات
    config = GoogleSheetsConfig.objects.filter(is_active=True).first()
    sync_interval = 1  # القيمة الافتراضية دقيقة واحدة
    
    # استخدام القيمة من قاعدة البيانات إذا كانت موجودة
    if config and config.sync_interval_minutes:
        sync_interval = max(1, config.sync_interval_minutes)  # لا تقل عن دقيقة واحدة

    # إضافة وظيفة المزامنة التلقائية
    scheduler.add_job(
        perform_sync,
        'interval',
        minutes=sync_interval,
        id='sync_with_google_sheets',
        replace_existing=True
    )

    # إضافة وظيفة حذف سجلات التنفيذ القديمة للمهام المجدولة
    scheduler.add_job(
        delete_old_job_executions,
        trigger='cron',
        day_of_week='mon',
        hour='00',
        minute='00',
        id='delete_old_job_executions',
        replace_existing=True
    )

    try:
        logger.info("بدء تشغيل جدولة المهام مع فترة مزامنة %s دقيقة...", sync_interval)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("تم إيقاف جدولة المهام")
        scheduler.shutdown()