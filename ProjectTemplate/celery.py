import os

from celery import Celery

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ProjectTemplate.settings")

app = Celery("ProjectTemplate")

# Load settings from Django
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_pool_limit = 2
app.conf.broker_url = app.conf.broker_url or os.getenv("REDIS_URL")

# Discover tasks.py files in all apps automatically
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Periodic task schedule
app.conf.beat_schedule = {
    # "send-ticket-auto-response": {
    #     "task": "Main.tasks.fetch_breet_rates",
    #     "schedule": timedelta(minutes=1),
    # },
    # ...
}
