from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes, authentication_classes, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from django_ratelimit.decorators import ratelimit
from .serializers import APITokenObtainSerializer, TokenRefreshSerializer, UserRegisterSerializer, UserLoginSerializer
from .authentication import AnonAuthentication, UserAuthentication
from .models import User
from .services import AuthService

@api_view(['GET'])
@ratelimit(key="ip", rate='5/m')
@authentication_classes([SessionAuthentication])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def user_view(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            user_details = {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                }
            return Response(user_details,status=status.HTTP_200_OK)
        else:
            return Response('User not Authenticated',status=status.HTTP_418_IM_A_TEAPOT)
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@ratelimit(key="ip", rate='3/m')
@authentication_classes([])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def register_view(request):
    if request.method == 'POST':
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                AuthService.create_user(request,**serializer.validated_data)
                return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED, )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response("Error: Username/Mail already exists", status=status.HTTP_409_CONFLICT)
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def login_view(request):
    if request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            AuthService.login_user(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@authentication_classes([AnonAuthentication])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def api_token_obtain_view(request):
    if request.method == 'POST':
        serializer = APITokenObtainSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@authentication_classes([AnonAuthentication])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def token_refresh_view(request):
    serializer = TokenRefreshSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)