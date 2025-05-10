from celery.schedules import crontab
from datetime import timedelta
import os

# Using a single SQLite database for both broker and result backend
sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'celery.sqlite')
broker_url = f'sqla+sqlite:///{sqlite_path}'
result_backend = f'db+sqlite:///{sqlite_path}'

# مهام التسعير الديناميكي وجدولتها
beat_schedule = {
    'update-dynamic-prices': {
        'task': 'orders.tasks.pricing_tasks.update_dynamic_prices',
        'schedule': timedelta(minutes=15),
        'options': {
            'expires': 14 * 60
        }
    },
    'cleanup-expired-pricing-rules': {
        'task': 'orders.tasks.pricing_tasks.cleanup_expired_pricing_rules',
        'schedule': crontab(hour=0, minute=0),
    },
    'notify-price-changes': {
        'task': 'orders.tasks.pricing_tasks.notify_price_changes',
        'schedule': timedelta(hours=1),
    }
}

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Riyadh'
enable_utc = True

# Windows-specific settings
worker_pool = 'solo'
broker_connection_retry = True
broker_connection_max_retries = None
worker_cancel_long_running_tasks_on_connection_loss = True