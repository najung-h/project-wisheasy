# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings 

class User(AbstractUser):
    """
    커스텀 유저 모델 (기본 user 상속)
    """
    pass

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,       # 현재 사용하는 User 모델과 연결
        on_delete=models.CASCADE,
        related_name='profile'
    )
    name = models.CharField(max_length=100, blank=True)
    nickname = models.CharField(max_length=50, blank=True)
    profile_image = models.URLField(blank=True)
    google_mail = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.user.username or self.google_mail} Profile"