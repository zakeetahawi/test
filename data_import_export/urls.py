from django.urls import path
from . import views

app_name = 'data_import_export'

urlpatterns = [
    # Dashboard
    path('', views.import_export_dashboard, name='dashboard'),
    
    # Import
    path('import/', views.import_data, name='import_data'),
    
    # Export
    path('export/', views.export_data, name='export_data'),
    
    # Import/Export Logs
    path('logs/', views.import_log_list, name='import_log_list'),
    path('logs/<int:pk>/', views.import_log_detail, name='import_log_detail'),
    
    # Import Templates
    path('templates/', views.import_template_list, name='import_template_list'),
    path('templates/create/', views.import_template_create, name='import_template_create'),
    path('templates/<int:pk>/update/', views.import_template_update, name='import_template_update'),
    path('templates/<int:pk>/delete/', views.import_template_delete, name='import_template_delete'),
    path('templates/<int:pk>/download/', views.download_import_template, name='download_import_template'),
]
