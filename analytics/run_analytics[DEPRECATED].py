from .services.ml import NLPProcessor, ArticleRanker
from django.db.models import OuterRef, Exists
from utils.models import ArticleMetaAnalytics, FrequentData
from django.conf import settings
import redis
import json
from datetime import datetime, UTC, timedelta


redis_client = redis.StrictRedis(host=settings.REDIS["default"]["HOST"],
                                 port=settings.REDIS["default"]["PORT"],
                                 db=settings.REDIS["default"]["DB"], decode_responses=True)


def runAnalytics():
    """
    Runs analytics and saves to db
    """
    while redis_client.llen('frequentdata_queue') > 0:
        if redis_client.llen('frequentdata_queue'):
            data = json.loads(redis_client.rpop('frequentdata_queue'))
            analysed_data = NLPProcessor.process_article(data)
            if analysed_data:
                ArticleMetaAnalytics.objects.create(**analysed_data)

    if redis_client.llen('frequentdata_queue') == 0:
        return True


def findTopArticlesLast32Hours():
    # Time for my special secret sauce article ranking algorithm
    # for i in range(10):
    #     print('he', end='')

    columns = ['id', 'article_id', 'polarity_pos', 'polarity_neu', 'polarity_neg',
               'polarity_comp', 'wordcount', 'n_sentences', 'article_embedding_norm',
               'readability_flesch_reading_ease', 'readability_dale_chall_readability_score',
               'readability_time_to_read']

    thirty_two_hrs_ago = datetime.now(UTC)-timedelta(hours=32)
    exists_query = FrequentData.objects.filter(
        id=OuterRef('article_id'), imageurl__isnull=False)
    data = ArticleMetaAnalytics.objects.filter(created_at__gt=thirty_two_hrs_ago).annotate(
            has_image=Exists(exists_query)).filter(has_image=True).values_list(*columns)

    ranked_articles_list = ArticleRanker.score_articles(data, columns)
    redis_client.set('featured_articles_ids', json.dumps(ranked_articles_list))
