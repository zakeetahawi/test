from django.urls import path
from . import views

app_name = 'installations'

urlpatterns = [
    # Dashboard
    path('', views.InstallationDashboardView.as_view(), name='dashboard'),
    
    # Installation URLs
    path('create/', views.InstallationCreateView.as_view(), name='installation_create'),
    # Transport URLs
    path('transport/', views.TransportListView.as_view(), name='transport_list'),
    path('transport/create/', views.TransportCreateView.as_view(), name='transport_create'),
    path('transport/<int:pk>/', views.TransportDetailView.as_view(), name='transport_detail'),
    path('transport/<int:pk>/update/', views.TransportUpdateView.as_view(), name='transport_update'),
    path('transport/<int:pk>/delete/', views.TransportDeleteView.as_view(), name='transport_delete'),
]
