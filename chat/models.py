from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    sender = models.ForeignKey(
        User,
        related_name="sent_messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True  # Visitor or unauthenticated sender
    )
    receiver = models.ForeignKey(
        User,
        related_name="received_messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True  # Receiver could be null for anonymous-only chats
    )
    content = models.TextField()
    room_name = models.CharField(
        max_length=100,
        null=True,
        blank=True  # Used to group chats by visitor IP or slug
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.sender and self.receiver:
            return f"{self.sender} -> {self.receiver}: {self.content[:20]}"
        elif self.sender:
            return f"{self.sender} -> VisitorRoom({self.room_name}): {self.content[:20]}"
        else:
            return f"Visitor({self.room_name}) -> {self.receiver or 'Unknown'}: {self.content[:20]}"


class Visitor(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_visitors"
    )

    def __str__(self):
        return self.ip_address

class VisitorAssignment(models.Model):
    visitor = models.OneToOneField(Visitor, on_delete=models.CASCADE)
    assigned_rm = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.visitor.ip_address} → {self.assigned_rm.username if self.assigned_rm else 'Unassigned'}"
