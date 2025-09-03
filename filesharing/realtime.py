from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def office_group(office_id: int) -> str:
    return f"office_{office_id}"

def user_group(user_id: int) -> str:
    return f"user_{user_id}"

def chat_group_name(chat_id: int) -> str:
    return f"chat_{chat_id}"

channel_layer = get_channel_layer()

def send_to_office(office_id: int, type_: str, payload: dict):
    async_to_sync(channel_layer.group_send)(
        office_group(office_id),
        {"type": type_.replace(".", "_"), "payload": payload}
    )

def send_to_user(user_id: int, type_: str, payload: dict):
    async_to_sync(channel_layer.group_send)(
        user_group(user_id),
        {"type": type_.replace(".", "_"), "payload": payload}
    )

def broadcast_chat_event(chat_id: int, type_: str, payload: dict):
    async_to_sync(channel_layer.group_send)(
        chat_group_name(chat_id),
        {"type": type_.replace(".", "_"), "payload": payload}
    )
