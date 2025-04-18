from django.urls import path
from . import views

app_name = 'orders'


urlpatterns = [
    # Order URLs
    path('', views.order_list, name='order_list'),
# alias for compatibility
path('orders/', views.order_list, name='orders_list'),
    path('create/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/update/', views.order_update, name='order_update'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    
    # Payment URLs
    path('<int:order_pk>/payment/create/', views.payment_create, name='payment_create'),
    path('payment/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

]
