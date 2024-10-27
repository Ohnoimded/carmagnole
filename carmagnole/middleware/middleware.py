from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from utils.models import ArticleAccess, FrequentData, UserTracker
from django.shortcuts import get_object_or_404
from rest_framework import status
import json

from django.http import JsonResponse,HttpResponseBadRequest
from django.utils.html import escape

class HideServerHeadersMiddleware(MiddlewareMixin):
    # def __init__(self, get_response):
    #     self.get_response = get_response

    # def __call__(self, request):
    #     response = self.get_response(request)
    #     return self.process_response(request, response)

    def process_response(self, request, response):
        
        if isinstance(response, JsonResponse):
            response['Server'] = 'Carmagnole v0.1'
            response['X-Powered-By'] = None
        elif hasattr(response, 'headers'):
            response.headers['Server'] = 'Carmagnole v0.1'
            response.headers['X-Powered-By'] = None
        # print(response.headers, request.method)
        return response
    
class VersioningMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        if 'API-Version' not in response:
            response['API-Version'] = '1.0'
            response.headers['API-Version'] = '1.0'
        return response

class TrackAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == status.HTTP_200_OK:
            try:
                response_data = json.loads(response.content)
                article_id = response_data['article_data']['id']
            except:
                return response
            accessed_ip = self.get_client_ip(request)
            if accessed_ip:
                self.track_access(article_id, accessed_ip)
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  
        else:
            ip = request.META.get('REMOTE_ADDR') 

        return ip

    def track_access(self, article_id,accessed_ip):
        ArticleAccess.objects.create(article_id=article_id, accessed_at=now(),accessed_ip=accessed_ip)
        
class SanitizeURLParamsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.GET._mutable = True
        for key, value in request.GET.items():
            request.GET[key] = escape(value)
        request.GET._mutable = False
        response = self.get_response(request)
        return response