# import json
# from channels.generic.http import AsyncHttpConsumer
# from channels.db import database_sync_to_async
# from utils.models import MarketDataMatView 
# from datetime import datetime, UTC
# import asyncio

# class MarketDataSSEConsumer(AsyncHttpConsumer):
#     async def handle(self, body):
#         await self.send_headers(headers=[
#             (b"Cache-Control", b"no-cache"),
#             (b"Content-Type", b"text/event-stream"),
#             (b"Transfer-Encoding", b"chunked"),
#         ])

#         while True:
#             data = await self.get_market_data()
#             json_data = json.dumps({
#                 'content': data,
#                 'time': str(datetime.now(UTC))
#             })
#             await self.send_body(f"data: {json_data}\n\n".encode("utf-8"), more_body=True)
#             await asyncio.sleep(15)

#     @database_sync_to_async
#     def get_market_data(self):
#         return list(MarketDataMatView.objects.all().values(
#             'id', 'ticker_symbol', 'ticker_desc', 'current_price',
#             'last_price', 'last_traded_date', 'currency_code',
#             'currency_char', 'html_code'
#         ))