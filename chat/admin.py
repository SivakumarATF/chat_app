from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'short_content', 'timestamp')
    list_filter = ('sender', 'receiver', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    ordering = ('-timestamp',)

    def short_content(self, obj):
        return (obj.content[:50] + '...') if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
