from django.shortcuts import render


# Create your views here.
# 사용자의 경로 안내 우선 순위를 설정한다.
def info(request):
    return render(request, "journeys/route.html")
