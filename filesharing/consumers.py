import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from asgiref.sync import sync_to_async
from .models import Chat, ChatParticipant, ChatMessage, Office, ChatMessageHide

def office_group_name(office_id: int) -> str:
    return f"office_{office_id}"

def user_group_name(user_id: int) -> str:
    return f"user_{user_id}"

def chat_group_name(chat_id: int) -> str:
    return f"chat_{chat_id}"

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user", AnonymousUser())
        if not user or not user.is_authenticated:
            # Optional: accept and only send public events; we’ll close to be strict.
            await self.close(code=4401)  # 4401: Unauthorized (custom) codes 4000-4999 are reserved for app use
            return

        self.groups_to_leave = []

        # Add user’s personal group
        self.user_group = user_group_name(user.id)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        self.groups_to_leave.append(self.user_group)
        print(self.groups_to_leave)

        # Add user’s office group (if any)
        self.office_group = None
        if getattr(user, "office_id", None):
            self.office_group = office_group_name(user.office_id)
            await self.channel_layer.group_add(self.office_group, self.channel_name)
            '''
                you can group add before you accept. but you cannot send before you accept.
            '''
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


##############################################################################3
#               IN-APP CHATTING CONSUMERS
###############################################################################
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user = user
        self.user_group = user_group_name(user.id)
        self.joined_chats = set()
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

        await self.send_json({"type": "ws.chat.connected", "user_id": user.id, "office_id": getattr(user, 'office_id', None)})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        for cid in list(self.joined_chats):
            await self.channel_layer.group_discard(chat_group_name(cid), self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            return

        action = data.get("action")

        if action == "subscribe":
            await self._subscribe(data)
        elif action == "unsubscribe":
            await self._unsubscribe(data)
        elif action == "send_message":
            await self._send_message(data)
        elif action == "edit_message":
            await self._edit_message(data)
        elif action == "delete_message":
            await self._delete_message(data)
        elif action == "read_messages":
            await self._read_messages(data)
        else:
            await self.send_json({"type": "error", "error": "Unknown action"})

    # ------------------ Actions ------------------

    async def _subscribe(self, data):
        chat_id = int(data.get("chat_id"))
        # membership check
        is_member = await sync_to_async(self._is_office_member)(chat_id, getattr(self.user, 'office_id', None))
        if not is_member:
            await self.send_json({"type": "error", "error": "Not a participant of this chat."})
            return

        await self.channel_layer.group_add(chat_group_name(chat_id), self.channel_name)
        self.joined_chats.add(chat_id)
        await self.send_json({"type": "chat.subscribed", "chat_id": chat_id})

        # On subscribe, mark undelivered messages as delivered for my office
        await sync_to_async(self._mark_delivered_for_office)(chat_id, self.user.office_id)

        # Notify of deliveries to update ticks (to everyone is fine)
        await self.channel_layer.group_send(
            chat_group_name(chat_id),
            {"type": "chat_event", "payload": {"type": "chat.message.delivered.bulk", "chat_id": chat_id, "office_id": self.user.office_id}}
        )

    async def _unsubscribe(self, data):
        chat_id = int(data.get("chat_id"))
        if chat_id in self.joined_chats:
            await self.channel_layer.group_discard(chat_group_name(chat_id), self.channel_name)
            self.joined_chats.discard(chat_id)
            await self.send_json({"type": "chat.unsubscribed", "chat_id": chat_id})

    async def _send_message(self, data):
        chat_id = int(data.get("chat_id"))
        content = (data.get("content") or "").strip()
        voice_note = data.get("voice_note")
        temp_id = data.get("temp_id")  # client temp id for optimistic UI

        if not content and not voice_note:
            await self.send_json({"type": "chat.ack", "temp_id": temp_id, "ok": False, "error": "Empty message"})
            return

        # membership check
        is_member = await sync_to_async(self._is_office_member)(chat_id, getattr(self.user, 'office_id', None))
        if not is_member:
            await self.send_json({"type": "chat.ack", "temp_id": temp_id, "ok": False, "error": "Not a participant"})
            return

        msg = await sync_to_async(self._create_message)(chat_id, self.user.id, content, voice_note)

        # Broadcast to chat group
        payload = await sync_to_async(self._serialize_message)(msg.id)
        payload["type"] = "chat.message.new"
        payload["chat_id"] = chat_id
        payload["temp_id"] = temp_id

        await self.channel_layer.group_send(
            chat_group_name(chat_id),
            {"type": "chat_event", "payload": payload}
        )

        # Also notify sender personal group with ack
        await self.send_json({"type": "chat.ack", "temp_id": temp_id, "ok": True, "message": self._message_public(payload)})

    async def _edit_message(self, data):
        message_id = int(data.get("message_id"))
        new_content = (data.get("new_content") or "").strip()
        if not new_content:
            await self.send_json({"type": "error", "error": "Empty edit content"})
            return

        result = await sync_to_async(self._edit_message_sync)(message_id, self.user.id, new_content)
        if isinstance(result, dict) and result.get('error'):
            await self.send_json({"type": "error", "error": result['error']})
            return

        msg = result
        serialized = await sync_to_async(self._serialize_message)(msg.id)
        payload = {"type": "chat.message.edited", "chat_id": msg.chat_id, "message": serialized}
        await self.channel_layer.group_send(chat_group_name(msg.chat_id), {"type": "chat_event", "payload": payload})

    async def _delete_message(self, data):
        message_id = int(data.get("message_id"))
        for_all = bool(data.get("for_all", False))

        result = await sync_to_async(self._delete_message_sync)(message_id, self.user.id, for_all)
        if isinstance(result, dict) and result.get('error'):
            await self.send_json({"type": "error", "error": result['error']})
            return

        chat_id = result['chat_id']
        if result['kind'] == 'all':
            # Broadcast deletion
            await self.channel_layer.group_send(
                chat_group_name(chat_id),
                {"type": "chat_event", "payload": {"type": "chat.message.deleted", "chat_id": chat_id, "message_id": message_id}}
            )
        else:
            # Hidden for me only → notify only requester to remove/hide
            await self.send_json({"type": "chat.message.hidden", "chat_id": chat_id, "message_id": message_id})

    async def _read_messages(self, data):
        chat_id = int(data.get("chat_id"))
        up_to_id = int(data.get("up_to_message_id"))
        if not await sync_to_async(self._is_office_member)(chat_id, getattr(self.user, 'office_id', None)):
            await self.send_json({"type": "error", "error": "Not a participant"})
            return

        count = await sync_to_async(self._mark_read_up_to)(chat_id, self.user.office_id, up_to_id)
        if count > 0:
            await self.channel_layer.group_send(
                chat_group_name(chat_id),
                {"type": "chat_event", "payload": {"type": "chat.message.read", "chat_id": chat_id, "office_id": self.user.office_id, "up_to_message_id": up_to_id}}
            )

    # ------------------ Helpers (sync) ------------------

    def _is_office_member(self, chat_id, office_id) -> bool:
        if not office_id:
            return False
        return Chat.objects.filter(id=chat_id, participants__id=office_id).exists()

    def _create_message(self, chat_id, user_id, content, voice_note):
        msg = ChatMessage.objects.create(chat_id=chat_id, sender_id=user_id, content=content, voice_note=voice_note)

        chat = Chat.objects.get(id=chat_id)
        sender_office_id = chat.created_by.__class__.objects.get(id=user_id).office_id  # ugly; better fetch user
        # safer:
        sender_office_id = msg.sender.office_id

        # mark delivered for all recipients (all offices except sender's)
        recipients = chat.participants.exclude(id=sender_office_id)
        for off in recipients:
            msg.delivered_to.add(off)
        return msg

    def _edit_message_sync(self, message_id, user_id, new_content):
        try:
            msg = ChatMessage.objects.select_related('chat', 'sender').get(id=message_id)
        except ChatMessage.DoesNotExist:
            return {'error': 'Message not found'}

        if msg.sender_id != user_id:
            return {'error': 'Cannot edit others messages'}

        if not msg.can_edit(msg.sender):
            return {'error': 'Edit window expired (15 minutes)'}

        msg.content = new_content
        msg.updated_at = timezone.now()
        msg.save()
        return msg

    def _delete_message_sync(self, message_id, user_id, for_all: bool):
        try:
            msg = ChatMessage.objects.select_related('chat', 'sender').get(id=message_id)
        except ChatMessage.DoesNotExist:
            return {'error': 'Message not found'}

        chat = msg.chat
        if for_all:
            if msg.sender_id != user_id:
                return {'error': 'Only the sender can delete for everyone'}
            msg.is_deleted = True
            msg.save()
            return {'kind': 'all', 'chat_id': chat.id}
        else:
            # delete for me (only for DIRECT chats and only for other people's messages)
            if chat.chat_type != 'direct':
                return {'error': 'Delete-for-me allowed only in direct chats'}
            if msg.sender_id == user_id:
                return {'error': 'Use delete-for-all for your own message'}
            ChatMessageHide.objects.get_or_create(message=msg, user_id=user_id)
            return {'kind': 'me', 'chat_id': chat.id}

    def _mark_delivered_for_office(self, chat_id, office_id):
        msgs = ChatMessage.objects.filter(chat_id=chat_id).exclude(sender__office_id=office_id).exclude(delivered_to=office_id)
        for m in msgs:
            m.delivered_to.add(office_id)

    def _mark_read_up_to(self, chat_id, office_id, up_to_id) -> int:
        msgs = ChatMessage.objects.filter(chat_id=chat_id, id__lte=up_to_id).exclude(sender__office_id=office_id).exclude(read_by=office_id)
        count = msgs.count()
        for m in msgs:
            m.read_by.add(office_id)
        return count

    def _serialize_message(self, message_id):
        msg = ChatMessage.objects.select_related('sender', 'chat').get(id=message_id)
        return {
            'id': msg.id,
            'chat': msg.chat_id,
            'sender': {
                'id': msg.sender_id,
                'first_name': msg.sender.first_name,
                'last_name': msg.sender.last_name,
                'office_id': getattr(msg.sender, 'office_id', None),
            },
            'content': msg.content,
            'voice_note': msg.voice_note,
            'is_deleted': msg.is_deleted,
            'created_at': msg.created_at.isoformat(),
            'updated_at': msg.updated_at.isoformat() if msg.updated_at else None,
            'delivered_office_ids': list(msg.delivered_to.values_list('id', flat=True)),
            'read_office_ids': list(msg.read_by.values_list('id', flat=True)),
        }

    def _message_public(self, payload):
        # Remove temp_id for generic payload if needed by clients
        p = dict(payload)
        p.pop('temp_id', None)
        return p

    # ------------------ Outbound ------------------
    async def chat_event(self, event):
        await self.send_json(event['payload'])

    async def send_json(self, payload: dict):
        await self.send(text_data=json.dumps(payload))
