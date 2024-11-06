from datetime import datetime, UTC

import json

from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.db import connection as django_db_connection
from django.db.models import F, Value
from django.db.models.functions import JSONObject
from django.contrib.postgres.aggregates import ArrayAgg

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

import asyncio
from adrf.decorators import api_view
from asgiref.sync import async_to_sync, sync_to_async

from collections.abc import AsyncGenerator

import psycopg
import psycopg_pool
from utils.models import MarketDataMatView
from utils.api_version import api_version

from django.conf import settings

import redis.asyncio as redis


redis_client = redis.Redis(connection_pool=settings.REDIS["async_default"]["POOL"],decode_responses=True)

channel = 'stock_updates_channel'


async def stream_messages() -> AsyncGenerator[str, None]:
    initial_load = None

    if not initial_load:
        initial_load = await redis_client.get('stock_updates_initial_load')
        if not initial_load:
            initial_load = await MarketDataMatView.objects.annotate(
                json_obj=JSONObject(
                    id=F('id'),
                    ticker_short=F('ticker_short'),
                    ticker_desc=F('ticker_desc'),
                    current_price=F('current_price'),
                    last_price=F('last_price'),
                    last_traded_date=F('last_traded_date'),
                    currency_code=F('currency_code'),
                    html_code=F('html_code'),
                    currency_prefix=F('currency_prefix'),
                    currency_unicode=F('currency_unicode')
                )
            ).aaggregate(json_agg=ArrayAgg('json_obj'))
            initial_load = json.dumps(initial_load['json_agg'],ensure_ascii=False)
            await redis_client.set('stock_updates_initial_load',initial_load)
            yield f"event: stock_market_updates\nsent_time: {datetime.now().isoformat()}\ndata: {initial_load}\n\n"
        yield f"event: stock_market_updates\nsent_time: {datetime.now().isoformat()}\ndata: {initial_load}\n\n"

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data_payload = message['data']
                yield f"event: stock_market_updates\nsent_time: {datetime.now().isoformat()}\ndata: {data_payload}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()
        
