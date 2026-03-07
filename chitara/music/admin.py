from django.contrib import admin
from .models import User, Song, SingerModel, Feedback

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'registered_at']
    search_fields = ['name', 'email']

@admin.register(SingerModel)
class SingerModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'genre', 'mood', 'occasion', 'generation_status', 'is_shared', 'created_at']
    list_filter = ['genre', 'mood', 'occasion', 'generation_status', 'is_shared']
    search_fields = ['title']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'submitted_at']
    search_fields = ['user__name']