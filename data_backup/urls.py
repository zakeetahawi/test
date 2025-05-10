from django.urls import path
from . import views

app_name = 'data_backup'

urlpatterns = [
    path('dashboard/', views.backup_dashboard, name='dashboard'),
    path('sync/now/', views.sync_now, name='sync_now'),
    path('import-from-sheets/', views.import_from_sheets, name='import_from_sheets'),
    path('update-sync-interval/', views.update_sync_interval, name='update_sync_interval'),
    path('cloud-storage/settings/', views.cloud_storage_settings, name='cloud_storage_settings'),
    path('cloud-storage/test/', views.test_cloud_storage, name='test_cloud_storage'),
    path('backup/metrics/', views.backup_metrics, name='backup_metrics'),
    path('backup/reports/<str:report_type>/', views.backup_reports, name='backup_reports'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/restore/', views.restore_backup, name='restore_backup'),
    path('backup/restore/<int:backup_id>/', views.restore_backup, name='restore_backup'),
]