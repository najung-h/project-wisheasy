# config/settings/prod.py

from .base import *
import environ

# environ 초기화
env = environ.Env()

DEBUG=False  # 기본값 False


# .env 파일 로드
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# 이제 설정 읽기
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = ["wisheasy.site", "www.wisheasy.site"]

# EC2 추가
EC2 = env.list("DJANGO_EC2_HOSTS", default=[])
ALLOWED_HOSTS += EC2

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env.str("MYSQL_DB"),
        "USER": env.str("MYSQL_USER"),
        "PASSWORD": env.str("MYSQL_PASSWORD"),
        "HOST": env.str("MYSQL_HOST", default="localhost"),
        "PORT": env.int("MYSQL_PORT", default=3306),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=0),
    }
}