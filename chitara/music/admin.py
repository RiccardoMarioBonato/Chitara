from django.contrib import admin
from .models import Song, SingerModel, Feedback, Genre, Mood, Occasion, Theme


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(SingerModel)
class SingerModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'genre', 'mood', 'occasion', 'generation_status', 'is_shared', 'created_at']
    list_filter = ['genre', 'mood', 'occasion', 'generation_status', 'is_shared']
    search_fields = ['title']
    filter_horizontal = ['themes']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'submitted_at']
    search_fields = ['user__username']