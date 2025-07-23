from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from django.contrib.auth.models import User
from .models import *



@login_required
def chat_room(request, room_name):
    visitors = Visitor.objects.all()
    search_query = request.GET.get('search', '')
    users = User.objects.exclude(id=request.user.id)

    # 1. Fetch all messages in this room (visitor IP or username)
    chats = Message.objects.filter(room_name=room_name)

    # 2. Include direct messages (user ↔ user)
    chats |= Message.objects.filter(
        (Q(sender__username=room_name) & Q(receiver=request.user)) |
        (Q(sender=request.user) & Q(receiver__username=room_name))
    )

    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))

    chats = chats.order_by('timestamp')

    # Last messages for sidebar
    user_last_messages = []
    for user in users:
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) |
            (Q(receiver=request.user) & Q(sender=user))
        ).order_by('-timestamp').first()

        user_last_messages.append({
            'user': user,
            'last_message': last_message
        })

    fallback_time = timezone.make_aware(datetime.min)
    user_last_messages.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else fallback_time,
        reverse=True
    )

    return render(request, 'chat.html', {
        'room_name': room_name,
        'chats': chats,
        'users': users,
        'visitors': visitors,
        'user_last_messages': user_last_messages,
        'search_query': search_query,
    })





def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip






def visitor_chat_view(request):
    ip = get_client_ip(request)
    visitor, created = Visitor.objects.get_or_create(ip_address=ip)

    # Fetch previous chat history for this visitor
    chats = Message.objects.filter(room_name=ip).order_by('timestamp')

    return render(request, "visitor_chat.html", {
        "room_name": ip,
        "chats": chats
    })

