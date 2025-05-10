import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.core.serializers import serialize

# Set UTF-8 as the default encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Get all model data excluding specified models
data = serialize('json', 
    [obj for obj in django.apps.apps.get_models() 
     for obj in obj.objects.all()
     if obj._meta.app_label + '.' + obj._meta.model_name 
     not in ['auth.permission', 'contenttypes.contenttype', 'admin.logentry', 'sessions.session']],
    ensure_ascii=False
)

# Write to file with UTF-8 encoding
with open('data.json', 'w', encoding='utf-8') as f:
    f.write(data)