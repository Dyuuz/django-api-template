import logging

from axes.signals import user_locked_out, user_login_failed
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from ipware import get_client_ip as ipware_get_client_ip

from Main.geo_location.geo import resolve_and_store
from Main.tasks import send_login_alert

logger = logging.getLogger(__name__)


def get_client_ip(request):
    client_ip, is_routable = ipware_get_client_ip(request, proxy_count=1)
    # logger.info("XFF header: %r | REMOTE_ADDR: %r", request.META.get("HTTP_X_FORWARDED_FOR"), request.META.get("REMOTE_ADDR"))
    if client_ip:
        return client_ip
    # ipware couldn't confidently resolve a proxied IP (e.g. local dev
    # with no proxy in front, or a hop-count mismatch) — fall back to
    # whatever Django itself sees directly.
    return request.META.get("REMOTE_ADDR")


@receiver(user_login_failed)
def on_login_failed(sender, request, credentials, **kwargs):
    if request:
        resolve_and_store(get_client_ip(request))


@receiver(user_locked_out)
def on_locked_out(sender, request, username, ip_address=None, **kwargs):
    resolve_and_store(ip_address or (get_client_ip(request) if request else None))


@receiver(user_logged_in)
def on_login_success(sender, request, user, **kwargs):
    if not request:
        return

    ip_address = get_client_ip(request)
    location = resolve_and_store(ip_address)  # however this returns location today
    device = request.META.get("HTTP_USER_AGENT", "Unknown device")
    login_time = timezone.now().strftime("%d %b %Y, %H:%M %Z")

    send_login_alert.delay(
        user_id=user.pk,
        ip_address=ip_address or "Unknown",
        location=location or "Unknown location",
        device=device,
        login_time=login_time,
    )
