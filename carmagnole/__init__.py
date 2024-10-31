from __future__ import absolute_import, unicode_literals

from .celery import app as celery_app
from celery._state import _set_current_app

__all__ = ('celery_app',)
