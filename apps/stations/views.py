from django.shortcuts import render
from django.http import JsonResponse
from apps.journeys.models import Stations

# Create your views here.
# 역 정보를 검색하고 제공한다.
def station_info(request):
    return render(request, "stations/station_info.html")

def search_stations(request):
    """
    역 이름 검색 자동완성 API
    /api/search/stations/?q=검색어
    """
    query = request.GET.get('q', None)
    results = []

    if query and len(query) > 0: # 검색어가 있고 0글자 이상일 때
        # 'name__icontains' : 대소문자 구분 없이 포함
        # 'name__startswith' : 해당 글자로 시작 (이걸 더 추천)
        stations = Stations.objects.filter(name__startswith=query)[:10] # 최대 10개

        for station in stations:
            results.append({
                'name': station.name,
                'line': station.line,
            })

    return JsonResponse({'results': results})