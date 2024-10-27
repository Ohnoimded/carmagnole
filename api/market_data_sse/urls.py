from django.urls import path, re_path
from .views import stream_messages_view


urlpatterns = [
    path('stream/', stream_messages_view, name='market_data_stream'),
]


