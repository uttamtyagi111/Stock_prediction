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
from rest_framework_simplejwt.tokens import UntypedToken
from channels.db import database_sync_to_async
from jwt.exceptions import InvalidTokenError
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class EmailStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the token from the query string
        token = self.scope['query_string'].decode('utf-8').split('=')[1]

        try:
            # Validate the JWT token and retrieve the user
            user = await self.get_user_from_token(token)

            if user:
                # Create a user-specific group based on user ID
                self.group_name = f'user_{user.id}'

                # Add this WebSocket connection to the user's group
                await self.channel_layer.group_add(
                    self.group_name,
                    self.channel_name
                )

                # Accept the WebSocket connection
                await self.accept()
            else:
                # If user is not authenticated, close the connection
                await self.close()

        except InvalidTokenError:
            # Invalid token, close the connection
            await self.close()

    async def disconnect(self, close_code):
        # Remove the WebSocket connection from the user's group when it disconnects
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_status_update(self, event):
        # Receive the message from the group and send it to the WebSocket client
        status = event['status']
        email = event['email']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'email': email,
            'status': status,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        This method decodes the JWT token and retrieves the user.
        """
        try:
            # Validate the token and extract the payload
            validated_token = UntypedToken(token)
            user_id = validated_token.get('user_id')

            # Fetch the user from the database
            return User.objects.get(id=user_id)
        except (InvalidTokenError, User.DoesNotExist):
            return None

