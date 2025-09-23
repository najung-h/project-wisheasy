from django.urls import path
from .views import healthz
from . import views

app_name = "common"
urlpatterns = [
    path("", views.index, name="index"),
    path("healthz/", healthz, name="healthz"),
]
