from django.urls import path
from . import views
from .views import FactoryDashboardView

app_name = 'factory'

urlpatterns = [
    path('dashboard/', FactoryDashboardView.as_view(), name='dashboard'),
    # Dashboard
    path('', views.factory_list, name='factory_list'),
    # alias for compatibility
    path('factory/', views.factory_list, name='factory_main'),
    
    # Production Lines
    path('production-lines/', views.production_line_list, name='production_line_list'),
    path('production-lines/<int:pk>/', views.production_line_detail, name='production_line_detail'),
    path('production-lines/create/', views.production_line_create, name='production_line_create'),
    path('production-lines/<int:pk>/update/', views.production_line_update, name='production_line_update'),
    path('production-lines/<int:pk>/delete/', views.production_line_delete, name='production_line_delete'),
    
    # Production Orders
    path('production-orders/', views.production_order_list, name='production_order_list'),
    path('production-orders/<int:pk>/', views.production_order_detail, name='production_order_detail'),
    path('production-orders/create/', views.production_order_create, name='production_order_create'),
    path('production-orders/<int:pk>/update/', views.production_order_update, name='production_order_update'),
    path('production-orders/<int:pk>/delete/', views.production_order_delete, name='production_order_delete'),
    
    # Production Stages
    path('production-orders/<int:order_pk>/stages/create/', views.production_stage_create, name='production_stage_create'),
    path('production-stages/<int:pk>/update/', views.production_stage_update, name='production_stage_update'),
    path('production-stages/<int:pk>/delete/', views.production_stage_delete, name='production_stage_delete'),
    
    # Production Issues
    path('issues/', views.production_issue_list, name='production_issue_list'),
    path('issues/<int:pk>/', views.production_issue_detail, name='production_issue_detail'),
    path('production-orders/<int:order_pk>/issues/create/', views.production_issue_create, name='production_issue_create'),
    path('issues/<int:pk>/update/', views.production_issue_update, name='production_issue_update'),
]
