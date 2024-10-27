# Generated by Django 5.0 on 2024-08-25 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0013_remove_marketdata_stock_market_prices_symbol_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketDataMatView',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('ticker_symbol', models.CharField(max_length=20)),
                ('ticker_desc', models.CharField(max_length=120)),
                ('current_time_utc', models.DateTimeField()),
                ('current_time_ltz', models.DateTimeField()),
                ('timezone_name', models.CharField(max_length=34)),
                ('current_price', models.DecimalField(decimal_places=3, max_digits=10)),
                ('last_price', models.DecimalField(decimal_places=3, max_digits=10)),
                ('last_traded_date', models.DateField()),
                ('currency_name', models.CharField(max_length=120)),
                ('currency_code', models.CharField(max_length=3)),
                ('currency_char', models.TextField()),
                ('html_code', models.CharField(max_length=10)),
            ],
            options={
                'db_table': 'stock_prices_matview',
                'managed': False,
            },
        ),
    ]
