import hashlib

from django.core.cache import cache

THREAT_WINDOW_SECONDS = 60 * 60  # 1 hour


class ThreatTracker:
    KEY_PREFIX = "security:threat:"

    def _get_key(self, ip):
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        return f"{self.KEY_PREFIX}{ip_hash}"

    def add_score(self, ip, score):
        key = self._get_key(ip)

        # Initialize the counter only if it doesn't exist.
        # Its expiry is not reset by subsequent requests.
        cache.add(key, 0, timeout=THREAT_WINDOW_SECONDS)

        # Redis-backed cache supports atomic increments.
        return cache.incr(key, score)

    def get_score(self, ip):
        return cache.get(self._get_key(ip), 0)
