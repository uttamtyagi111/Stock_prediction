# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class EmailStatusConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user_id = self.scope['url_route']['kwargs']['user_id']
#         self.group_name = f'email_status_{self.user_id}'

#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )
        
#         await self.accept()
#         print(f"WebSocket connected for user: {self.user_id}")

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.group_name,
#             self.channel_name
#         )
#         print(f"WebSocket disconnected for user: {self.user_id}")

#     async def receive(self, text_data):
#         pass

#     async def send_status_update(self, event):
#         status = event['status']
#         email = event['email']
#         timestamp = event['timestamp']

#         await self.send(text_data=json.dumps({
#             'email': email,
#             'status': status,
#             'timestamp': timestamp
#         }))


import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class EmailStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'email_status_{self.user_id}'

        try:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"WebSocket connected for user: {self.user_id}")
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user: {self.user_id}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"Received data: {data}")
            # Handle commands if needed
        except json.JSONDecodeError:
            logger.error("Failed to decode WebSocket message")

    async def send_status_update(self, event):
        try:
            status = event['status']
            email = event['email']
            timestamp = event['timestamp']

            await self.send(text_data=json.dumps({
                'email': email,
                'status': status,
                'timestamp': timestamp
            }))
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
