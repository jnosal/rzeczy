from django.db import models
from django.utils.translation import gettext_lazy as _


class ShortenedUrl(models.Model):
    signature = models.CharField(max_length=100, primary_key=True, db_index=True)
    url = models.URLField(blank=False, null=False, db_index=True, unique=True)
    created_at = models.DateTimeField(
        _("Created"), auto_now_add=True, blank=True, null=True
    )
    updated_at = models.DateTimeField(
        _("Updated"), auto_now=True, blank=True, null=True
    )
