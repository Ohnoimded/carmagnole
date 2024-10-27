###############################################################
# SHould consider making this into a service and restart and 
# stop periodically. WOuld be more controllable compared to
# this loop that starts only when the build is complete 
# which can be offset and data fetch start delay can happen.
# Most exchanges trade for less than 8 hrs per day, so adding a 
# check at every 30 mins would be ideal
##############################################################


import os
import django
from django.conf import settings
from redis import Redis, ConnectionPool

settings.configure(

    DATABASES={
        "default": {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # 'NAME': os.environ.get('POSTGRES_DB'),
            # 'USER': os.environ.get('POSTGRES_USERID'),
            # 'PASSWORD': os.environ.get('POSTGRES_PWD'),
            # 'HOST': 'host.docker.internal',  # use 'localhost' for running locally
            # 'PORT': '5432',

            'NAME': os.environ.get('POSTGRES_AWS_DB'),
            'USER': os.environ.get('POSTGRES_AWS_USERID'),
            'PASSWORD': os.environ.get('POSTGRES_AWS_PWD'),
            'HOST': os.environ.get('POSTGRES_AWS_HOST'), 
            'PORT': os.environ.get('POSTGRES_AWS_PORT'),
        },
    },

    REDIS={
        "default": {
            "POOL": ConnectionPool(
                host=os.environ.get("REDIS_HOST", 'localhost'),
                port=os.environ.get("REDIS_PORT", 6379),
                db=os.environ.get("REDIS_DB", 0),
                password=os.environ.get("REDIS_PASSWORD", None),
                max_connections=1000,
                socket_timeout=1500,
            ),
        }
    },

    INSTALLED_APPS=[
        'utils',  # Include the apps you need
    ],
    LANGUAGE_CODE="en-us",
    TIME_ZONE="UTC",
    USE_I18N=True,
    USE_TZ=True,
    DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
)

django.setup()

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
from utils.models import MarketData, StockSymbolsModel, StockMarketsModel
from django.db import connections
import ssl
import certifi
from asgiref.sync import sync_to_async
import psycopg2
import json
from datetime import datetime
import base64

from google_cookie_manager import GoogleCookieManager

