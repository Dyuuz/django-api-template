from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return [
            "homepage",
            "about",
            "services",
            "sectors",
            "results",
            "faqs",
            "contact",
        ]

    def location(self, item):
        return reverse(item)
