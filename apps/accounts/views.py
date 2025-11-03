from django.shortcuts import render


# Create your views here.
def mypage(request):
    return render(request, "accounts/mypage.html")


# 사용자의 경로 안내 우선 순위를 설정한다.
def settings(request):
    return render(request, "accounts/settings.html")