class MarketDataUpdater:
    def __init__(self):
        self.tickers = None
        self.results = None
        self.active_tickers = None 
        self.db_cursor = None
        self.redis = Redis(connection_pool=settings.REDIS["default"]["POOL"],charset="utf-8", decode_responses=True)



    @sync_to_async
    def setup_db_connection(self):
        self.db_cursor = connections['default'].cursor()
        
    @sync_to_async
    def fetch_active_tickers(self):
        try:
            self.db_cursor.callproc('get_current_trading_symbols') # check utils.model to get the implementation
            self.active_tickers = self.db_cursor.fetchall()
            # print(active_tickers)
            if not self.active_tickers:
                print("No active tickers found.")
                return []
            columns = [col[0] for col in self.db_cursor.description]
            return [dict(zip(columns, row)) for row in self.active_tickers]
        except Exception as e:
            print(f"Error fetching tickers: {e}")
            return []

    async def scrape_prices(self):
        if not self.tickers:
            print("No tickers available to fetch prices.")
            return
        
        cookies = self.redis.get("cookies_google")
        if not cookies:
            await GoogleCookieManager(self.redis).fetch_store_google_cookies()
            cookies = self.redis.get("cookies_google")
        if cookies:
            cookies = cookies.decode('utf-8')
        
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36", 
                "Cookie": str(cookies)}
            # Need to fetch and store cookies
                    
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [self._fetch_single_price(stock, session) for stock in [i for i in self.tickers]]
            self.results = [res for res in await asyncio.gather(*tasks) if res]

    async def _fetch_single_price(self, stock, session, retry=False):
        try:
            sslcontext = ssl.create_default_context(cafile=certifi.where())
            target_url = f'https://www.google.com/finance/quote/{stock["google"]}'
            async with session.get(target_url, ssl=sslcontext) as response:
                if str(response.url) != target_url:
                    if not retry:
                        await GoogleCookieManager(self.redis).fetch_store_google_cookies() ## EU REGULATION COOOKIE CONSENT THINGY
                        raise Exception("Cookie Error")
                txt = await response.text()
                soup = BeautifulSoup(txt, 'html.parser')
                price = float(soup.select_one('div.YMlKec.fxKbKc').get_text().replace(',', ''))
                return {'ticker': stock['google'], 'price': price,'timezone_name':stock['timezone_name']}
        except Exception as e:
            print(f"Error scraping price for {stock['google']}: {e}")
            return None
        
    @sync_to_async
    def push_to_redis_and_send_notification(self):
        channel = 'stock_updates_channel'
        self.db_cursor.execute(''' SELECT 
										JSON_AGG(
										JSON_BUILD_OBJECT(
										'id', id,
										'ticker_short', ticker_short,
										--'ticker_symbol', ticker_symbol,
										'ticker_desc', ticker_desc, 
										'current_price', current_price,         
										'last_price', last_price, 
										'last_traded_date', last_traded_date, 
										'currency_code', currency_code ,                   
										--'currency_char', currency_char
										'html_code', html_code,
										'currency_prefix', currency_prefix,
										'currency_unicode' ,currency_unicode
										)
										) 
									FROM stock_prices_matview;
                                    ;''')
        push_data = json.dumps(self.db_cursor.fetchone()[0],ensure_ascii=False)
        self.redis.set('stock_updates_initial_load',push_data) # for initial 
        self.redis.publish(channel,push_data)
        self.db_cursor.execute("SELECT pg_notify('stock_market_updates',%s)",[push_data])
            
    @sync_to_async
    def save_to_db(self):
        if not self.results:
            print("No market data to save.")
            return

        try:
            for item in self.results:
                symbol = StockSymbolsModel.objects.get(google=item['ticker'])
                MarketData.objects.create(
                    symbol=symbol,
                    price=item['price'],
                    time=datetime.now(UTC)
                )
            self.db_cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY stock_prices_matview;')
            
        except Exception as e:
            print(f"Error saving data to DB: {e}")
            
    
            
    async def run(self):
        print('Process Running....')
        await self.setup_db_connection()
        while True:
            try:
                self.tickers = await self.fetch_active_tickers()
                if self.tickers:
                    await self.scrape_prices()
                    await self.save_to_db()
                    await self.push_to_redis_and_send_notification()
                else:
                    raise Exception('No tickers found.')
                await asyncio.sleep(46)  # Fetch every 46 seconds
            except Exception as e:
                print(f"Error in main loop: {e}. Retrying in 60 minutes.")
                await asyncio.sleep(3600)

if __name__ == "__main__":
    print('Market Data Live Fetch Starting.')
    asyncio.run(MarketDataUpdater().run())
    print('Market Data Live Fetch Stopped.')
    # I should have added a logger here but this is low priority data and can be easily implemented with CSR







# timezone_queryset = StockMarketsModel.objects.values('timezone').distinct()

# exch_timezones = [i['timezone'] for i in timezone_queryset]


# def isTradingNow(tz):
#     current_time = datetime.now(tz=ZoneInfo(tz))
#     morning_start = current_time.replace(hour=9, minute=00, second=00, microsecond=00)
#     evening_end = current_time.replace(hour=16, minute=00, second=00, microsecond=00)
    
#     if morning_start <= current_time <= evening_end :
#         return True
#     return False
# current_trading_zones = []

# for i in exch_timezones:
#     if isTradingNow(i):
#         current_trading_zones.append(i)

# trading_symbols_queryset = StockSymbolsModel.objects.select_related('')

# def getTickers():
#     ticker_dict={}
#     for i in query_set:
#         ticker_dict[i['description']]=i['google']
#     tickers= [v for k,v in ticker_dict.items()]
#     return tickers
# tickers = getTickers()

# async def market_peasant(session, ticker):
#     async with session.get(f'https://www.google.com/finance/quote/{ticker}') as response:
#         txt = await response.text()
#         soup = BeautifulSoup(txt, 'html.parser')
#         current = float(soup.select_one('div.YMlKec.fxKbKc').get_text().replace(',',''))
#         previous_close = float(soup.select_one('div.P6K39c').get_text().replace(',',''))
#         return {ticker: current}# previous_close

# async def getMarketData():
#     async with aiohttp.ClientSession() as session:
#         tasks = [market_peasant(session, ticker) for ticker in tickers]
#         results = await asyncio.gather(*tasks)
#         combined_results = {k: v for result in results for k, v in result.items()}
#         print(combined_results)
#         return combined_results
