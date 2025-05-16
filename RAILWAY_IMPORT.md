# استيراد البيانات إلى قاعدة بيانات Railway

هذا الملف يشرح كيفية استيراد البيانات من النسخة الاحتياطية المحلية إلى قاعدة بيانات Railway.

## الخطوات

### 1. التأكد من وجود نسخة احتياطية

تأكد من وجود نسخة احتياطية في مجلد `backups`. يمكنك إنشاء نسخة احتياطية جديدة باستخدام الأمر:

```bash
python manage.py dbbackup
```

### 2. الحصول على رابط قاعدة البيانات على Railway

1. قم بتسجيل الدخول إلى حساب Railway الخاص بك على [railway.app](https://railway.app/)
2. انتقل إلى مشروعك
3. انقر على قاعدة البيانات PostgreSQL
4. انقر على تبويب "Connect" (اتصال)
5. انسخ رابط الاتصال (DATABASE_URL)

### 3. استيراد البيانات باستخدام السكريبت

استخدم السكريبت `import_to_railway.py` لاستيراد البيانات:

```bash
python import_to_railway.py --db-url "postgresql://postgres:password@containers-us-west-1.railway.app:5432/railway" --backup-file "backups/default-Zakee_VM-2025-05-16-204243.psql.bin" --format "psql"
```

استبدل القيم بالقيم الفعلية:
- `--db-url`: رابط قاعدة البيانات على Railway
- `--backup-file`: مسار ملف النسخة الاحتياطية
- `--format`: تنسيق ملف النسخة الاحتياطية (psql أو json)

### 4. التحقق من النتائج

بعد اكتمال عملية الاستيراد، يمكنك التحقق من النتائج عن طريق:

1. الوصول إلى التطبيق على Railway
2. تسجيل الدخول باستخدام اسم المستخدم وكلمة المرور (admin/admin)
3. التحقق من أن البيانات موجودة

## استكشاف الأخطاء وإصلاحها

إذا واجهت أي مشاكل أثناء عملية الاستيراد، فيمكنك:

1. التحقق من سجلات الأخطاء في الطرفية
2. التأكد من صحة رابط قاعدة البيانات
3. التأكد من أن ملف النسخة الاحتياطية موجود وصالح
4. التأكد من أن لديك الصلاحيات اللازمة للوصول إلى قاعدة البيانات

## استيراد البيانات يدويًا

إذا واجهت مشاكل مع السكريبت، يمكنك استيراد البيانات يدويًا باستخدام أمر `pg_restore`:

```bash
set PGPASSWORD=your_password
pg_restore -h your_host -p your_port -U your_user -d your_db -v --no-owner --no-privileges --clean your_backup_file
```

أو باستخدام أمر `loaddata` لملفات JSON:

```bash
set DATABASE_URL=your_db_url
python manage.py loaddata your_json_file
```
