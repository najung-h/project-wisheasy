from django.urls import path
from . import views 
from apps.journeys.views import StationFacilityListView  # journeys 쪽 뷰 재사용

app_name = "stations_api"

urlpatterns = [
    # 역 검색 API
    path("search/", views.search_stations, name="search_stations"),
    # 역 편의시설 API
    path(
        "<int:station_id>/facilities/",
        StationFacilityListView.as_view(),
        name="station-facilities",
    ),
]
