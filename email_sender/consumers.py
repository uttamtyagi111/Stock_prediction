# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class EmailStatusConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Join a specific group for email status updates
#         self.group_name = 'email_status_updates'
#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )
#         await self.accept()
#         print(f"WebSocket connected: {self.channel_name}")

#     async def disconnect(self, close_code):
#         # Leave the group
#         await self.channel_layer.group_discard(
#             self.group_name,
#             self.channel_name
#         )
#         print(f"WebSocket disconnected: {self.channel_name}")

#     # Receive message from WebSocket (if needed)
#     async def receive(self, text_data):
#         # For this use-case, you might not need to handle incoming messages
#         pass

#     # Handler for sending status updates to WebSocket
#     async def send_status_update(self, event):
#         status = event['status']
#         email = event['email']
#         timestamp = event['timestamp']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'email': email,
#             'status': status,
#             'timestamp': timestamp
#         }))
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

class EmailStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the authenticated user's ID or email
        user = self.scope["user"]

        if user.is_authenticated:
            # Create a group name for this specific user
            self.group_name = f'user_{user.id}'  # or user.username, email, etc.

            # Add this WebSocket connection to the user's group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            # Accept the WebSocket connection
            await self.accept()

        else:
            # If the user is not authenticated, reject the connection
            await self.close()

    async def disconnect(self, close_code):
        # Leave the user-specific group when the WebSocket disconnects
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_status_update(self, event):
        status = event['status']
        email = event['email']
        timestamp = event['timestamp']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'email': email,
            'status': status,
            'timestamp': timestamp
        }))
