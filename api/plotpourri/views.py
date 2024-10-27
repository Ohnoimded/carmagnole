from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny
from rest_framework import status

from django.http import JsonResponse, HttpResponse

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.models import Avg, Sum, Count, F, Func, CharField, Value, JSONField, DateField, IntegerField
from django.db.models.functions import Round, TruncDate, Cast
from django.db.models.expressions import RawSQL
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.validators import validate_email

from django.views.decorators.cache import cache_page

from authenticate.authentication import AnonAuthentication
from utils.models import NewsletterSubscriberModel
from datetime import datetime, timezone, UTC

from utils.models import FrequentData, ArticleMetaAnalytics
from utils.api_version import api_version
from .filters import FrequentDataFilter, ArticleMetaAnalyticsFilter, convert_timeperiod_to_datetime

import json


@api_version(version='1.0')
@api_view(["GET"])
@permission_classes([AllowAny])
# @authentication_classes([BasicAuthentication])
@authentication_classes([AnonAuthentication])
@cache_page(60 * 5)
def serve_plot_data(request, *args, **kwargs):
    """
    For now I am only interested in serving the same data. need to work on different plots and 
    filters in the future. Not enough time. Gotta deploy fast.
    """
    if request.method == "GET":

        try:
            frequentdata_filtered = FrequentDataFilter(
                request.GET, queryset=FrequentData.objects.all())

            analytics_filtered = ArticleMetaAnalyticsFilter(
                request.GET, queryset=ArticleMetaAnalytics.objects.all())

            queryset = ArticleMetaAnalytics.objects.filter(article__in=frequentdata_filtered.qs.values('id'),  # article_id <> id relationship
                                                           ).filter(id__in=analytics_filtered.qs.values('id'))
            plot_type = request.GET.get('plot_type', 'sentiment_daily')

            start_time = convert_timeperiod_to_datetime(
                request.GET.get('timeperiod', '1d'))

            if plot_type == "topic_counts":
                # .filter(polarity_pos__gt=F('polarity_neg'))
                result = (queryset
                          .values('article__section')
                          .exclude(article__section__in=['us-news','uk-news', 'australia-news', 'world'])
                          .exclude(article__section__contains='_news')
                          .annotate(total_count=Count('id'))
                          .order_by('-total_count'))[:16]
                final_result = [{'topic': item['article__section'],
                                 'count': item['total_count']}for item in result]
                
                return JsonResponse(data={ "status": "success",
                                          "message": "Article counts per topic",
                                          "timestamp":datetime.now(UTC),
                                          "count":len(final_result), 
                                          'data': final_result
                                          }, status=status.HTTP_200_OK)

            if plot_type == "sentiment_daily":
                result = queryset\
                    .values(
                        publishdate=TruncDate(
                            'article__publishdate')
                    ).annotate(
                        avg_polarity_pos=Round(
                            Avg('polarity_pos'), 5),
                        avg_polarity_neg=Round(
                            Avg('polarity_neg'), 5)
                    ).order_by('-publishdate'
                    ).values(date=F("publishdate"), positive=F("avg_polarity_pos"), negative=F("avg_polarity_neg"))
                    
                final_result = list(result)
                return JsonResponse(data={ "status": "success",
                                          "message": "Positive and negative sentiments of articles per day",
                                          "timestamp":datetime.now(UTC),
                                          "count":len(final_result), 
                                          'data': final_result
                                          }, status=status.HTTP_200_OK)
                
            if plot_type == "geo_hotspots":

                # article_ids = tuple(queryset.values_list('article', flat=True))

                with connection.cursor() as cursor:
                    cursor.execute(f"""
                            SELECT 
                                -- fd.publishdate::date AS day, 
                                nc.key AS country_code,
                                SUM(nc.value::int) AS total_count
                            FROM 
                                article_meta_analytics ama 
                            JOIN 
                                frequent_data fd ON fd.id = ama.article_id
                            JOIN 
                                jsonb_each_text(ama.ner_countries) AS nc ON true
                            WHERE fd.publishdate >= %s
                            GROUP BY 
                                --fd.publishdate::date, 
                                nc.key
                        
                    """, [start_time])
                    rows = cursor.fetchall()

                final_result = [{"country":row[0],"count":row[1]} for row in rows]

                # final_result = [{'day': item['day'], 'country_counts': json.loads(item['country_counts'])} for item in result]
                return JsonResponse(data={ "status": "success",
                                          "message": "Frequency of each country mentioned",
                                          "timestamp":datetime.now(UTC),
                                          "count":len(final_result), 
                                          'data': final_result
                                          }, status=status.HTTP_200_OK)

            if plot_type == "wordcloud":

                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT 
                                nc.key AS word_code,
                                SUM(nc.value::int) AS total_count
                            FROM 
                                article_meta_analytics ama 
                            JOIN 
                                frequent_data fd ON fd.id = ama.article_id
                            JOIN 
                                jsonb_each(ama.ner_keywords) AS nc ON true
                            WHERE fd.publishdate >= %s
                            GROUP BY nc.key
                            ORDER BY total_count DESC 
                            LIMIT 100;
                    """, [start_time])
                    rows = cursor.fetchall()
                    
                final_result = [{"word":row[0],"count":row[1]} for row in rows]
                return JsonResponse(data={ "status": "success",
                                          "message": "Top 100 most frequent keywords by total_count",
                                          "timestamp":datetime.now(UTC),
                                          "count":len(final_result), 
                                          'data': final_result
                                          }, status=status.HTTP_200_OK)
        except ValidationError:
            return HttpResponse(content="Invalid inputs", status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return HttpResponse(content="Unsupported parameter", status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        return HttpResponse(content="Method not allowed", status=status.HTTP_405_METHOD_NOT_ALLOWED)
