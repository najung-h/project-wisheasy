from django.urls import path
from . import views

app_name = "stations"
urlpatterns = [
    path("", views.station_info, name='station_info'),
]
