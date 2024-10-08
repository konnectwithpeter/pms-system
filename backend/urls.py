from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.conf import settings

from django.views.generic import TemplateView

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("api/", include("base.urls")),
        path("index.html", TemplateView.as_view(template_name="index.html")),
        re_path(
            r"^(?!(api|admin|static|media|manifest.json|service-worker.js|service-worker.js.map).*$)",
            TemplateView.as_view(template_name="index.html"),
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
