"""
مسارات وحدة استيراد وتصدير البيانات
"""

from django.urls import path
from . import views

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.dashboard, name='dashboard'),
    
    # استيراد البيانات
    path('import/', views.import_data, name='import_data'),
    
    # تصدير البيانات
    path('export/', views.export_data, name='export_data'),
    
    # سجلات الاستيراد/التصدير
    path('logs/', views.log_list, name='log_list'),
    path('logs/<int:pk>/', views.log_detail, name='log_detail'),
    
    # قوالب الاستيراد
    path('templates/', views.template_list, name='template_list'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/download/', views.template_download, name='template_download'),
]
