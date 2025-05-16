#!/usr/bin/env python
"""
سكريبت لاستيراد البيانات من النسخة الاحتياطية إلى قاعدة البيانات الجديدة على Railway
"""
import os
import sys
import subprocess
import argparse
import time
from datetime import datetime

def upload_backup_to_railway(backup_file, railway_db_url):
    """رفع النسخة الاحتياطية إلى قاعدة البيانات على Railway"""
    print(f"رفع النسخة الاحتياطية {backup_file} إلى قاعدة البيانات على Railway...")
    
    # استخراج معلومات الاتصال من رابط قاعدة البيانات
    # مثال: postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway
    db_url_parts = railway_db_url.replace("postgresql://", "").split("@")
    user_pass = db_url_parts[0].split(":")
    host_port_db = db_url_parts[1].split("/")
    host_port = host_port_db[0].split(":")
    
    db_user = user_pass[0]
    db_password = user_pass[1]
    db_host = host_port[0]
    db_port = host_port[1]
    db_name = host_port_db[1]
    
    # إعداد متغيرات البيئة للاتصال بقاعدة البيانات
    env = os.environ.copy()
    env["PGPASSWORD"] = db_password
    
    # استخدام pg_restore لاستيراد النسخة الاحتياطية
    command = [
        "pg_restore",
        "-h", db_host,
        "-p", db_port,
        "-U", db_user,
        "-d", db_name,
        "-v",  # وضع التفصيل
        "--no-owner",  # تجاهل معلومات المالك
        "--no-privileges",  # تجاهل معلومات الصلاحيات
        "--clean",  # حذف الكائنات الموجودة قبل إنشائها
        backup_file
    ]
    
    print(f"تنفيذ الأمر: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"خطأ في استيراد النسخة الاحتياطية: {result.stderr}")
            return False
        
        print("تم استيراد النسخة الاحتياطية بنجاح.")
        return True
    except Exception as e:
        print(f"حدث خطأ أثناء استيراد النسخة الاحتياطية: {str(e)}")
        return False

def import_json_to_railway(json_file, railway_db_url):
    """استيراد ملف JSON إلى قاعدة البيانات على Railway"""
    print(f"استيراد ملف JSON {json_file} إلى قاعدة البيانات على Railway...")
    
    # تعيين متغير البيئة DATABASE_URL
    os.environ["DATABASE_URL"] = railway_db_url
    
    # استخدام loaddata لاستيراد ملف JSON
    command = [
        "python", "manage.py", "loaddata",
        json_file
    ]
    
    print(f"تنفيذ الأمر: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"خطأ في استيراد ملف JSON: {result.stderr}")
            return False
        
        print("تم استيراد ملف JSON بنجاح.")
        return True
    except Exception as e:
        print(f"حدث خطأ أثناء استيراد ملف JSON: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="استيراد البيانات من النسخة الاحتياطية إلى قاعدة البيانات الجديدة على Railway")
    parser.add_argument("--db-url", required=True, help="رابط قاعدة البيانات على Railway")
    parser.add_argument("--backup-file", required=True, help="مسار ملف النسخة الاحتياطية")
    parser.add_argument("--format", choices=["psql", "json"], default="psql", help="تنسيق ملف النسخة الاحتياطية (psql أو json)")
    
    args = parser.parse_args()
    
    if args.format == "psql":
        # استيراد النسخة الاحتياطية بتنسيق PostgreSQL
        if not upload_backup_to_railway(args.backup_file, args.db_url):
            sys.exit(1)
    elif args.format == "json":
        # استيراد ملف JSON
        if not import_json_to_railway(args.backup_file, args.db_url):
            sys.exit(1)
    
    print("تم استيراد البيانات بنجاح إلى قاعدة البيانات الجديدة على Railway.")

if __name__ == "__main__":
    main()
