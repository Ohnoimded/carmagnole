# Generated by Django 5.1 on 2024-10-09 22:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0021_newslettersubscribermodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslettersubscribermodel',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
