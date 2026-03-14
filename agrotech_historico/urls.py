"""
Configuración de URLs para AgroTech Histórico
Sistema de análisis satelital agrícola
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve as static_serve

def redirigir_a_login(request):
    """Redirige la raíz al login"""
    return redirect('informes:login')

@csrf_exempt
def healthcheck(request):
    """Endpoint para Railway healthcheck - retorna 200 OK sin redirecciones"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AgroTech Histórico',
        'database': 'connected'
    }, status=200)

urlpatterns = [
    # Healthcheck para Railway - acepta con o sin trailing slash
    re_path(r'^health/?$', healthcheck, name='healthcheck'),
    path("admin/", admin.site.urls),
    path("", redirigir_a_login, name='home'),
    path("informes/", include('informes.urls')),
    
    # Sistema Demo - Links únicos (AISLADO - sin autenticación)
    path("demo/", include('informes.urls_demo', namespace='demo')),
]

# Servir archivos media en desarrollo Y producción
# En producción (DEBUG=False), static() no genera patterns.
# Usamos re_path con django.views.static.serve para servir media siempre.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Producción: servir media files (generados en runtime, ej. heatmaps demo)
    # Los archivos estáticos los sirve WhiteNoise, pero media no.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', static_serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