@require_GET
async def stream_messages_view(request, *args, **kwargs):
    response = StreamingHttpResponse(
        stream_messages(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Connection'] = 'keep-alive'

    return response
##########################################################################################

# conn_params = django_db_connection.get_connection_params()
# conn_params.pop('cursor_factory')
# conn_string = f"postgresql://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/{conn_params['dbname']}"

# connection = None

# async def initialize_connection():
#     global connection
#     if connection is None:
#         # Initialize the connection and set up the LISTEN command
#         connection = await psycopg.AsyncConnection.connect(conn_string, autocommit=True)
#         async with connection.cursor() as cursor:
#             await cursor.execute("LISTEN stock_market_updates;")
#             print("LISTEN command executed")

# async def get_connection():
#     if connection is None:
#         await initialize_connection()
#     return connection

# async def stream_messages() -> AsyncGenerator[str, None]:
#     aconnection  = await get_connection()  # Ensure the connection is initialized
#     # print("Listening for notifications...")

#     async for notify in aconnection.notifies():
#         if notify:
#             data_payload = json.dumps(json.loads(notify.payload), ensure_ascii=False)
#             yield f"event: stock_market_updates\nsent_time: {datetime.now().isoformat()}\ndata: {data_payload}\n\n"

# async def stream_messages_view(request):
#     response = StreamingHttpResponse(
#         stream_messages(),  # Use the async generator directly
#         content_type='text/event-stream'
#     )
#     response['Cache-Control'] = 'no-cache'
#     response['X-Accel-Buffering'] = 'no'
#     response['Connection'] = 'keep-alive'

#     return response

#################################################################################
# USelss singleton
# class DatabaseConnection:
#     _instance = None
#     _connection = None

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             # Initialize the connection asynchronously
#             asyncio.ensure_future(cls._instance._initialize_connection())
#         return cls._instance

#     async def _initialize_connection(self):
#         if self._connection is None:
#             print("Initializing connection")
#             conn_params = django_db_connection.get_connection_params()
#             conn_params.pop('cursor_factory')
#             self._connection = await  psycopg.AsyncConnectionPool(**conn_params, autocommit=True)
#             # self._connection = await psycopg.AsyncConnection.connect(**conn_params, autocommit=True)
#             print("Connection initialized")
#             # Listen to a notification channel
#             async with self._connection.cursor() as cursor:
#                 await cursor.execute("LISTEN stock_market_updates;")
#                 print("LISTEN command executed")

#     @property
#     async def connection(self):
#         if self._connection is None:
#             await self._initialize_connection()
#         return self._connection

#     async def close(self):
#         if self._connection:
#             await self._connection.close()
#             self._connection = None
#             print("Connection closed")


# async def stream_messages() -> AsyncGenerator[str, None]:
#     db = DatabaseConnection()
#     connection = await db.connection
#     async for notify in connection.notifies():
#         data_payload = json.dumps(json.loads(notify.payload),ensure_ascii=False)
#         yield f"event: stock_market_updates\nsent_time: {datetime.now(UTC)}\ndata: {data_payload}\n\n"

# conn_params = django_db_connection.get_connection_params()
# conn_params.pop('cursor_factory')
# conn = psycopg.connect(**conn_params, autocommit=True)
# conn.execute("LISTEN stock_market_updates")
# gen = conn.notifies()


# async def stream_messages() -> AsyncGenerator[str, None]:
#     for notify in gen:
#         data_payload = json.dumps(json.loads(notify.payload),ensure_ascii=False)
#         yield f"event: stock_market_updates\nsent_time: {datetime.now(UTC)}\ndata: {data_payload}\n\n"

##########################################################################################################


# First attempt copied from a website
# async def stream_messages() -> AsyncGenerator[str, None]:

#     # Get the connection params from Django
#     connection_params = django_db_connection.get_connection_params()

#     connection_params.pop('cursor_factory')

#     aconnection = await psycopg.AsyncConnection.connect(
#         **connection_params,
#         autocommit=True,
#     )

#     channel_name = "stock_market_updates"

#     async with aconnection.cursor() as acursor:
#         await acursor.execute(f"LISTEN {channel_name}")
#         gen = aconnection.notifies()
#         async for notify in gen:
#             data_payload = json.dumps(json.loads(notify.payload),ensure_ascii=False)
#             yield f"event: stock_market_updates\nsent_time: {datetime.now(UTC)}\ndata: {data_payload}\n\n"


# async def stream_messages_view(request) -> StreamingHttpResponse:
#     response = StreamingHttpResponse(
#         streaming_content=stream_messages(),
#         content_type="text/event-stream",
#     )
#     response['Cache-Control'] = 'no-cache'
#     response['X-Accel-Buffering'] = 'no'
#     response['Connection'] = 'keep-alive'
#     return response


# async def fetch_data() -> list:
#     query = """
#         SELECT id, ticker_symbol, ticker_desc, current_price,
#                last_price, last_traded_date, currency_code,
#                currency_char, html_code
#         FROM stock_prices_matview

#     """
#     with psycopg.connect.cursor() as cursor:
#         cursor.execute(query)
#         rows = cursor.fetchall()
#         columns = [col[0] for col in cursor.description]
#         return [dict(zip(columns, row)) for row in rows]

# async def event_stream():
#     while True:
#         data = await asyncio.to_thread(fetch_data)  # Run sync function in a thread
#         json_data = json.dumps({
#             'content': data,
#             'time': str(datetime.now(UTC))
#         })

#         yield f"data: {json_data}\n\n"
#         await asyncio.sleep(15)  # Non-blocking sleep

# async def market_data_sse(request):
#     response = StreamingHttpResponse(
#         event_stream(),  # Use the async generator directly
#         content_type='text/event-stream'
#     )
#     response['Cache-Control'] = 'no-cache'
#     response['X-Accel-Buffering'] = 'no'
#     response['Connection'] = 'keep-alive'

#     return response
