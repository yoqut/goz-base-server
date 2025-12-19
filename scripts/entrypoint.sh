#!/bin/sh

python manage.py migrate
python manage.py createsuper --noinput
python manage.py collectstatic --noinput

exec "$@"
