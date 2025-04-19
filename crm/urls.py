from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views_health import health_check

urlpatterns = [
    path('health-check/', health_check, name='health_check'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('factory/', include('factory.urls')),
    path('inventory/', include('inventory.urls')),
    path('orders/', include('orders.urls')),
    path('reports/', include('reports.urls')),
    path('inspections/', include('inspections.urls')),
    path('installations/', include('installations.urls')),
    path('data-import-export/', include('data_import_export.urls')),
    # API endpoints
    path('api/accounts/', include('accounts.urls', namespace='api_accounts')),
    path('api/customers/', include('customers.urls', namespace='api_customers')),
    path('api/factory/', include('factory.urls', namespace='api_factory')),
    path('api/inventory/', include('inventory.urls', namespace='api_inventory')),
    path('api/orders/', include('orders.urls', namespace='api_orders')),
    path('api/reports/', include('reports.urls', namespace='api_reports')),
    path('api/inspections/', include('inspections.urls', namespace='api_inspections')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
