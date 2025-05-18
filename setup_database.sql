-- إنشاء قاعدة البيانات
CREATE DATABASE crm_system;

-- إنشاء المستخدم
CREATE USER crm_user WITH PASSWORD '5525';

-- منح الصلاحيات
GRANT ALL PRIVILEGES ON DATABASE crm_system TO crm_user;
ALTER USER crm_user CREATEDB;
