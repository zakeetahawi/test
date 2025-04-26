from django.urls import path
from . import views
from .views import InventoryDashboardView

app_name = 'inventory'

urlpatterns = [
    # Main inventory home
    path('', views.inventory_home, name='inventory_home'),
    # Dashboard
    path('dashboard/', InventoryDashboardView.as_view(), name='dashboard'),

    # Customer Orders CRUD
    path('customer-orders/', views.customer_order_list, name='customer_order_list'),
    path('customer-orders/create/', views.customer_order_create, name='customer_order_create'),
    path('customer-orders/<int:pk>/', views.customer_order_detail, name='customer_order_detail'),
    path('customer-orders/<int:pk>/update/', views.customer_order_update, name='customer_order_update'),
    path('customer-orders/<int:pk>/delete/', views.customer_order_delete, name='customer_order_delete'),

    # Category CRUD
    path('categories/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:pk>/update/', views.category_update, name='category_update'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Supplier CRUD
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('supplier/create/', views.supplier_create, name='supplier_create'),
    path('supplier/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('supplier/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Warehouse CRUD
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouse/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouse/<int:pk>/update/', views.warehouse_update, name='warehouse_update'),
    path('warehouse/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),

    # Purchase Order Views
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/update/', views.purchase_order_update, name='purchase_order_update'),
    path('purchase-orders/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    # path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_confirm_delete'),

    # Supply Order Views
    path('supply-orders/', views.supply_order_list, name='supply_order_list'),
    path('supply-orders/create/', views.supply_order_create, name='supply_order_create'),
    path('supply-orders/<int:pk>/', views.supply_order_detail, name='supply_order_detail'),
    path('supply-orders/<int:pk>/update/', views.supply_order_update, name='supply_order_update'),
    path('supply-orders/<int:pk>/delete/', views.supply_order_delete, name='supply_order_delete'),

    # Advanced Reports
    path('advanced-reports/', views.advanced_reports, name='advanced_reports'),
    path('product-report/', views.product_report, name='product_report'),
    path('supplier-report/', views.supplier_report, name='supplier_report'),
    path('warehouse-report/', views.warehouse_report, name='warehouse_report'),
    # Supply Order Report
    path('supply-orders/report/', views.supply_order_report, name='supply_order_report'),

    # Stock Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/create/', views.product_create, name='product_create'),
    path('product/<int:pk>/update/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('product/<int:product_pk>/transaction/create/', views.transaction_create, name='transaction_create'),

    # API endpoints
    path('api/products/<int:pk>/', views.product_api_detail, name='product_api_detail'),
    path('api/products/', views.product_api_list, name='product_api_list'),
]

