# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    커스텀 유저 모델 (기본 user 상속)
    """
    pass