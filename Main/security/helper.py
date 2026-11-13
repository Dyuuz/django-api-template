import hashlib
import os


def anonymize_ip(ip):
    if not ip:
        return "unknown"

    secret = os.environ["IP_HASH_SECRET"]
    return hashlib.sha256(f"{secret}:{ip}".encode()).hexdigest()[:16]
