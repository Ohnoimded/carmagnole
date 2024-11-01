# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11.5
FROM python:${PYTHON_VERSION}-slim-bookworm as base
# FROM python:${PYTHON_VERSION}-alpine as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /carmagnole


ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    cron \
    memcached \
 && rm -rf /var/lib/apt/lists/*

## Alpine
# RUN apk add --no-cache \
#     postgresql-client \
#     cronie \
#     memcached

# # Install build dependencies and Python packages
# RUN apk add --no-cache --virtual .build-deps gcc musl-dev libpq-dev \
#     && apk add --no-cache bash

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt 
    # pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.7.1/en_core_web_md-3.7.1.tar.gz

# This is only to download spacy language models. 
# RUN  python -m spacy download en_core_web_md
RUN --mount=type=cache,target=/root/.cache python -m spacy download en_core_web_md

# # Switch to the non-privileged user to run the application.
# USER appuser

COPY . .

EXPOSE 8000

###############################################
#  THings to do
# change user to nonprivileged
# move etl to a separate container.
#######################################

# Run the application using Gunicorn
# CMD ["gunicorn", ".venv.Lib.site-packages.asgiref.wsgi", "--bind=0.0.0.0:8000"]
# CMD ["python", "manage.py","runserver"]
CMD ["bash", "django_build_init.sh"]
# CMD ["sh", "build_init.sh"]