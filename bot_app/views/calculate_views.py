import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def calculate(request):

    result = json.loads(request.body)

    jsons = {
        "status": "success",
        "car_class": {
            "comfort": 230_000,
            "economy": 450_000,
            "standard": 500_000

        }
    }

    return JsonResponse(jsons)
