from django.urls import include, path
from .views import test_request

urlpatterns = [
    path('news/', include('api.api_news.urls')),    
    path('test/', test_request, name='test'),
    path('market_data/', include('api.market_data_sse.urls')),
    path('newsletter/', include('api.newsletter.urls')),
    path('analytics/', include('api.plotpourri.urls')),
]
