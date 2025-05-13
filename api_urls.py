from django.urls import path
from . import api_views

urlpatterns = [
    # Dashboard
    path('dashboard/stats/', api_views.dashboard_stats, name='api_dashboard_stats'),
    
    # Customers
    path('customers/', api_views.customer_list, name='api_customer_list'),
    path('customers/<int:pk>/', api_views.customer_detail, name='api_customer_detail'),
    path('customers/categories/', api_views.customer_categories, name='api_customer_categories'),
    
    # Orders
    path('orders/', api_views.order_list, name='api_order_list'),
    path('orders/<int:pk>/', api_views.order_detail, name='api_order_detail'),
    path('orders/stats/', api_views.order_stats, name='api_order_stats'),
    
    # Inspections
    path('inspections/', api_views.inspection_list, name='api_inspection_list'),
    path('inspections/<int:pk>/', api_views.inspection_detail, name='api_inspection_detail'),
    path('inspections/stats/', api_views.inspection_stats, name='api_inspection_stats'),
    
    # Installations
    path('installations/', api_views.installation_list, name='api_installation_list'),
    path('installations/<int:pk>/', api_views.installation_detail, name='api_installation_detail'),
    path('installations/stats/', api_views.installation_stats, name='api_installation_stats'),
    
    # Inventory
    path('inventory/products/', api_views.inventory_products, name='api_inventory_products'),
    path('inventory/products/<int:pk>/', api_views.inventory_product_detail, name='api_inventory_product_detail'),
    path('inventory/categories/', api_views.inventory_categories, name='api_inventory_categories'),
    path('inventory/stats/', api_views.inventory_stats, name='api_inventory_stats'),
    path('inventory/stock-movements/', api_views.inventory_stock_movements, name='api_inventory_stock_movements'),
    path('inventory/stock-movements/<int:product_id>/', api_views.inventory_product_stock_movements, name='api_inventory_product_stock_movements'),
    
    # Users
    path('users/', api_views.user_list, name='api_user_list'),
    path('users/<int:pk>/', api_views.user_detail, name='api_user_detail'),
    
    # Tasks
    path('tasks/', api_views.task_list, name='api_task_list'),
    path('tasks/<int:pk>/', api_views.task_detail, name='api_task_detail'),
    
    # Reports
    path('reports/sales/', api_views.sales_report, name='api_sales_report'),
    path('reports/inventory/', api_views.inventory_report, name='api_inventory_report'),
    
    # Settings
    path('settings/', api_views.settings_get, name='api_settings_get'),
    path('settings/update/', api_views.settings_update, name='api_settings_update'),
]
