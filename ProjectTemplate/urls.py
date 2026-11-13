"""
URL configuration for ProjectTemplate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from csp.decorators import csp_replace
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerSplitView,
)
from two_factor.admin import AdminSiteOTPRequiredMixin
from two_factor.urls import urlpatterns as tf_urls

# Require a verified OTP device for all admin access.
# Registered models and Jazzmin are unaffected.
admin.site.__class__ = type(
    "OTPAdminSite",
    (AdminSiteOTPRequiredMixin, admin.site.__class__),
    {},
)

docs_csp = csp_replace(
    {
        "style-src": (
            "'self'",
            "'unsafe-inline'",  # no NONCE here, or the browser ignores unsafe-inline
            "https://fonts.googleapis.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
        ),
        "worker-src": ("'self'", "blob:"),
    }
)

urlpatterns = [
    path("", include(tf_urls)),
    path("admin/", admin.site.urls),
    path("api/v1/", include(("Main.urls", "v1"), namespace="v1")),
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        docs_csp(SpectacularSwaggerSplitView.as_view(url_name="schema")),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        docs_csp(SpectacularRedocView.as_view(url_name="schema")),
        name="redoc",
    ),
]
