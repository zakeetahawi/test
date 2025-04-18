from django.urls import path
from . import views

app_name = 'inspections'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('', views.InspectionListView.as_view(), name='inspection_list'),
    # alias for compatibility
    path('inspections/', views.InspectionListView.as_view(), name='inspections_list'),
    path('list/', views.InspectionListView.as_view(), name='inspection_list'),
    path('create/', views.InspectionCreateView.as_view(), name='inspection_create'),
    path('<int:pk>/', views.InspectionDetailView.as_view(), name='inspection_detail'),
    path('<int:pk>/update/', views.InspectionUpdateView.as_view(), name='inspection_update'),
    path('<int:pk>/delete/', views.InspectionDeleteView.as_view(), name='inspection_delete'),
    
    # Evaluations
    path('<int:inspection_pk>/evaluate/', views.EvaluationCreateView.as_view(), name='evaluation_create'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:inspection_pk>/notify/', views.NotificationCreateView.as_view(), name='notification_create'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
