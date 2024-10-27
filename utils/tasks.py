from django.conf import settings

from celery import shared_task
import redis

redis_client = redis.Redis(connection_pool=settings.REDIS["default"]["POOL"],decode_responses=True)

@shared_task
def clear_expired_redis_keys():
    """Redis takes up too much space storing keys. I have memory constraints"""
    cursor = '0'
    while cursor != 0:
        cursor, keys = redis_client.scan(cursor=cursor)
        for key in keys:
            if redis_client.ttl(key) == -2:  
                redis_client.delete(key)
    print("Expired keys cleared.")
