#!/bin/bash

cd /carmagnole



python manage.py check
python manage.py makemigrations utils
python manage.py makemigrations authenticate
python manage.py makemigrations
python manage.py migrate authenticate
python manage.py migrate utils
python manage.py migrate



uvicorn carmagnole.asgi:application --reload --host 0.0.0.0 --port 8000 \

    --log-level debug 
