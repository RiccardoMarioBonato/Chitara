from django.contrib import admin

from ..models import Occasion


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
