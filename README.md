# نظام الخواجه لإدارة العملاء (CRM)

## نظرة عامة
نظام إدارة العملاء الشامل "الخواجه" مصمم لدعم الشركات في إدارة عملائها، والمبيعات، والإنتاج، والمخزون بكفاءة عالية. النظام يدعم الآن إدارة قواعد البيانات المتعددة وعمليات النسخ الاحتياطي والاستعادة.

## المميزات الرئيسية
- إدارة العملاء
- تتبع الطلبات والمبيعات
- إدارة المخزون
- نظام إنتاج متكامل
- تقارير وإحصائيات متقدمة
- نسخ احتياطي ومزامنة مع Google Sheets
- إدارة قواعد البيانات المتعددة
- استيراد واستعادة قواعد البيانات

## المتطلبات التقنية
- Python 3.11+
- Django 4.2
- PostgreSQL (في الإنتاج)
- Redis (للقنوات والويب سوكت)
- Railway (للنشر)

## إعداد المشروع

### 1. استنساخ المستودع
```bash
git clone https://github.com/yourusername/elkhawaga-crm.git
cd elkhawaga-crm
```

### 2. إنشاء بيئة افتراضية
```bash
python -m venv venv
source venv/bin/activate  # على Linux/macOS
venv\Scripts\activate  # على Windows
```

### 3. تثبيت التبعيات
```bash
pip install -r requirements.txt
```

### 4. قاعدة البيانات

في بيئة التطوير المحلية، يمكنك استخدام SQLite أو PostgreSQL.

#### لاستخدام PostgreSQL محليًا:
```bash
createdb crm_system
```

#### في بيئة الإنتاج (Railway):
يتم إنشاء قاعدة بيانات PostgreSQL تلقائيًا عند إضافة خدمة PostgreSQL إلى مشروعك على Railway.

### 5. الترحيلات
```bash
python manage.py migrate
```
عادةً لن تحتاج إلا إذا غيرت النماذج أو أردت تحديث قاعدة البيانات.

### 6. إنشاء مستخدم مدير (Superuser)
```bash
python manage.py createsuperuser
```
أو يمكنك تسجيل الدخول مباشرة إذا كان لديك مستخدم بالفعل في قاعدة البيانات الحالية.

### 7. تشغيل الخادم
```bash
python manage.py runserver
```

## التكوين
- قم بتعديل `crm/settings.py` لتكوين إعدادات المشروع
- استخدم ملف `.env` لتكوين متغيرات البيئة في بيئة التطوير
- استخدم ملف `.env.production` كمرجع لإعداد متغيرات البيئة في Railway

## النشر على Railway

### 1. إنشاء مشروع جديد على Railway
1. قم بتسجيل الدخول إلى [Railway](https://railway.app/)
2. انقر على "New Project"
3. اختر "Deploy from GitHub repo"
4. حدد مستودع GitHub الخاص بك

### 2. إضافة قاعدة بيانات PostgreSQL
1. في مشروعك على Railway، انقر على "New Service"
2. اختر "Add Database" ثم "PostgreSQL"

### 3. إضافة متغيرات البيئة
1. انتقل إلى تبويب "Variables" في مشروع التطبيق
2. أضف المتغيرات التالية:
   - `SECRET_KEY` = مفتاح سري آمن
   - `DEBUG` = "0"
   - `ALLOWED_HOSTS` = "*.up.railway.app"
   - `ENABLE_SSL_SECURITY` = "true"

### 4. ترحيل البيانات (اختياري)
إذا كنت تريد نقل البيانات من SQLite إلى PostgreSQL:
1. قم بتصدير البيانات من SQLite محليًا:
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
   ```
2. قم باستيراد البيانات إلى PostgreSQL على Railway:
   ```bash
   python manage.py loaddata data.json
   ```

## المساهمة
1. قم بعمل fork للمشروع
2. أنشئ branch جديد (`git checkout -b feature/AmazingFeature`)
3. التزم بتغييراتك (`git commit -m 'Add some AmazingFeature'`)
4. ادفع إلى البرانش (`git push origin feature/AmazingFeature`)
5. افتح طلب سحب

## الترخيص
موزع تحت رخصة MIT. راجع `LICENSE` للمزيد من المعلومات.

## جهات الاتصال
- المطور: Zakee Tahawi
- رابط المشروع: https://github.com/zakeetahawi/test
