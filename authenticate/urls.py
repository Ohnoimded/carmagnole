from django.urls import path
from .views import register_view,login_view,api_token_obtain_view,token_refresh_view, user_view
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('user/login/', login_view, name='user_login_view'),
    path('user/register/', register_view, name='user_register_view'),
    path('user/', user_view, name='user_view'),
    path('api/token/', api_token_obtain_view, name='api_token_obtain'),
    # path('api/refresh/', token_refresh_view, name='api_token_refresh'), Might need in the future I guess
]
