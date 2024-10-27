from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny
from rest_framework import status

from django.http import JsonResponse, HttpResponse

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.validators import validate_email

from authenticate.authentication import AnonAuthentication
from utils.models import NewsletterSubscriberModel

from datetime import datetime, timezone, UTC

@api_view(['POST'])
@permission_classes([AllowAny])
# @authentication_classes([BasicAuthentication])
@authentication_classes([AnonAuthentication])
def subscribe_to_newsletter(request):
    if request.method == "POST":
        user_mail = request.data['email']
        if user_mail:
            try:
                validate_email(user_mail)
                subscriber = NewsletterSubscriberModel.objects.create(email=user_mail)
                subscriber.subscribe()
                return Response(data={"message": "Subscribed successfully", "email": subscriber.email},status=status.HTTP_201_CREATED)
            except ValidationError:
                return Response(data="Email validation error", status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            except IntegrityError:
                return Response(data={"message": "Subscribed successfully", "email": user_mail},status=status.HTTP_201_CREATED) #Just a safety measure
            
        return Response(data={"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(data={"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)