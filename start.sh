#!/bin/sh

python manage.py migrate
python manage.py collectstatic --noinput

gunicorn boxing.wsgi:application --bind 127.0.0.1:8001 --workers 3 --threads 2 &

exec nginx -c /app/nginx.conf -g "daemon off;"
