import django_filters
from utils.models import FrequentData

class FrequentDataFilter(django_filters.FilterSet):
    publishdate_gt = django_filters.DateTimeFilter(field_name='publishdate', lookup_expr='gt')
    publishdate_lt = django_filters.DateTimeFilter(field_name='publishdate', lookup_expr='lt')

    class Meta:
        model = FrequentData
        fields = {
            'source': ['exact', 'icontains'],
            'section': ['exact', 'icontains'],
            'author': ['exact', 'icontains'],
            'headline': ['exact', 'icontains'],
            'publishdate': [ 'exact'],
        }