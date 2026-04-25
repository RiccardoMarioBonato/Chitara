from django.contrib import admin

from ..models import SingerModel


@admin.register(SingerModel)
class SingerModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
