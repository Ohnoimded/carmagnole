from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.db import IntegrityError, connection
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

import json
import redis
import random

from authenticate.authentication import AnonAuthentication
from authenticate.permission import IsAuthenticatedOrToken
from utils.models import FrequentData, ArticleMetaAnalytics
from utils.api_version import api_version
from .serializers import FrequentDataSerializer, ArticleDataSerializer
from .filters import FrequentDataFilter
from .pagination import NewsPagination

redis_client = redis.Redis(
    connection_pool=settings.REDIS["default"]["POOL"], decode_responses=True)


class FrequentDataListView(generics.ListAPIView):
    queryset = FrequentData.objects.order_by('-id')[:100]
    serializer_class = FrequentDataSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FrequentDataFilter
    pagination_class = NewsPagination
    permission_classes = [IsAuthenticatedOrToken]
    authentication_classes = [AnonAuthentication]

    def get_queryset(self):

        featured_articles_ids = redis_client.get('featured_articles_ids')
        if featured_articles_ids:
            try:
                exclude_ids = json.loads(featured_articles_ids)[0:5]
            except (IndexError, ValueError, json.JSONDecodeError):
                exclude_ids = []
        else:
            exclude_ids = []

        latest_article = FrequentData.objects.order_by('-id').first()
        if latest_article:
            latest_id = latest_article.id
            if latest_id not in exclude_ids and not len(exclude_ids):  
                exclude_ids.append(latest_id)

        queryset = FrequentData.objects.order_by('-id').exclude(id__in=exclude_ids)[:100]

        return queryset

    @api_version(version='1.0')
    @method_decorator(cache_page(60*5))  # cache for 5 mins
    def get(self, request, *args, **kwargs):

        return super().get(self, request, *args, **kwargs)
        # return FrequentData.objects.all()[:100].cached_queryset()
        # return FrequentData.objects.all()[:100].cached_queryset()

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())

    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)


class FrequentDataDetailView(generics.RetrieveAPIView):
    queryset = FrequentData.objects.all()
    serializer_class = FrequentDataSerializer
    authentication_classes = [AnonAuthentication]


#######################################################################


class ArticleDetailAPIView(generics.RetrieveAPIView):

    """ 
    This view is only meant for individual articles and should not be paged.
    """
    queryset = FrequentData.objects.all()
    serializer_class = ArticleDataSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrToken]
    authentication_classes = [AnonAuthentication]
    lookup_field = 'slug'

    @api_version(version='1.0')
    @method_decorator(cache_page(60*60*5))  # Cache for 5 hrs
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            slug = request.GET.get('slug') or kwargs.get('slug')
            section = request.GET.get(
                'section') or kwargs.get('section') or None

            try:
                if not slug:
                    raise NotFound(detail="Article not found.")

                if section:
                    print(slug, section)
                    article = FrequentData.objects.filter(slug=slug, section=section).values().first()
                else:
                    article = FrequentData.objects.filter(slug=slug).values().first()

                if article is None:
                    raise NotFound(detail="Article not found.")
                
                # GEtting the keywords part
                article_id = article['id']
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                            SELECT 
                                nc.key AS word,
                                SUM(nc.value::int) AS total_count
                                FROM 
                                    article_meta_analytics ama 
                                JOIN 
                                    jsonb_each_text(ama.ner_keywords) as nc ON true
                                WHERE ama.article_id = %s
                                GROUP BY nc.key
                                ORDER BY total_count DESC LIMIT 5; 
                    """, [article_id])
                    rows = cursor.fetchall()
                    
                if rows:
                    article_meta = [{"word":row[0],"count":row[1]} for row in rows]
                else:
                    article_meta = ""
                
                serializer = ArticleDataSerializer(article)
                return JsonResponse({'article_data': serializer.data,'article_meta':article_meta})
            except NotFound as e:
                return JsonResponse({'error': 'Article not found'}, status=404)

            except Exception as e:
                return JsonResponse({'error': 'Something\'s wrong'}, status=500)
    # def get_object(self):
    #     try:
    #         return super().get_object()
    #     except FrequentData.DoesNotExist:
    #         raise NotFound(detail="Article not found.")


class FeaturedArticleView(generics.RetrieveAPIView):

    """
    Add caching with redis. dont use page cache cos we aint pagin'. Use SETEX and GET. 
    Putting this on backlog cos i need this up and running asap.
    """
    queryset = FrequentData.objects.all()
    serializer_class = FrequentDataSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrToken]
    # permission_classes = [IsAuthenticatedOrToken]
    authentication_classes = [AnonAuthentication]

    @api_version(version='1.0')
    def get(self, request, *args, **kwargs):
        if request.method == "GET":
            try:
                try:
                    featured_article_ids = json.loads(redis_client.get('featured_articles_ids'))
                    featured_articles_count = len(featured_article_ids)
                except:
                    featured_articles_count = 0

                if featured_articles_count:
                    # featured_article_id = json.loads(redis_client.get('featured_articles_ids'))[0]
                    if featured_articles_count <=4:
                        featured_article_id = featured_article_ids[random.randint(0, featured_articles_count-1)]
                    else:
                        featured_article_id = featured_article_ids[random.randint(0, 2)]  # Just getting the best and returning some random article from the best
                    
                    featured_article = FrequentData.objects.filter(id=featured_article_id).first()
                    
                    
                    if featured_article:
                        serializer = FrequentDataSerializer(featured_article)
                        return Response({'featured_article_data': serializer.data})
                    else:
                        raise NotFound(detail='Featured Article Not Found')
                else:
                    featured_article = FrequentData.objects.filter(
                        imageurl__isnull=False).order_by('-id').first()
                    # I think this avoids sending of duplicate articles
                    redis_client.set('featured_articles_ids',
                                     str([featured_article.id]))
                    if featured_article:
                        serializer = FrequentDataSerializer(featured_article)
                        return Response({'featured_article_data': serializer.data})
                    else:
                        raise NotFound(detail='Featured Article Not Found')
            except NotFound as e:
                return JsonResponse({'error': str(e)}, status=404)
            except Exception as e:
                return JsonResponse({'error': 'Something\'s wrong'}, status=500)
