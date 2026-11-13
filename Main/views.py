import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


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
                    "status": {"type": "string", "example": "success"},
                    "code": {"type": "string", "example": "API_HEALTHY"},
                    "message": {"type": "string", "example": "API is healthy."},
                },
            },
            500: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "error"},
                    "code": {"type": "string", "example": "HEALTH_CHECK_FAILED"},
                    "message": {
                        "type": "string",
                        "example": "An internal server error occurred.",
                    },
                },
            },
        },
    )
    def get(self, request):
        try:
            return Response(
                {
                    "status": "success",
                    "code": "API_HEALTHY",
                    "message": "API is healthy.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Health check failed")

            return Response(
                {
                    "status": "error",
                    "code": "HEALTH_CHECK_FAILED",
                    "message": "An internal server error occurred.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
