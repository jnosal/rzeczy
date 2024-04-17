#!/bin/bash
find . \( -name __pycache__ -o -name '*.pyc' \) -delete
DJANGO_SETTINGS_MODULE=zadanie.settings.test py.test --cov=. -s -v "$@"
