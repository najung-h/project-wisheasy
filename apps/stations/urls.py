from django.urls import path
from . import views

app_name = "stations"
urlpatterns = [
    path("", views.station_info, name="station_info"),
    # /api/stations/search/ 로 요청이 오도록 설정
    path("search/", views.search_stations, name="search_stations"),
]
