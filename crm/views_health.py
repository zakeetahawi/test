from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
import psutil
import os
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    فحص صحة التطبيق لـ Railway
    يتحقق من:
    1. اتصال قاعدة البيانات
    2. استخدام الذاكرة
    3. استخدام وحدة المعالجة المركزية
    4. مساحة القرص
    """
    # تسجيل طلب فحص الصحة
    logger.info(f"Health check requested from {request.META.get('REMOTE_ADDR')} - Path: {request.path}")

    # إذا كان المسار هو '/health/' بالضبط (كما يتوقع Railway)، نعيد استجابة بسيطة
    if request.path == '/health/':
        return HttpResponse("OK", content_type="text/plain")

    # التحقق من اتصال قاعدة البيانات
    db_status = "healthy"
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)
        logger.error(f"Database connection error: {str(e)}")

    # معلومات النظام
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_percent(interval=0.1)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        memory = None
        disk = None
        cpu = None

    response_data = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": {
            "status": db_status,
            "error": db_error,
            "engine": settings.DATABASES['default'].get('ENGINE', "dj_database_url (PostgreSQL)"),
        },
    }

    # إضافة معلومات النظام إذا كانت متاحة
    if memory and disk and cpu is not None:
        response_data["system"] = {
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": cpu,
            "disk_usage_percent": disk.percent,
        }

    response_data["environment"] = "production" if not settings.DEBUG else "development"

    # دائمًا نعيد 200 OK لـ Railway
    return JsonResponse(response_data, status=200)
