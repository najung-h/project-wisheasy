from django.shortcuts import render


# Create your views here.
# 역 정보를 검색하고 제공한다.
def station_info(request):
    return render(request, "stations/station_info.html")
