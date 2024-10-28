from django.conf import settings

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import now
from smtplib import SMTPException, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError, SMTPServerDisconnected, SMTPNotSupportedError

import redis

from .create_mail_for_the_day import create_mail
from utils.models import NewsletterSubscriberModel 
import time

redis_client = redis.Redis(connection_pool=settings.REDIS["default"]["POOL"],encoding='utf-8',decode_responses=True)

@shared_task
def send_newsletter():

    html_content = redis_client.get('daily_newsletter')
    if not html_content:
        create_mail(pls_return=False)
        html_content = redis_client.get('daily_newsletter')
        
    if isinstance(html_content, bytes):
        html_content = html_content.decode('utf-8')
    
    while True:
        
        last_id = redis_client.get('sent_newsletter_subscribers_last_id')
        
        if last_id:
            last_id = int(last_id)
            subscribers = NewsletterSubscriberModel.objects.all().\
            filter(subscribed=True, id__gt=last_id).order_by('id')[:10]
        else:
            subscribers = NewsletterSubscriberModel.objects.all().filter(subscribed = True).order_by('id')[:10]

        try:
            for subscriber in subscribers:
                if redis_client.sismember('sent_newsletter_subscribers', subscriber.id):
                    continue
                email = EmailMultiAlternatives(
                    subject="Le Carmagnole: Daily Nuggets",
                    body="Today's Top News",  # Plain text content
                    from_email='Le Carmagnole <noreply@carmagnole.ohnoimded.com>',
                    to=[subscriber.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                redis_client.sadd('sent_newsletter_subscribers', subscriber.id)
                redis_client.expire('sent_newsletter_subscribers', 60**60*6) 
                if subscribers:
                    redis_client.set('sent_newsletter_subscribers_last_id', subscribers.last().id, ex=60 * 60 * 2)
                time.sleep(1)
        except:
            pass
        
