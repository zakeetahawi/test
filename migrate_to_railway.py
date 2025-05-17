#!/usr/bin/env python
"""
سكريبت لنقل البيانات من قاعدة البيانات المحلية إلى قاعدة البيانات الجديدة على Railway
"""
import os
import sys
import subprocess
import argparse
import time
from datetime import datetime

def create_backup(backup_file=None):
    """إنشاء نسخة احتياطية من قاعدة البيانات المحلية"""
    if not backup_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"railway_migration_{timestamp}.psql"
    
    backup_path = os.path.join("backups", backup_file)
    
    print(f"إنشاء نسخة احتياطية في {backup_path}...")
    
    # استخدام dbbackup لإنشاء نسخة احتياطية
    result = subprocess.run(
        ["python", "manage.py", "dbbackup", "-o", backup_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"خطأ في إنشاء النسخة الاحتياطية: {result.stderr}")
        return None
    
    print("تم إنشاء النسخة الاحتياطية بنجاح.")
    return backup_path

def update_env_file(db_url, db_user, db_password, db_host, db_port, db_name):
    """تحديث ملف .env بمعلومات قاعدة البيانات الجديدة"""
    print("تحديث ملف .env...")
    
    with open(".env", "r", encoding="utf-8") as f:
        env_content = f.readlines()
    
    new_env_content = []
    updated = {
        "DATABASE_URL": False,
        "DB_USER": False,
        "DB_PASSWORD": False,
        "DB_HOST": False,
        "DB_PORT": False,
        "DB_NAME": False
    }
    
    for line in env_content:
        if line.startswith("DATABASE_URL="):
            new_env_content.append(f"DATABASE_URL={db_url}\n")
            updated["DATABASE_URL"] = True
        elif line.startswith("DB_USER="):
            new_env_content.append(f"DB_USER={db_user}\n")
            updated["DB_USER"] = True
        elif line.startswith("DB_PASSWORD="):
            new_env_content.append(f"DB_PASSWORD={db_password}\n")
            updated["DB_PASSWORD"] = True
        elif line.startswith("DB_HOST="):
            new_env_content.append(f"DB_HOST={db_host}\n")
            updated["DB_HOST"] = True
        elif line.startswith("DB_PORT="):
            new_env_content.append(f"DB_PORT={db_port}\n")
            updated["DB_PORT"] = True
        elif line.startswith("DB_NAME="):
            new_env_content.append(f"DB_NAME={db_name}\n")
            updated["DB_NAME"] = True
        else:
            new_env_content.append(line)
    
    # إضافة أي متغيرات غير موجودة
    for key, value in updated.items():
        if not value:
            if key == "DATABASE_URL":
                new_env_content.append(f"DATABASE_URL={db_url}\n")
            elif key == "DB_USER":
                new_env_content.append(f"DB_USER={db_user}\n")
            elif key == "DB_PASSWORD":
                new_env_content.append(f"DB_PASSWORD={db_password}\n")
            elif key == "DB_HOST":
                new_env_content.append(f"DB_HOST={db_host}\n")
            elif key == "DB_PORT":
                new_env_content.append(f"DB_PORT={db_port}\n")
            elif key == "DB_NAME":
                new_env_content.append(f"DB_NAME={db_name}\n")
    
    with open(".env", "w", encoding="utf-8") as f:
        f.writelines(new_env_content)
    
    print("تم تحديث ملف .env بنجاح.")

def restore_backup_to_railway(backup_path):
    """استعادة النسخة الاحتياطية في قاعدة البيانات الجديدة على Railway"""
    print(f"استعادة النسخة الاحتياطية {backup_path} إلى قاعدة البيانات الجديدة...")
    
    # استخدام dbrestore لاستعادة النسخة الاحتياطية
    result = subprocess.run(
        ["python", "manage.py", "dbrestore", "-i", os.path.basename(backup_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"خطأ في استعادة النسخة الاحتياطية: {result.stderr}")
        return False
    
    print("تم استعادة النسخة الاحتياطية بنجاح.")
    return True

def test_connection():
    """اختبار الاتصال بقاعدة البيانات الجديدة"""
    print("اختبار الاتصال بقاعدة البيانات الجديدة...")
    
    result = subprocess.run(
        ["python", "manage.py", "check"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"خطأ في الاتصال بقاعدة البيانات: {result.stderr}")
        return False
    
    print("تم الاتصال بقاعدة البيانات بنجاح.")
    return True

def main():
    parser = argparse.ArgumentParser(description="نقل البيانات من قاعدة البيانات المحلية إلى قاعدة البيانات الجديدة على Railway")
    parser.add_argument("--db-url", required=True, help="رابط قاعدة البيانات الكامل")
    parser.add_argument("--db-user", required=True, help="اسم المستخدم")
    parser.add_argument("--db-password", required=True, help="كلمة المرور")
    parser.add_argument("--db-host", required=True, help="اسم المضيف")
    parser.add_argument("--db-port", required=True, help="رقم المنفذ")
    parser.add_argument("--db-name", required=True, help="اسم قاعدة البيانات")
    parser.add_argument("--backup-file", help="اسم ملف النسخة الاحتياطية (اختياري)")
    
    args = parser.parse_args()
    
    # إنشاء نسخة احتياطية
    backup_path = create_backup(args.backup_file)
    if not backup_path:
        sys.exit(1)
    
    # تحديث ملف .env
    update_env_file(
        args.db_url,
        args.db_user,
        args.db_password,
        args.db_host,
        args.db_port,
        args.db_name
    )
    
    # اختبار الاتصال بقاعدة البيانات الجديدة
    if not test_connection():
        print("فشل الاتصال بقاعدة البيانات الجديدة. الرجاء التحقق من بيانات الاتصال.")
        sys.exit(1)
    
    # استعادة النسخة الاحتياطية في قاعدة البيانات الجديدة
    if not restore_backup_to_railway(backup_path):
        print("فشل استعادة النسخة الاحتياطية. الرجاء التحقق من الأخطاء.")
        sys.exit(1)
    
    print("تم نقل البيانات بنجاح إلى قاعدة البيانات الجديدة على Railway.")

if __name__ == "__main__":
    main()
