import os
from django.core.wsgi import get_wsgi_application
from mangum import Mangum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# Get the Django WSGI application we want to use
application = get_wsgi_application()

# Create a Mangum adapter for ASGI/WSGI support
handler = Mangum(application, lifespan="off")
