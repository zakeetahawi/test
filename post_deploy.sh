#!/bin/bash

# تشغيل الهجرات
python manage.py migrate

# إنشاء الأقسام الأساسية
python manage.py create_core_departments

# إنشاء مستخدم المشرف الافتراضي إذا لم يكن موجودًا
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

# جمع الملفات الثابتة
python manage.py collectstatic --noinput
