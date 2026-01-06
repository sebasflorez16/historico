"""
Middleware personalizado para seguridad de sesiones
"""

from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SessionAbsoluteTimeoutMiddleware:
    """
    Middleware para implementar timeout absoluto de sesión.
    Cierra la sesión después de un tiempo máximo, incluso con actividad.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Verificar tiempo absoluto de sesión
            session_start = request.session.get('session_start_time')
            
            if not session_start:
                # Primera vez que se detecta esta sesión
                request.session['session_start_time'] = timezone.now().isoformat()
            else:
                # Calcular tiempo transcurrido
                session_start_time = timezone.datetime.fromisoformat(session_start)
                elapsed_time = (timezone.now() - session_start_time).total_seconds()
                
                # Verificar si excede el timeout absoluto
                max_timeout = getattr(settings, 'SESSION_ABSOLUTE_TIMEOUT', 7200)  # 2 horas por defecto
                
                if elapsed_time > max_timeout:
                    logger.info(f"Sesión expirada para usuario: {request.user.username} (timeout absoluto)")
                    logout(request)
                    # Redirigir al login con mensaje
                    request.session['session_expired'] = True
                    return redirect('informes:login')
        
        response = self.get_response(request)
        return response
