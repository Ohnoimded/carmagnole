from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny

from datetime import datetime, timezone, UTC
import json 
import redis
import html
import re


from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from smtplib import SMTPException, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError


from authenticate.authentication import AnonAuthentication

redis_client = redis.Redis(connection_pool=settings.REDIS["default"]["POOL"],decode_responses=True)

from .create_mail_for_the_day import create_mail


def send_test_email(html_content,text_content):
    # send_mail(
    #     'Test Email',  # Subject
    #     'This is a test email sent from Django.',  # Message
    #     'from@example.com',  # From email
    #     ['to@example.com'],  # To email (replace with the recipient's email)
    #     fail_silently=False,
    # )
    email = EmailMultiAlternatives(
        subject='Your Daily Newsletter is here!!!!',
        body=text_content,  
        from_email='noreply@carmagnole.ohnoimded.com',
        to=['nived@ohnoimded.com'],
    )

    # Attach the HTML content
    # email.attach_file(html_content, "text/html")
    html_content = redis_client.get('daily_newsletter')
    if isinstance(html_content, bytes):
        html_content = html_content.decode('utf-8')
    email.attach_alternative(html_content, "text/html")
    # email.content_subtype = 'text/html'
    email.send(fail_silently=False)





@api_view(['GET'])
@permission_classes([AllowAny])
# @authentication_classes([BasicAuthentication])
@authentication_classes([AnonAuthentication])
def mail_test(request):

    html_content,text_content = create_mail()
    
    send_test_email(html_content,text_content)
    
    return Response(data = "Sent a test mail!")
    # return Response(context)
    # return Response(data=json.dumps(str(article_data)))

