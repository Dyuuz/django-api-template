import logging
import uuid

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from ipware import get_client_ip

from Main.log_configs.logging_context import set_request, set_request_id

from .security.helper import anonymize_ip
from .security.ip_ban_manager import IPBanManager
from .security.threat_detector import ThreatDetector
from .security.threat_tracker import ThreatTracker

logger = logging.getLogger(__name__)

detector = ThreatDetector()
tracker = ThreatTracker()
ban_manager = IPBanManager()


class ClientTypeMiddleware(MiddlewareMixin):
    """
    Middleware to enforce and validate client type for API requests.

    Features:
    1. Checks for the presence of the "X-Client-Type" header in incoming requests.
       - Raises a ValidationError if the header is missing.
       - Validates that the client type is one of the allowed types ("web" or "mobile").
       - Logs warnings if the client type is missing or invalid.

    2. Logs information about each request, including:
       - The client type detected.
       - The authenticated user email if available, or "anonymous" otherwise.

    3. Logs information about each request, including:
       - The client type detected.
       - The resolved client identity.
       - The authenticated user email if available, or "anonymous" otherwise.

    4. Attaches the validated client_type to the request object for use in views.

    5. Process the incoming request before it reaches the view.
       Only enforces client type validation for /api/ paths.
    """

    allowed_client_types = ("web",)

    def process_request(self, request):
        """
        Validate client type for API requests, excluding documentation.
        """

        # Paths that don't require client type validation
        exempt_paths = getattr(settings, "CLIENT_TYPE_EXEMPT_PATHS", [])

        if any(request.path.startswith(path) for path in exempt_paths):
            return None

        if not request.path.startswith("/api/"):
            return None

        # Get client type from headers
        client_type = request.headers.get("X-Client-Type", "").lower()

        # get client identity for logging
        user_email = getattr(request.user, "email", "anonymous")
        # logger.info(f"ClientType check: {client_type or 'missing'}", extra={"user_identity": user_email})
        logger.info(
            f"ClientType check: {client_type or 'missing'}",
            extra={"user_identity": "anonymous"},
        )

        # Check if client type header is missing
        if not client_type:
            logger.warning(
                "Missing X-Client-Type header", extra={"user_identity": user_email}
            )
            return JsonResponse(
                {
                    "status": "error",
                    "code": "INVALID_CLIENT_TYPE",
                    "message": "Missing X-Client-Type header",
                    # "data": {
                    #     "allowed_types": ["web", "mobile"]
                    # }
                },
                status=400,
            )

        # Check if client type is valid
        if client_type not in self.allowed_client_types:
            logger.warning(
                f"Invalid X-Client-Type '{client_type}'",
                extra={"user_identity": user_email},
            )
            return JsonResponse(
                {
                    "status": "error",
                    "code": "INVALID_CLIENT_TYPE",
                    "message": "Invalid X-Client-Type header",
                    # "data": {
                    #     "allowed_types": ["web", "mobile"]
                    # }
                },
                status=400,
            )

        # Attach client_type to request for use in views
        request.client_type = client_type
        return None


class LoggingContextMiddleware:
    """
    Middleware that initializes request-scoped logging context.

    Responsibilities:
        - Stores the current HTTP request in context storage.
        - Generates and assigns a unique request_id per request.

    This enables log filters to inject request_id and user_id
    dynamically at log emission time, supporting JWT/DRF authentication
    where user resolution occurs inside the view layer.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request(request)

        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        response = self.get_response(request)
        return response


class DebugIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.warning(
            "DEBUG_IP xff=%r remote_addr=%r",
            request.META.get("HTTP_X_FORWARDED_FOR"),
            request.META.get("REMOTE_ADDR"),
        )
        return self.get_response(request)


class BlockScannersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip, _ = get_client_ip(request)

        # 1. Reject previously banned IPs
        if ip:
            try:
                ban_data = ban_manager.is_banned(ip)

                if ban_data:
                    return HttpResponse(
                        status=429,
                        headers={"Retry-After": str(ban_data["remaining"])},
                    )

            except Exception:
                logger.exception("Unable to check IP ban status")

        # 2. Normalize request path
        path = request.path.lower().rstrip("/") or "/"

        # 3. Detect suspicious requests
        threat = detector.detect(path)

        if threat is None:
            return self.get_response(request)

        score = threat["score"]
        reason = threat["reason"]

        ban_details = None

        # 4. Track suspicious activity and enforce bans
        if ip and ban_manager.is_bannable(ip):
            try:
                total_score = tracker.add_score(ip, score)

                logger.warning(
                    "Threat tracking diagnostic | IP_HASH=%s | "
                    "Score=%s | Total=%s | Bannable=%s",
                    anonymize_ip(ip),
                    score,
                    total_score,
                    ban_manager.is_bannable(ip),
                )

                ban_details = ban_manager.ban(
                    ip,
                    total_score,
                )

            except Exception:
                logger.exception(
                    "Threat tracking failed for IP %s",
                    ip,
                )

        # 5. Record security event
        logger.warning(
            "Security event | IP_HASH=%s | Path=%s | Method=%s | "
            "Reason=%s | Score=%s | Ban=%s",
            anonymize_ip(ip),
            path,
            request.method,
            reason,
            score,
            ban_details["level"] if ban_details else "none",
        )

        # 6. Reject the suspicious request
        return HttpResponse(status=403)

