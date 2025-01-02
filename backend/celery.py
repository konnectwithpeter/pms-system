from celery import Celery
from celery.schedules import crontab
import os

#app = Celery("backend", broker="amqp://guest:guest@147.79.102.115:5672//")
# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-recurring-invoices': {
        'task': 'management.tasks.generate_and_email_invoices',
        'schedule': 300.0,  # every 2 minutes
    },
}



