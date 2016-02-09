from .http import Response


def handler404(request):
    data = {
        "errors": [
            {
                "status": "404",
                "detail": "{} not found".format(request.path),
            },
        ],
    }
    return Response(data, status=404)
