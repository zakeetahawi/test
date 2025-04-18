from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report URLs
    path('', views.ReportListView.as_view(), name='report_list'),
# alias for compatibility
path('reports/', views.ReportListView.as_view(), name='reports_list'),
    path('create/', views.ReportCreateView.as_view(), name='report_create'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('<int:pk>/update/', views.ReportUpdateView.as_view(), name='report_update'),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report_delete'),
    path('<int:pk>/save-result/', views.save_report_result, name='save_report_result'),
    
    # Report Schedule URLs
    path('<int:pk>/schedule/create/', views.ReportScheduleCreateView.as_view(), name='schedule_create'),
    path('schedule/<int:pk>/update/', views.ReportScheduleUpdateView.as_view(), name='schedule_update'),
    path('schedule/<int:pk>/delete/', views.ReportScheduleDeleteView.as_view(), name='schedule_delete'),
]
