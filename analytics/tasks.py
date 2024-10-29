from celery import shared_task

from .services.ml import NLPProcessor, ArticleRanker
from django.db.models import OuterRef, Exists
from utils.models import ArticleMetaAnalytics, FrequentData
from django.conf import settings
import redis
import asyncio
from redis import Redis
import json
from datetime import datetime, UTC, timedelta
import time
import random

redis_client = Redis(connection_pool=settings.REDIS["default"]["POOL"],decode_responses=True)
LOCK_NAME = 'find_top_articles_lock'
LOCK_TIMEOUT = 60  

def acquire_lock(lock_name, timeout):
    identifier = str(time.time())
    time.sleep(round(random.random(),4))
    if redis_client.set(lock_name, identifier, nx=True, ex=timeout):
        return identifier
    return None

def release_lock(lock_name, identifier):
    lock_value = redis_client.get(lock_name)
    if lock_value and lock_value == identifier:
        redis_client.delete(lock_name)
        
@shared_task
def runAnalytics():
    """
    Runs analytics and saves to db
    """
    while redis_client.llen('frequentdata_queue') != 0:
        data  = redis_client.rpop('frequentdata_queue')
        if data:
            data = json.loads(data)
            analysed_data = NLPProcessor.process_article(data)
            if analysed_data:
                ArticleMetaAnalytics.objects.create(**analysed_data)
        else:
            time.sleep(2)
        

    if redis_client.llen('frequentdata_queue') == 0:
        lock_identifier = acquire_lock(LOCK_NAME, LOCK_TIMEOUT)
        if lock_identifier:
            try:
                findTopArticlesLast32Hours.delay()
            finally:
                release_lock(LOCK_NAME, lock_identifier)
        return True

@shared_task
def findTopArticlesLast32Hours():
    # Time for my special secret sauce article ranking algorithm
    # for i in range(10):
    #     print('he', end='')

    columns = ['id', 'article', 'polarity_pos', 'polarity_neu', 'polarity_neg',
               'polarity_comp', 'wordcount', 'n_sentences', 'article_embedding_norm',
               'readability_flesch_reading_ease', 'readability_dale_chall_readability_score',
               'readability_time_to_read']

    thirty_two_hrs_ago = datetime.now(UTC)-timedelta(hours=27) 
    exists_query = FrequentData.objects.filter(
        id=OuterRef('article'), imageurl__isnull=False).exclude(section__in = ['lifeandstyle','society','gnm-press-office'], imageurl="nan", author = "Corrections and clarifications column editor" )
    data = ArticleMetaAnalytics.objects.filter(created_at__gt=thirty_two_hrs_ago).annotate(
            has_image=Exists(exists_query)).filter(has_image=True).values_list(*columns)

    ranked_articles_list = ArticleRanker.score_articles(data, columns)
    redis_client.set('featured_articles_ids', json.dumps(ranked_articles_list[:7])) # only seven to avoid not sending new articles to front page. check the api views.  
