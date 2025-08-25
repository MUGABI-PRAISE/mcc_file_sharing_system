import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

def office_group_name(office_id: int) -> str:
    return f"office_{office_id}"

def user_group_name(user_id: int) -> str:
    return f"user_{user_id}"

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user", AnonymousUser())
        if not user or not user.is_authenticated:
            # Optional: accept and only send public events; we’ll close to be strict.
            await self.close(code=4401)  # 4401: Unauthorized (custom)
            return

        self.groups_to_leave = []

        # Add user’s personal group
        self.user_group = user_group_name(user.id)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        self.groups_to_leave.append(self.user_group)

        # Add user’s office group (if any)
        self.office_group = None
        if getattr(user, "office_id", None):
            self.office_group = office_group_name(user.office_id)
            await self.channel_layer.group_add(self.office_group, self.channel_name)
            self.groups_to_leave.append(self.office_group)

        await self.accept()

        # Optional handshake message
        await self.send_json({
            "type": "ws.connected",
            "user_id": user.id,
            "office_id": getattr(user, "office_id", None),
        })

    async def disconnect(self, code):
        for grp in getattr(self, "groups_to_leave", []):
            await self.channel_layer.group_discard(grp, self.channel_name)


    # We keep the client->server `receive` minimal (optional ping/echo).
    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})
        elif msg_type == "chat.message":
            # Broadcast to user's office and personal groups
            message = data.get("message", "")
            payload = {"type": "chat.message", "message": message, "from_user": self.scope["user"].id}

            # Send to user group
            await self.channel_layer.group_send(
                self.user_group,
                {"type": "chat_message", "payload": payload}
            )

            # Send to office group if exists
            if self.office_group:
                await self.channel_layer.group_send(
                    self.office_group,
                    {"type": "chat_message", "payload": payload}
                )


    # Helper to send JSON
    async def send_json(self, payload: dict):
        await self.send(text_data=json.dumps(payload))

    # === Event handlers (names map from dots->underscores) ===

    async def file_shared(self, event):
        # Broadcast to recipients when a file is sent
        await self.send_json({
            "type": "file.shared",
            "payload": event.get("payload", {}),
        })

    async def file_deleted(self, event):
        await self.send_json({
            "type": "file.deleted",
            "payload": event.get("payload", {}),
        })

    async def file_read(self, event):
        await self.send_json({
            "type": "file.read",
            "payload": event.get("payload", {}),
        })


    async def chat_message(self, event):
        await self.send_json(event["payload"])
