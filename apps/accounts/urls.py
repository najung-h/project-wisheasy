from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("mypage/", views.mypage, name="mypage"),
    path("settings/", views.settings, name="settings"),
]
