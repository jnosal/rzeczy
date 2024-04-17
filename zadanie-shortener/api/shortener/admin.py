from django.contrib import admin

from . import models


@admin.register(models.ShortenedUrl)
class ShortenedUrlAdmin(admin.ModelAdmin):
    list_display = ("url", "signature", "created_at")
    search_fields = ("url", "signature")
