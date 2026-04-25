from django.contrib import admin

from ..models import Song


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'genre', 'mood', 'occasion',
                    'generation_status', 'is_shared', 'created_at']
    list_filter = ['genre', 'mood', 'occasion', 'generation_status', 'is_shared']
    search_fields = ['title']
    filter_horizontal = ['themes']
