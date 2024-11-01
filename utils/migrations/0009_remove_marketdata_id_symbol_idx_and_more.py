# Generated by Django 5.0 on 2024-08-23 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0008_marketdatahistoric_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='marketdata',
            name='id_symbol_idx',
        ),
        migrations.AddIndex(
            model_name='marketdata',
            index=models.Index(fields=['id'], name='stock_market_prices_id_idx'),
        ),
        migrations.AddIndex(
            model_name='marketdata',
            index=models.Index(fields=['symbol'], name='stock_market_prices_symbol_idx'),
        ),
    ]
