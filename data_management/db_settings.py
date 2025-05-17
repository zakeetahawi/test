"""
ملف إعدادات قاعدة البيانات الخارجي
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# الحصول على مسار المشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# مسار ملف إعدادات قاعدة البيانات
DB_SETTINGS_FILE = os.path.join(BASE_DIR, 'db_settings.json')

def get_active_database_settings():
    """
    الحصول على إعدادات قاعدة البيانات النشطة

    Returns:
        dict: إعدادات قاعدة البيانات النشطة
    """
    try:
        # التحقق من وجود ملف الإعدادات
        if not os.path.exists(DB_SETTINGS_FILE):
            # إنشاء ملف إعدادات افتراضي
            default_settings = {
                'active_db': None,
                'databases': {}
            }
            save_database_settings(default_settings)
            return default_settings

        # قراءة ملف الإعدادات
        with open(DB_SETTINGS_FILE, 'r') as f:
            settings = json.load(f)

        return settings
    except Exception as e:
        logger.error(f"حدث خطأ أثناء قراءة إعدادات قاعدة البيانات: {str(e)}")
        return {
            'active_db': None,
            'databases': {}
        }

def save_database_settings(settings):
    """
    حفظ إعدادات قاعدة البيانات

    Args:
        settings (dict): إعدادات قاعدة البيانات
    """
    try:
        # حفظ ملف الإعدادات
        with open(DB_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error(f"حدث خطأ أثناء حفظ إعدادات قاعدة البيانات: {str(e)}")

def set_active_database(db_id):
    """
    تعيين قاعدة البيانات النشطة

    Args:
        db_id: معرف قاعدة البيانات
    """
    try:
        # الحصول على إعدادات قاعدة البيانات
        settings = get_active_database_settings()

        # تعيين قاعدة البيانات النشطة
        settings['active_db'] = db_id

        # حفظ الإعدادات
        save_database_settings(settings)

        logger.info(f"تم تعيين قاعدة البيانات النشطة: {db_id}")
        return True
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تعيين قاعدة البيانات النشطة: {str(e)}")
        return False

def add_database_settings(db_id, db_settings):
    """
    إضافة إعدادات قاعدة بيانات

    Args:
        db_id: معرف قاعدة البيانات
        db_settings: إعدادات قاعدة البيانات
    """
    try:
        # الحصول على إعدادات قاعدة البيانات
        settings = get_active_database_settings()

        # إضافة إعدادات قاعدة البيانات
        settings['databases'][str(db_id)] = db_settings

        # حفظ الإعدادات
        save_database_settings(settings)

        logger.info(f"تم إضافة إعدادات قاعدة البيانات: {db_id}")
        return True
    except Exception as e:
        logger.error(f"حدث خطأ أثناء إضافة إعدادات قاعدة البيانات: {str(e)}")
        return False

def remove_database_settings(db_id):
    """
    حذف إعدادات قاعدة بيانات

    Args:
        db_id: معرف قاعدة البيانات
    """
    try:
        # الحصول على إعدادات قاعدة البيانات
        settings = get_active_database_settings()

        # حذف إعدادات قاعدة البيانات
        if str(db_id) in settings['databases']:
            del settings['databases'][str(db_id)]

        # إذا كانت قاعدة البيانات المحذوفة هي النشطة، قم بتعيين قاعدة بيانات أخرى كنشطة
        if settings['active_db'] == db_id:
            # البحث عن قاعدة بيانات أخرى
            if settings['databases']:
                settings['active_db'] = list(settings['databases'].keys())[0]
            else:
                settings['active_db'] = None

        # حفظ الإعدادات
        save_database_settings(settings)

        logger.info(f"تم حذف إعدادات قاعدة البيانات: {db_id}")
        return True
    except Exception as e:
        logger.error(f"حدث خطأ أثناء حذف إعدادات قاعدة البيانات: {str(e)}")
        return False

def reset_to_default_settings():
    """
    إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية
    """
    try:
        # إنشاء ملف إعدادات افتراضي
        default_settings = {
            'active_db': None,
            'databases': {}
        }

        # حفظ الإعدادات
        save_database_settings(default_settings)

        logger.info("تم إعادة تعيين إعدادات قاعدة البيانات إلى الإعدادات الافتراضية")
        return True
    except Exception as e:
        logger.error(f"حدث خطأ أثناء إعادة تعيين إعدادات قاعدة البيانات: {str(e)}")
        return False
