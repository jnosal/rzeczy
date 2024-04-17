#!/bin/bash
echo "Waiting for postgres to get up and running..."
while ! nc -z database 5432; do
  echo "waiting for postgress listening..."
  sleep 0.1
done
echo "PostgreSQL started"
python3.11 manage.py migrate --settings=zadanie.settings.dev
python3.11 manage.py collectstatic --noinput --settings=zadanie.settings.dev
python3.11 manage.py runserver 0.0.0.0:4444 --settings=zadanie.settings.dev
