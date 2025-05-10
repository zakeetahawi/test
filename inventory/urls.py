from django.urls import path
from . import views
from .views import InventoryDashboardView
from .dashboard_view_append import low_stock_report, stock_movement_report, optimized_product_detail

app_name = 'inventory'

urlpatterns = [
    # Dashboard as main page
    path('', InventoryDashboardView.as_view(), name='dashboard'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/create/', views.product_create, name='product_create'),
    path('product/<int:pk>/update/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('product/<int:product_pk>/transaction/create/', views.transaction_create, name='transaction_create'),
    
    # Dashboard reports
    path('reports/low-stock/', low_stock_report, name='low_stock_report'),
    path('reports/stock-movement/', stock_movement_report, name='stock_movement_report'),
    path('product/<int:product_id>/detail/', optimized_product_detail, name='optimized_product_detail'),
    
    # تعليق الروابط غير المتوفرة حالياً، يمكن إضافتها لاحقاً عند إنشاء الوظائف المقابلة
    # path('reports/product-performance/', product_performance, name='product_performance'),
    # path('reports/expiry/', expiry_report, name='expiry_report'),
]

