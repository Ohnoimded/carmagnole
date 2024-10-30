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
def send_email_task(subject, body, from_email, to_email):
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=body,  # Plain text content
            from_email=from_email,
            to=[to_email],
        )
        email.attach_alternative(body, "text/html")
        email.send()
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

@shared_task
def send_newsletter():
    html_content = redis_client.get('daily_newsletter')
    if not html_content:
        create_mail(pls_return=False)
        html_content = redis_client.get('daily_newsletter')

    if isinstance(html_content, bytes):
        html_content = html_content.decode('utf-8')

    last_id = redis_client.get('sent_newsletter_subscribers_last_id')
    if last_id:
        last_id = int(last_id)
        subscribers = NewsletterSubscriberModel.objects.filter(subscribed=True, id__gt=last_id).order_by('id')[:10]
    else:
        subscribers = NewsletterSubscriberModel.objects.filter(subscribed=True).order_by('id')[:10]

    if not subscribers:
        return  

    for subscriber in subscribers:
        # It is memory heavy to add to set, if no. of subscribers grow. But SES 200 per day limit ruins the fun of destroying the container with memory fill
        if not redis_client.sismember('sent_newsletter_subscribers', subscriber.id): 
            
            last_subscriber_id = subscriber.id
            redis_client.sadd('sent_newsletter_subscribers', last_subscriber_id)
            redis_client.set('sent_newsletter_subscribers_last_id', last_subscriber_id)
            
            send_email_task.delay(
                subject="La Carmagnole: Daily Nuggets",
                body=html_content,
                from_email='La Carmagnole <noreply@carmagnole.ohnoimded.com>',
                to_email=subscriber.email,
            )

    