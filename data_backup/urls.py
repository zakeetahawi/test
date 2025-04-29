from django.urls import path
from . import views

app_name = 'data_backup'

urlpatterns = [
    path('', views.backup_dashboard, name='dashboard'),
    path('sync-now/', views.sync_now, name='sync_now'),
    path('import-from-sheets/', views.import_from_sheets, name='import_from_sheets'),
]