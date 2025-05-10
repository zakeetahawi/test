# دليل تثبيت وإعداد بيئة التطوير

## المتطلبات الأساسية

1. **Python**
   - الإصدار: 3.8 أو أحدث
   - تأكد من تثبيت pip

2. **Node.js**
   - الإصدار: 16.x أو أحدث
   - تأكد من تثبيت npm

3. **PostgreSQL**
   - الإصدار: 13 أو أحدث

4. **Redis**
   - الإصدار: 7.0 أو أحدث

## خطوات الإعداد

### 1. إعداد قاعدة البيانات
```sql
CREATE DATABASE crm_db;
CREATE USER crm_user WITH PASSWORD 'your_password';
ALTER ROLE crm_user SET client_encoding TO 'utf8';
ALTER ROLE crm_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE crm_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;
```

### 2. إعداد البيئة الافتراضية وتثبيت التبعيات الخلفية
```bash
# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# تثبيت التبعيات
pip install -r requirements.txt
```

### 3. إعداد ملف البيئة (.env)
```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://crm_user:your_password@localhost:5432/crm_db
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. تهيئة قاعدة البيانات
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. إعداد الواجهة الأمامية
```bash
# الانتقال لمجلد الواجهة الأمامية
cd frontend

# تثبيت التبعيات
npm install

# إنشاء ملف البيئة
echo "VITE_API_URL=http://localhost:8000" > .env
```

## تشغيل التطبيق

### 1. تشغيل الخادم الخلفي
```bash
# تشغيل Redis
redis-server

# تشغيل Celery (في نافذة طرفية جديدة)
celery -A crm worker -l info

# تشغيل خادم التطوير (في نافذة طرفية جديدة)
python manage.py runserver
```

### 2. تشغيل الواجهة الأمامية
```bash
# في مجلد frontend
npm run dev
```

## اختبار التثبيت

1. **فحص الخادم الخلفي**
   - افتح http://localhost:8000/admin
   - سجل الدخول باستخدام حساب المشرف

2. **فحص الواجهة الأمامية**
   - افتح http://localhost:5173
   - تأكد من ظهور صفحة تسجيل الدخول

3. **فحص WebSocket**
   - تأكد من اتصال WebSocket في وحدة تحكم المتصفح
   - تحقق من تحديثات التركيب المباشرة

## استكشاف الأخطاء وإصلاحها

### مشاكل قاعدة البيانات
```bash
# إعادة تهيئة قاعدة البيانات
python manage.py flush
python manage.py migrate
```

### مشاكل التبعيات
```bash
# تحديث التبعيات الخلفية
pip install --upgrade -r requirements.txt

# تحديث تبعيات الواجهة الأمامية
npm update
```

### مشاكل Redis/Celery
```bash
# فحص حالة Redis
redis-cli ping

# تنظيف صف Celery
celery -A crm purge
```

## النسخ الاحتياطي

### 1. قاعدة البيانات
```bash
# إنشاء نسخة احتياطية
python manage.py dbbackup

# استعادة نسخة احتياطية
python manage.py dbrestore
```

### 2. الملفات
```bash
# نسخ احتياطي للملفات
python manage.py mediabackup

# استعادة الملفات
python manage.py mediarestore
```

## تحديث النظام

### 1. تحديث الكود
```bash
git pull origin main
```

### 2. تحديث التبعيات
```bash
pip install -r requirements.txt
npm install
```

### 3. تحديث قاعدة البيانات
```bash
python manage.py migrate
```

### 4. إعادة تشغيل الخدمات
```bash
# إعادة تشغيل Celery
celery -A crm worker -l info

# إعادة تشغيل الخادم
python manage.py runserver
