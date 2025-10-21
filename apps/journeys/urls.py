from django.urls import path
from . import views

app_name = "journeys"
urlpatterns = [
    path("", views.route, name="route"),
    path("leave/", views.leave, name="leave"),
]
