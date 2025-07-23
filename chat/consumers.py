import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, Visitor




class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope["user"]
        room_name = self.room_name

        # Handle typing indicator
        if "typing" in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "sender": user.username if user.is_authenticated else "visitor",
                    "typing": data["typing"]
                }
            )
            return

        # Handle normal messages
        if "message" in data:
            message = data["message"]

            if user.is_authenticated:
                await self.save_message(user, room_name, message)
                sender_type = "rm"
                sender = user.username
            else:
                await self.get_or_assign_rm(room_name)
                await self.save_message(None, room_name, message)
                sender_type = "visitor"
                sender = room_name

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": sender,
                    "sender_type": sender_type,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "sender_type": event["sender_type"]
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            "typing": event["typing"],
            "sender": event["sender"]
        }))

    @database_sync_to_async
    def save_message(self, sender, room_name, message):
        try:
            receiver = None
            if sender:
                try:
                    receiver = User.objects.get(username=room_name)
                except User.DoesNotExist:
                    try:
                        visitor = Visitor.objects.get(ip_address=room_name)
                        receiver = visitor.assigned_to
                    except Visitor.DoesNotExist:
                        receiver = None
            else:
                visitor = Visitor.objects.get(ip_address=room_name)
                receiver = visitor.assigned_to if visitor.assigned_to else None

            Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=message,
                room_name=room_name
            )
        except Exception as e:
            print("Error saving message:", e)

    @database_sync_to_async
    def get_or_assign_rm(self, ip):
        visitor, _ = Visitor.objects.get_or_create(ip_address=ip)
        if not visitor.assigned_to:
            rms = User.objects.filter(is_staff=True, is_active=True)
            if rms.exists():
                assigned = random.choice(rms)
                visitor.assigned_to = assigned
                visitor.save()
        return visitor.assigned_to
