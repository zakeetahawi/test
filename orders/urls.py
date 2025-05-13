from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import OrdersDashboardView

app_name = 'orders'

router = DefaultRouter()

urlpatterns = [
    # Dashboard as main page
    path('', OrdersDashboardView.as_view(), name='dashboard'),

    # Order Views
    path('list/', views.order_list, name='order_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('create/', views.order_create, name='order_create'),
    path('<int:pk>/update/', views.order_update, name='order_update'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Payment Views
    path('payment/<int:order_pk>/create/', views.payment_create, name='payment_create'),
    path('payment/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # Salesperson Views
    path('salesperson/', views.salesperson_list, name='salesperson_list'),

    # Update Order Status
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_status'),



    # API Dynamic Pricing
    path('api/', include(router.urls)),
]
