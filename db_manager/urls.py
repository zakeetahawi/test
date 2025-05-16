from django.urls import path
from . import views

app_name = 'db_manager'

urlpatterns = [
    # صفحة الإعداد الأولي
    path('setup/', views.setup_view, name='setup'),
    path('setup/<uuid:token>/', views.setup_with_token, name='setup_with_token'),

    # إدارة قواعد البيانات
    path('', views.database_list, name='database_list'),
    path('create/', views.database_create, name='database_create'),
    path('edit/<int:pk>/', views.database_edit, name='database_edit'),
    path('delete/<int:pk>/', views.database_delete, name='database_delete'),
    path('set-default/<int:pk>/', views.database_set_default, name='database_set_default'),
    path('test-connection/<int:pk>/', views.database_test_connection, name='database_test_connection'),
    path('test-current-connection/', views.test_current_database_connection, name='test_current_connection'),

    # النسخ الاحتياطية
    path('backups/', views.backup_list, name='backup_list'),
    path('backups/create/', views.backup_create, name='backup_create'),
    path('backups/download/<int:pk>/', views.backup_download, name='backup_download'),
    path('backups/restore/<int:pk>/', views.backup_restore, name='backup_restore'),
    path('backups/delete/<int:pk>/', views.backup_delete, name='backup_delete'),

    # استيراد وتصدير
    path('import/', views.database_import, name='database_import'),
    path('export/', views.database_export, name='database_export'),
    path('import/status/<int:pk>/', views.import_status, name='import_status'),
    path('import/from-file/', views.import_data_from_file, name='import_data_from_file'),
    path('import/direct/', views.direct_import_form, name='direct_import_form'),

    # رموز الإعداد
    path('tokens/', views.token_list, name='token_list'),
    path('tokens/create/', views.token_create, name='token_create'),
    path('tokens/delete/<int:pk>/', views.token_delete, name='token_delete'),
]
