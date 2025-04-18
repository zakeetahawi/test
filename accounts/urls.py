from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Notification URLs
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Company Info URLs
    path('company-info/', views.company_info_view, name='company_info'),
    
    # Form Field Management URLs
    path('form-fields/', views.form_field_list, name='form_field_list'),
    path('form-fields/create/', views.form_field_create, name='form_field_create'),
    path('form-fields/<int:pk>/update/', views.form_field_update, name='form_field_update'),
    path('form-fields/<int:pk>/delete/', views.form_field_delete, name='form_field_delete'),
    path('form-fields/<int:pk>/toggle/', views.toggle_form_field, name='toggle_form_field'),
]
