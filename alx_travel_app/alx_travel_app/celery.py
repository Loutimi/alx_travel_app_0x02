import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

# Create Celery app
app = Celery('alx_travel_app')

# Load settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks across all apps
app.autodiscover_tasks()
