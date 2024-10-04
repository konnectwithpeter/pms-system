from celery import Celery
from celery.schedules import crontab

app = Celery("backend", broker="amqp://guest:guest@rabbitmq//")

app.conf.result_backend = "rpc://"

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from base.tasks import (
        send_reminders
    )  # Move here

    # sender.add_periodic_task(30.0, test.s('world'), name='test every 30 seconds')crontab(hour=0, minute=0, day_of_month='1')

    # sender.add_periodic_task(
    #     60.0, generate_monthly_bills.s(), name="generate monthly bills on 1st"
    # )
    # sender.reset_water_bills(
    #     60.0, generate_monthly_bills.s(), name="reset water meter on 1st"
    # )
