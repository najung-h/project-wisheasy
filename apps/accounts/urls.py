from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("settings/", views.settings, name="settings"),
]
