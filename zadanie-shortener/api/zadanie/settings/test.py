import logging

from .base import *

DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_zadanie",
        "TEST_NAME": "test_zadanie",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "database",
        "ATOMIC_REQUESTS": False,
    }
}


CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
}

AUTH_PASSWORD_VALIDATORS = []
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]


logging.disable(logging.CRITICAL)
