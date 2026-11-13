from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import TemplateView

from Main.sitemaps import StaticViewSitemap
from Main.views import HealthCheckAPIView

urlpatterns = []

urlpatterns += [
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"static": StaticViewSitemap}},
        name="sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("health-check/", HealthCheckAPIView.as_view(), name="health-check"),
]

BASE_DIR = Path(__file__).resolve().parent.parent

if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=BASE_DIR / "Main/static")
