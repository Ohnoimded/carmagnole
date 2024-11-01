from django.conf import settings

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import now
from smtplib import SMTPException, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError, SMTPServerDisconnected, SMTPNotSupportedError

import redis

from .create_mail_for_the_day import create_mail
from utils.models import NewsletterSubscriberModel 
import time
from datetime import timedelta

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
    while True:
        html_content = redis_client.get('daily_newsletter')
        if not html_content:
            create_mail(pls_return=False)
            html_content = redis_client.get('daily_newsletter')

        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8')

        last_id = redis_client.get('sent_newsletter_subscribers_last_id')
        last_id = int(last_id) if last_id else 0

        subscribers = NewsletterSubscriberModel.objects.filter(subscribed=True, id__gt=last_id).order_by('id')[:10]

        if not subscribers:
            break  

        for subscriber in subscribers:
            if not redis_client.sismember('sent_newsletter_subscribers', subscriber.id):
                last_subscriber_id = subscriber.id
                redis_client.sadd('sent_newsletter_subscribers', last_subscriber_id)
                redis_client.expire('sent_newsletter_subscribers', 10800)
                redis_client.set('sent_newsletter_subscribers_last_id', last_subscriber_id, ex=10800)

                send_email_task.delay(
                    subject="La Carmagnole: Daily Nuggets",
                    body=html_content,
                    from_email='La Carmagnole <noreply@carmagnole.ohnoimded.com>',
                    to_email=subscriber.email,
                )
        time.sleep(2) 