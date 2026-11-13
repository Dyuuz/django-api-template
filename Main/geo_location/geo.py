"""IP -> location resolution, backed by a local MaxMind GeoLite2
database (no external API calls, no rate limits). Results are cached
in IPLocation so each unique IP is only ever looked up once.
"""

import logging

import geoip2.database
from django.conf import settings

from Main.models import IPLocation

logger = logging.getLogger(__name__)

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = geoip2.database.Reader(str(settings.GEOIP2_DB_PATH))
    return _reader


def resolve_and_store(ip_address):
    """Look up ip_address and persist it to IPLocation, unless it's
    already cached. Returns a human-readable "City, Region, Country"
    string (or None if nothing could be resolved).
    """
    if not ip_address:
        return None

    existing = IPLocation.objects.filter(ip_address=ip_address).first()
    if existing:
        return _format_location(existing)

    try:
        response = _get_reader().city(ip_address)
    except Exception:
        # Local/private IPs (127.0.0.1, 10.x.x.x, etc.) and lookup
        # misses land here — nothing meaningful to store, skip silently.
        logger.debug("Could not resolve location for IP %s", ip_address)
        return None

    location = IPLocation.objects.update_or_create(
        ip_address=ip_address,
        defaults={
            "city": response.city.name or "",
            "region": response.subdivisions.most_specific.name or "",
            "country": response.country.name or "",
        },
    )[0]
    return _format_location(location)


def _format_location(location):
    parts = [p for p in (location.city, location.region, location.country) if p]
    return ", ".join(parts) if parts else None
