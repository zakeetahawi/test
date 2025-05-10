import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# Create the Celery app
app = Celery('crm')

# Load the celery config module directly
app.config_from_object('crm.celeryconfig')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
