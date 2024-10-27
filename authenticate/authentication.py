from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.authentication import BaseAuthentication,BasicAuthentication,SessionAuthentication
from .models import User

 
class AnonAuthentication(BaseAuthentication):
    '''
    This is supposed to be only for API related authentication for single use JWT. 
    Hence, anon.
    '''
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None

        try:
            validated_token = AccessToken(token)
            return (None, validated_token)
        except TokenError:
            raise InvalidToken('Token is invalid or expired')

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
    
class UserAuthentication(SessionAuthentication):
    '''
    Need to use somewhere. 
    '''
    def authenticate(self, request):
        return super().authenticate(request)
    
    def enforce_csrf(self, request):
        return super().enforce_csrf(request)
    