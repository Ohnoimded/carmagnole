import django_filters
from utils.models import ArticleMetaAnalytics, FrequentData
from django.db.models import Q, F

from datetime import datetime, timedelta, UTC

def convert_timeperiod_to_datetime(value='1d'):
    now = datetime.now(UTC)
    if value == "1d":
        start_time = now - timedelta(hours=24)
    elif value == "1w":
        start_time = now - timedelta(hours=168)
    elif value == "2w":
        start_time = now - timedelta(hours=336)
    elif value == "1m":
        start_time = now - timedelta(hours=720)
    else:
        start_time =  now - timedelta(hours=24) # safety
    return start_time
            
class FrequentDataFilter(django_filters.FilterSet):
    
    # publishdate is different from created_at in metanalytics table. publishdate is part of frequentdata so we need a join for that
    
    # publishdate_gt = django_filters.DateTimeFilter(field_name='publishdate', lookup_expr='gt')
    # publishdate_lt = django_filters.DateTimeFilter(field_name='publishdate', lookup_expr='lt')
    timeperiod = django_filters.CharFilter(method='filter_by_time_period')
    
    
    def filter_by_time_period(self, queryset, name, value='1d'):
         
        start_time = convert_timeperiod_to_datetime(value)
        return queryset.filter(publishdate__gte=start_time)
    
    class Meta:
        model = FrequentData
        fields: dict[str,list] = {
            'source': ['exact', 'icontains'],
            'section': ['exact', 'icontains'],
            'author': ['exact', 'icontains'],
            'headline': ['exact', 'icontains'],
            'publishdate': [ 'exact'],
        }
        
class ArticleMetaAnalyticsFilter(django_filters.FilterSet):
    
    pos_or_neg =  django_filters.CharFilter(method='filter_by_polarity_type')
    
    def filter_by_polarity_type(self, queryset, name, value):
        if value == "pos":
            return queryset.filter(polarity_pos__gt=F('polarity_neg'))
        elif value == "neg":
            return queryset.filter(polarity_neg__gt=F('polarity_pos'))
        return queryset
    
    ner_countries = django_filters.CharFilter(method='filter_by_ner_countries')
    
    def filter_by_ner_countries(self, queryset, name, value):
        countries = value.split(',')
        query = Q()
        for country in countries:
            query |= Q(ner_countries__contains=country)
        return queryset.filter(query)

    class Meta:
        model = ArticleMetaAnalytics
        fields = {
            'polarity_pos': ['gt', 'lt', 'exact'],
            'polarity_neu': ['gt', 'lt', 'exact'],
            'polarity_neg': ['gt', 'lt', 'exact'],
            'polarity_comp': ['gt', 'lt', 'exact'],
            'wordcount': ['gt', 'lt', 'exact'],
            'n_sentences': ['gt', 'lt', 'exact'],
        }