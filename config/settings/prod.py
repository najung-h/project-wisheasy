# config/settings/prod.py

from .base import *
import environ
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# environ 초기화
env = environ.Env()

DEBUG="True"  # 기본값 False


# .env 파일 로드
environ.Env.read_env(BASE_DIR / ".env.prod")

# 이제 설정 읽기
SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = ["wisheasy.site", "www.wisheasy.site"]

# EC2 추가
EC2 = env.list("EC2_HOST")
ALLOWED_HOSTS += EC2

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env.str("MYSQL_DATABASE"),
        "USER": env.str("MYSQL_USER"),
        "PASSWORD": env.str("MYSQL_PASSWORD"),
        "HOST": env.str("DB_HOST", default="localhost"),
        "PORT": env.int("DB_PORT", default=3306),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=0),
    }
}

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Django 로깅: 콘솔 + 파일(7일 보관)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}:{lineno} | {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file_rotating": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "django.log"),
            "when": "D",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "file_rotating"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console", "file_rotating"], "level": "WARNING", "propagate": False},
        "django.request": {"handlers": ["console", "file_rotating"], "level": "ERROR", "propagate": False},
    },
}