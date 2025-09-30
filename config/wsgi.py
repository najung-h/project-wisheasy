"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django는 WSGI 규약을 따르면서,
# 진입점을 app(fastapi)가 아니라 application이라는 객체로 정해놓음
application = get_wsgi_application()
