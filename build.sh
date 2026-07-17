#!/usr/bin/env bash
set -b errexit

python -m pip install --upgrade pip
python -m pip install --r requirements.xt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py ensure_superuser
