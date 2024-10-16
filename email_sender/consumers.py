import json
from channels.generic.websocket import AsyncWebsocketConsumer

class EmailStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join a specific group for email status updates
        self.group_name = 'email_status_updates'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected: {self.channel_name}")

    # Receive message from WebSocket (if needed)
    async def receive(self, text_data):
        # For this use-case, you might not need to handle incoming messages
        pass

    # Handler for sending status updates to WebSocket
    async def send_status_update(self, event):
        status = event['status']
        email = event['email']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'email': email,
            'status': status,
            'timestamp': timestamp
        }))




# from channels.generic.websocket import AsyncWebsocketConsumer
# from rest_framework_simplejwt.tokens import UntypedToken
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from django.contrib.auth.models import AnonymousUser
# from channels.db import database_sync_to_async
# import json
# from django.contrib.auth import get_user_model
# from urllib.parse import parse_qs

# User = get_user_model()

# class EmailStatusConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Extract the token from the query string (URL)
#         query_params = parse_qs(self.scope['query_string'].decode())
#         token = query_params.get('token')

#         if token:
#             try:
#                 # Validate the token
#                 untoken = UntypedToken(token[0])  # Get the first item (token)
#                 user_id = untoken['user_id']  # Extract the user ID from the token
                
#                 # Retrieve the user from the database
#                 self.scope['user'] = await database_sync_to_async(User.objects.get)(id=user_id)
#             except (InvalidToken, TokenError) as e:
#                 # If token is invalid, mark user as anonymous
#                 print(f"Token error: {e}")
#                 self.scope['user'] = AnonymousUser()
#         else:
#             # If no token is provided, mark user as anonymous
#             self.scope['user'] = AnonymousUser()

#         user = self.scope["user"]

#         if user.is_authenticated:
#             # Create a group name based on the authenticated user's ID
#             self.group_name = f"user_{user.id}"
#             await self.channel_layer.group_add(self.group_name, self.channel_name)
#             await self.accept()
#         else:
#             print("User is not authenticated, closing connection.")
#             await self.close()

#     async def disconnect(self, close_code):
#         if self.group_name:
#             await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def send_status_update(self, event):
#         status = event['status']
#         email = event['email']
#         timestamp = event['timestamp']

#         # Send message to the WebSocket
#         await self.send(text_data=json.dumps({
#             'email': email,
#             'status': status,
#             'timestamp': timestamp
#         }))








# from channels.generic.websocket import AsyncWebsocketConsumer
# import json

# class EmailStatusConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         # Print the session to check if it exists
#         print(f"Session data: {self.scope['session']}")
#         print(f"Session data: {self.scope['session'].items()}")

#         user = self.scope["user"]
#         self.group_name = None  
#         print(f"User authenticated: {user.is_authenticated}")  # Check if the user is authenticated
         
#         if user.is_authenticated:
#             self.group_name = f'user_{user.id}'
            
#             # Add this WebSocket connection to the user's group
#             await self.channel_layer.group_add(
#                 self.group_name,
#                 self.channel_name
#             )
            
#             # Accept the WebSocket connection
#             await self.accept()
#         else:
#             print("User is not authenticated, closing connection.")
#             await self.close()

#     async def disconnect(self, close_code):
#         if self.group_name:
#             await self.channel_layer.group_discard(
#                 self.group_name,
#                 self.channel_name
#             )

#     async def send_status_update(self, event):
#         status = event['status']
#         email = event['email']
#         timestamp = event['timestamp']

#         # Send the message to the WebSocket
#         await self.send(text_data=json.dumps({
#             'email': email,
#             'status': status,
#             'timestamp': timestamp
#         }))

