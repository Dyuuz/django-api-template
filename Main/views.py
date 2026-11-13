from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Health Check"],
        summary="Check API health",
        description="Returns the current API health status.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                },
            }
        },
    )
    def get(self, request):
        return Response({"status": "healthy"})
