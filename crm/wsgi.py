"""
WSGI config for CRM project.
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# تهيئة تطبيق WSGI
application = get_wsgi_application()

# إضافة دعم WhiteNoise للملفات الثابتة
application = WhiteNoise(application)
