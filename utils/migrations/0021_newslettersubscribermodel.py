# Generated by Django 5.1 on 2024-10-09 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0020_articlemetaanalytics_wordcount'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterSubscriberModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('subscribed', models.BooleanField(default=True)),
                ('subscription_date', models.DateTimeField(auto_now=True)),
                ('unsubscription_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'newsletter_subscribers',
            },
        ),
    ]
