from django.db import models


# Create your models here.
class IPLocation(models.Model):
    """Cached geolocation for an IP address, resolved once and reused
    for every subsequent login attempt/failure from that same IP,
    instead of doing a fresh lookup on every axes event.
    """

    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    resolved_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ip_address} — {self.display}"

    @property
    def display(self):
        parts = [p for p in (self.city, self.region, self.country) if p]
        return ", ".join(parts) if parts else "Unknown"
