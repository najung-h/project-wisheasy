# config/settings/local.py

from .base import *

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# End session when browser closes (session cookie)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Local runs over HTTP → allow non-secure cookies
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False