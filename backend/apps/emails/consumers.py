import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class EmailStatusConsumer(WebsocketConsumer):
    """
     Each authenticated user is subscribed to their own private group
    so that only they receive updates about their emails.
    """
    def connect(self):
        """
        Called when a browser client opens a WebSocket connection.
        Joins the user-specific channel group and accepts the connection.
        """
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            self.close()
            return

        #Unique group name created
        self.group_name = f"User_{self.user.id}_emails"
        print(f"Joined group: {self.group_name}")
        #Add this webscoket connection to the user specific group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        #accept the websocket handsake
        self.accept()
        print("WebSocket accepted")
        #confirm connection to the client

        self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Connected. Listening for email updates.."
        }))

    def disconnect(self, close_code):
        # called when browser disconnets
        # Only discard from group if we successfully joined one
        # (i.e., the user was authenticated during connect)

        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name,
                self.channel_name
            )

    def receive(self, text_data):
        pass

    def email_status_update(self, event):
        """
        Called when the Channel Layer broadcasts an email_status_update
        message to this consumer's group (triggered from Celery tasks.py).
        Forwards the status update to the connected browser via WebSocket.
        """
        print("Consumer received:", event)
        
        self.send(text_data=json.dumps({
            "type": "email_status_update",
            "email_id": event['email_id'],
            "status": event['status'],
            "sent_at": event.get("sent_at"),
            "error_message": event.get("error_message"),
        }))