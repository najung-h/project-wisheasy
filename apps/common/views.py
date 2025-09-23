from django.http import JsonResponse
from django.shortcuts import render


# Create your views here.
def healthz(_request):
    return JsonResponse({"status": "ok"})


# 출발역/도착역을 입력받고 경로 안내를 제공한다.
def index(request):
    return render(request, "common/index.html")
