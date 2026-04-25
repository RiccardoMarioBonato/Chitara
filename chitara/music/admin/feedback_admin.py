from django.contrib import admin

from ..models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'submitted_at']
    search_fields = ['user__username']
