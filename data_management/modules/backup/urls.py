"""
مسارات وحدة النسخ الاحتياطي
"""

from django.urls import path
from . import views

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.dashboard, name='backup_dashboard'),
    
    # النسخ الاحتياطي
    path('create/', views.create_backup, name='create_backup'),
    path('list/', views.backup_list, name='backup_list'),
    path('<int:pk>/', views.backup_detail, name='backup_detail'),
    path('<int:pk>/download/', views.backup_download, name='backup_download'),
    path('<int:pk>/restore/', views.restore_backup, name='restore_backup'),
    path('<int:pk>/delete/', views.delete_backup, name='delete_backup'),
    
    # إعدادات Google Sheets
    path('google-sheets/', views.google_sheets_config, name='google_sheets_config'),
    path('google-sheets/sync/', views.sync_google_sheets, name='sync_google_sheets'),
    path('google-sheets/logs/', views.sync_logs, name='sync_logs'),
]
