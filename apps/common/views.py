from django.http import JsonResponse


# Create your views here.
def healthz(_request):
    return JsonResponse({"status": "ok"})
