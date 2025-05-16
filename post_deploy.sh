#!/bin/bash

# نسخ ملف .env.railway إلى .env إذا كان موجودًا
if [ -f .env.railway ]; then
    echo "نسخ ملف .env.railway إلى .env..."
    cp .env.railway .env
fi

# طباعة معلومات قاعدة البيانات للتشخيص
echo "معلومات قاعدة البيانات:"
echo "DATABASE_URL: $DATABASE_URL"

# تشغيل الهجرات
echo "تشغيل الهجرات..."
python manage.py migrate

# إنشاء الأقسام الأساسية
echo "إنشاء الأقسام الأساسية..."
python manage.py create_core_departments

# إنشاء مستخدم المشرف الافتراضي إذا لم يكن موجودًا
echo "إنشاء مستخدم المشرف الافتراضي..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

# جمع الملفات الثابتة
echo "جمع الملفات الثابتة..."
python manage.py collectstatic --noinput

echo "اكتمل النشر بنجاح!"
