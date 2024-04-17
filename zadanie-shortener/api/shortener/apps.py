from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ShortenerAppConfig(AppConfig):
    name = "shortener"
    verbose_name = _("Shortened Urls")

    def ready(self):
        pass
