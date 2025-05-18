-- منح صلاحيات إضافية للمستخدم
ALTER USER crm_user WITH SUPERUSER;

-- منح صلاحيات على المخطط العام
\c crm_system
GRANT ALL ON SCHEMA public TO crm_user;
ALTER SCHEMA public OWNER TO crm_user;
