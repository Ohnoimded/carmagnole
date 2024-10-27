from django.urls import path
from .views import FrequentDataListView, FrequentDataDetailView, ArticleDetailAPIView, FeaturedArticleView


urlpatterns = [
    path('frequentdata/', FrequentDataListView.as_view(), name='frequentdata-list'),
    path('frequentdata/<int:pk>/', FrequentDataDetailView.as_view(), name='frequentdata-detail'),
    path('article/', ArticleDetailAPIView.as_view(), name='article-detail-query'), 
    path('article/<slug:slug>/', ArticleDetailAPIView.as_view(), name='article-detail'),
    path('featured_article/', FeaturedArticleView.as_view(), name='featured-article'),
]