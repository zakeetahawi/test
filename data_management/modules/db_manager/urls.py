"""
مسارات وحدة إدارة قواعد البيانات
"""

from django.urls import path
from . import views

app_name = 'db_manager'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.dashboard, name='db_dashboard'),

    # إدارة قواعد البيانات
    path('databases/', views.database_list, name='database_list'),
    path('databases/create/', views.database_create, name='database_create'),
    path('databases/<int:pk>/', views.database_detail, name='database_detail'),
    path('databases/<int:pk>/update/', views.database_update, name='database_update'),
    path('databases/<int:pk>/delete/', views.database_delete, name='database_delete'),
    path('databases/<int:pk>/set-default/', views.database_set_default, name='database_set_default'),
    path('databases/<int:pk>/set-active/', views.database_set_active, name='database_set_active'),
    path('databases/reload/', views.database_reload, name='database_reload'),
    path('databases/reset-settings/', views.reset_database_settings, name='reset_database_settings'),
    path('test-current-connection/', views.test_current_database_connection, name='test_current_connection'),

    # النسخ الاحتياطي والاستعادة
    path('backups/', views.backup_list, name='db_backup_list'),
    path('backups/create/', views.backup_create, name='db_backup_create'),
    path('backups/<int:pk>/', views.backup_detail, name='db_backup_detail'),
    path('backups/<int:pk>/download/', views.backup_download, name='db_backup_download'),
    path('backups/<int:pk>/restore/', views.backup_restore, name='db_backup_restore'),
    path('backups/<int:pk>/delete/', views.backup_delete, name='db_backup_delete'),

    # استيراد البيانات
    path('import/', views.database_import, name='db_import'),
    path('import/', views.database_import, name='db_import_form'),  # إضافة اسم مسار بديل
    path('import/<int:pk>/', views.import_detail, name='db_import_detail'),
    path('import/<int:pk>/status/', views.import_status, name='import_status'),

    # تصدير البيانات
    path('export/', views.database_export, name='db_export'),

    # إعداد النظام
    path('setup/', views.setup, name='db_setup'),
    path('setup/<uuid:token>/', views.setup_with_token, name='db_setup_with_token'),
    path('setup/create-token/', views.create_setup_token, name='create_setup_token'),
]
