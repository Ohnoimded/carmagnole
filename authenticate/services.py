from django.contrib.auth import login, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import uuid

from .models import User


class AuthService:
    '''
    The whole class is supposed to be doing the token/cookie generation with login/register
    '''
    
    @staticmethod
    def create_user(request,**validated_data):
        user = User.objects.create_user(**validated_data)
        login(request, user)
        return user
    
    # This is bound to fail. need to test. 
    @staticmethod 
    def login_user(request,user):
        try:
            if user.is_authenticated:
                login(request, user)
                return user
            else:
                print('here')
                raise Exception('User not authorized')  # this is pointless I think. not interested in testing. 
        except Exception as e:
            raise e
    
    @staticmethod
    def generate_api_tokens(client_id=None):
        refresh = RefreshToken()
        if client_id:
            refresh['client_id'] = client_id
        return {
            'client_id': client_id if client_id else str(uuid.uuid4()),
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    @staticmethod
    def refresh_token(refresh_token):
        try:
            token = RefreshToken(refresh_token)
            token.check_blacklist()
            access_token = str(token.access_token)
            
            token.blacklist()
            new_refresh_token = RefreshToken()
            
            return {
                'access': access_token,
                'refresh': str(new_refresh_token)
            }
        except TokenError as e:
            raise ValueError(str(e))