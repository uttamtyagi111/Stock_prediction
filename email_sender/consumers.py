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
