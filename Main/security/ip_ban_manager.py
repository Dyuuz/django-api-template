import hashlib
import ipaddress
import time

from django.core.cache import cache

BAN_DURATIONS = {
    "low": 15 * 60,  # 15 minutes
    "medium": 24 * 60 * 60,  # 24 hours
    "high": 7 * 24 * 60 * 60,  # 7 days
}


class IPBanManager:
    BAN_KEY_PREFIX = "security:ban:"

    def _get_key(self, ip):
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        return f"{self.BAN_KEY_PREFIX}{ip_hash}"

    @staticmethod
    def is_bannable(ip):
        try:
            return ipaddress.ip_address(ip).is_global
        except ValueError:
            return False

    def is_banned(self, ip):
        ban_data = cache.get(self._get_key(ip))

        if not ban_data:
            return None

        remaining = ban_data["duration"] - (time.time() - ban_data["banned_at"])

        if remaining <= 0:
            return None

        return {
            **ban_data,
            "remaining": int(remaining) + 1,
        }

    def ban(self, ip, score):
        if not self.is_bannable(ip):
            return None

        if score >= 30:
            duration = BAN_DURATIONS["high"]
            level = "high"

        elif score >= 20:
            duration = BAN_DURATIONS["medium"]
            level = "medium"

        elif score >= 10:
            duration = BAN_DURATIONS["low"]
            level = "low"

        else:
            return None

        ban_data = {
            "level": level,
            "duration": duration,
            "banned_at": time.time(),
        }

        cache.set(
            self._get_key(ip),
            ban_data,
            timeout=duration,
        )

        return ban_data
