from __future__ import absolute_import, unicode_literals
import os
import django
from celery import Celery
from datetime import timedelta
from celery.schedules import  crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carmagnole.settings')
django.setup()

app = Celery('carmagnole')


app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)
app.autodiscover_tasks()

app.conf.result_expires = timedelta(hours=8)
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_transport_options = {'visibility_timeout': 28800}
app.conf.broker_heartbeat = 10
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_retry = True
app.conf.broker_connection_max_retries = None  
app.conf.broker_connection_retry_delay = 5
app.conf.worker_max_tasks_per_child = 50

app.conf.beat_schedule = {
    'send-newsletter-everyday': {
        'task': 'mails.tasks.send_newsletter',
        'schedule': crontab(hour='4', minute="30"),  
    },
    'clear-expired-redis-keys-every-six-hours': {
        'task': 'utils.tasks.clear_expired_redis_keys',
        'schedule': crontab(hour='*/4', minute='0'),  
    },
}
