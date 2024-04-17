from django.urls import re_path

from . import api

app_name = "shortener"

urlpatterns = [
    re_path(r"^shorten$", api.ShortenLinkApiView.as_view(), name="shorten"),
    re_path(r"^(?P<signature>\w+)$", api.shortened_link_redirect_view, name="redirect"),
]
