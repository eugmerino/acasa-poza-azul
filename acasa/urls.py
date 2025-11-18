from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

def custom_404_view(request, exception=None):
    """
    Vista simple para mostrar el template 404
    """
    return render(request, '404.html', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("core.urls")),
    path("", include("collection.urls")),
    path("", include("project.urls")),
    path("reuniones/", include("meeting.urls")),
    path("finanzas/", include("finance.urls")),
    path("reparaciones/", include("repair.urls")),
    path("bitacora/", include("audit.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all pattern para URLs no encontradas
urlpatterns += [
    re_path(r'^.*$', custom_404_view),
]
