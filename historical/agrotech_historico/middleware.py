"""
Middleware personalizado para AgroTech Histórico
"""
from django.utils.deprecation import MiddlewareMixin


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware que permite que el endpoint de healthcheck funcione sin SSL redirect
    y sin APPEND_SLASH para evitar 301 redirects que fallan el healthcheck de Railway
    """
    
    def process_request(self, request):
        # Si es el endpoint de healthcheck, marcar para evitar SSL redirect
        if request.path.startswith('/health'):
            request._healthcheck = True
        return None


class ConditionalSSLRedirectMiddleware(MiddlewareMixin):
    """
    Middleware que maneja SSL redirect excepto para healthcheck
    """
    
    def process_request(self, request):
        # Si es healthcheck, no redirigir a HTTPS
        if getattr(request, '_healthcheck', False):
            return None
        
        # Para otras rutas, aplicar SSL redirect si no es DEBUG
        from django.conf import settings
        if not settings.DEBUG:
            if not request.is_secure():
                # Redirigir a HTTPS
                from django.http import HttpResponsePermanentRedirect
                url = request.build_absolute_uri(request.get_full_path())
                secure_url = url.replace('http://', 'https://')
                return HttpResponsePermanentRedirect(secure_url)
        
        return None
