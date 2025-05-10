from django.urls import path
from . import views

app_name = 'installations'

urlpatterns = [
    # Dashboard
    path('', views.InstallationDashboardView.as_view(), name='dashboard'),
    
    # Installation URLs
    path('list/', views.InstallationListView.as_view(), name='installation_list'),
    path('create/', views.InstallationCreateView.as_view(), name='installation_create'),
    path('<int:pk>/', views.InstallationDetailView.as_view(), name='installation_detail'),
    path('<int:pk>/update/', views.InstallationUpdateView.as_view(), name='installation_update'),
    path('<int:pk>/delete/', views.InstallationDeleteView.as_view(), name='installation_delete'),
]
