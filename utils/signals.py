from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from .models import FrequentData
from datetime import datetime, timezone, UTC

from celery import chain

import json 
import redis

from analytics.tasks import runAnalytics

redis_client = redis.Redis(connection_pool=settings.REDIS["default"]["POOL"],decode_responses=True)


@receiver(post_save, sender=FrequentData)
def push_to_redis_on_save(sender, instance,created, **kwargs):
    if created:
        data  = {
            'id':instance.id,
            'nohtmlbody':instance.nohtmlbody,
            'wordcount':instance.wordcount,
            'created_at': str(datetime.now(UTC))
        }
        redis_client.lpush('frequentdata_queue',json.dumps(data))
        
    if redis_client.llen('frequentdata_queue'):
        # analytics_chain = chain(run_analytics_task.s(), find_top_articles_last_32Hours_task.s())
        runAnalytics.delay()
       
   