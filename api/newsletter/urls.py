from django.urls import path, re_path
from .views import subscribe_to_newsletter


urlpatterns = [
    path('subscribe/', subscribe_to_newsletter, name='newsletter_subscribe'),
]


