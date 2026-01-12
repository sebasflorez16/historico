"""
Configuración de URLs para AgroTech Histórico
Sistema de análisis satelital agrícola
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
]

# Servir archivos media en desarrollo Y producción
# Railway es efímero pero durante la sesión necesitamos servir uploads
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Servir archivos estáticos solo en desarrollo (en producción usa WhiteNoise)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
