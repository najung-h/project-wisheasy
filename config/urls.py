"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include(("apps.common.urls", "common"), namespace="common")),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("allauth.urls")),  # allauth는 그대로
    path("stations/", include(("apps.stations.urls", "stations"), namespace="stations")),
    path("journeys/", include(("apps.journeys.urls", "journeys"), namespace="journeys")),
    # /api/stations/로 시작하는 모든 URL은 stations.urls로 위임
    path("api/stations/", include(("apps.stations.api_urls", "stations_api"), namespace="stations_api")),
]
