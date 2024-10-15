from celery import Celery
from celery.schedules import crontab
import os

app = Celery("backend", broker="amqp://guest:guest@147.79.102.115:5672//")
# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

#app = Celery("backend")

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task
def print_numbers():
    from base.tasks import print_numbers
    print_numbers()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute="*"),  # Run every minute
        print_numbers.s(),  # Task to execute
        name="print numbers every minute",
    )
