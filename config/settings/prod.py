# config/settings/prod.py

from .base import *

# base.py에서 env 객체가 이미 초기화되었으므로, 여기서는 .env.prod 파일만 로드합니다.
# 이 파일의 변수들이 base.py의 설정을 덮어쓰게 됩니다.
environ.Env.read_env(BASE_DIR / ".env.prod")

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