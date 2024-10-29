from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta
from celery.schedules import  crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carmagnole.settings')

app = Celery('carmagnole')


app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.result_expires = timedelta(hours=3)


app.conf.beat_schedule = {
    'send-newsletter-everyday': {
        'task': 'mails.tasks.send_newsletter',
        'schedule': crontab(hour='4', minute="30"),  
    },
    'clear-expired-redis-keys-every-six-hours': {
        'task': 'utils.tasks.clear_expired_redis_keys',
        'schedule': crontab(hour='6'),  
    },
}
