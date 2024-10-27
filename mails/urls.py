from django.urls import path
from .views import mail_test

urlpatterns = [
    path('', mail_test, name='mail-test'),
    
]