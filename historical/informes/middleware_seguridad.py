"""
Middleware de gestión de sesiones con advertencias de timeout
Diferencia entre superusuarios (15 min) y usuarios regulares (30 min)
"""

from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.shortcuts import redirect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionTimeoutMiddleware:
    """
    Middleware para gestionar el timeout de sesiones con diferenciación por rol
    - Superusuarios: 15 minutos de inactividad
    - Usuarios regulares: 30 minutos de inactividad
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Código antes de que la vista sea llamada
        
        if request.user.is_authenticated:
            # Determinar timeout según tipo de usuario
            if request.user.is_superuser:
                session_age = settings.SUPERUSER_SESSION_TIMEOUT  # 15 minutos
                user_type = "superusuario"
            else:
                session_age = settings.SESSION_COOKIE_AGE  # 30 minutos
                user_type = "usuario"
            
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Calcular tiempo transcurrido desde última actividad
                try:
                    last_activity_time = datetime.fromisoformat(last_activity)
                    current_time = datetime.now()
                    elapsed_seconds = (current_time - last_activity_time).total_seconds()
                    
                    # Verificar si la sesión ha expirado
                    if elapsed_seconds > session_age:
                        logger.info(
                            f"Sesión expirada para {user_type} '{request.user.username}' "
                            f"después de {int(elapsed_seconds/60)} minutos de inactividad"
                        )
                        logout(request)
                        messages.warning(
                            request,
                            f'⏰ Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.'
                        )
                        return redirect('admin:login')
                    
                    # Calcular tiempo restante
                    remaining_seconds = session_age - elapsed_seconds
                    
                    # Si faltan menos de 5 minutos para expirar, mostrar advertencia
                    if 0 < remaining_seconds < settings.SESSION_TIMEOUT_WARNING:  # 5 minutos
                        remaining_minutes = int(remaining_seconds / 60) + 1
                        warning_key = f'timeout_warning_shown_{int(elapsed_seconds/60)}'
                        
                        if not request.session.get(warning_key):
                            icon = "🔐" if request.user.is_superuser else "⏰"
                            messages.warning(
                                request,
                                f'{icon} Tu sesión expirará en {remaining_minutes} minutos por inactividad.'
                            )
                            request.session[warning_key] = True
                            logger.info(
                                f"Advertencia de timeout enviada a {user_type} '{request.user.username}' "
                                f"({remaining_minutes} min restantes)"
                            )
                
                except (ValueError, TypeError) as e:
                    logger.error(f"Error al procesar timeout de sesión: {e}")
            
            # Actualizar última actividad
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Registrar tipo de usuario en sesión para referencia
            if 'user_type' not in request.session:
                request.session['user_type'] = user_type
                timeout_minutes = int(session_age / 60)
                logger.info(
                    f"{user_type.capitalize()} '{request.user.username}' autenticado "
                    f"(timeout: {timeout_minutes} minutos)"
                )
        
        response = self.get_response(request)
        
        # Código después de que la vista sea llamada
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware para agregar headers de seguridad
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # En producción, agregar estos headers adicionales:
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response['Content-Security-Policy'] = "default-src 'self'"
        
        return response
