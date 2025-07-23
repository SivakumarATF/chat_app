from django.urls import path
from . import views

urlpatterns = [
    path('chat/<str:room_name>/', views.chat_room, name='chat'),
    path('visitor-chat/', views.visitor_chat_view, name='visitor_chat'),  # <-- Add this
]
