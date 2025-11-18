from django.shortcuts import render
from django.http import JsonResponse
from apps.journeys.models import Station

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

    if query and len(query) > 0:
        
        # 1. 'Station' 모델에서 'name'으로 검색합니다.
        stations = Station.objects.filter(
            name__startswith=query
        )
        
        # 2. 'prefetch_related'로 N+1 쿼리 문제를 방지합니다.
        #    (각 Station에 연결된 Line 정보 10개를 미리 한 번에 가져옴)
        stations = stations.prefetch_related('lines')[:10]

        # 3. 각 Station 객체를 순회합니다.
        for s in stations:
            # 4. 해당 역(s)에 연결된 모든 호선(l)의 이름을 리스트로 만듭니다.
            #    (예: ["2호선", "신분당선"])
            line_names = [l.name for l in s.lines.all()]
            
            # 5. 리스트를 ", "로 연결된 하나의 문자열로 만듭니다.
            #    (예: "2호선, 신분당선")
            lines_str = ", ".join(line_names)
            
            results.append({
                'name': s.name,    # 역 이름 (예: "강남")
                'line': lines_str  # 호선 이름 (예: "2호선, 신분당선")
            })
        
        # 최종 결과 리스트에서 10개만 반환
        return JsonResponse({'results': results[:10]})

    # 검색어가 없는 경우 빈 리스트 반환
    return JsonResponse({'results': []})