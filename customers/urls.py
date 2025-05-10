from django.urls import path
from . import views
from .views import CustomerDashboardView

app_name = 'customers'

urlpatterns = [
    # Dashboard as main page
    path('', CustomerDashboardView.as_view(), name='dashboard'),
    
    # Customer Views
    path('list/', views.customer_list, name='customer_list'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/update/', views.customer_update, name='customer_update'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Note Management
    path('<int:pk>/add-note/', views.add_customer_note, name='add_note'),
    path('<int:customer_pk>/notes/<int:note_pk>/delete/', views.delete_customer_note, name='delete_note'),
    
    # Category Management 
    path('categories/', views.customer_category_list, name='category_list'),
    path('categories/add/', views.add_customer_category, name='add_category'),
]
