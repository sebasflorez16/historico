"""
Servicio de Email para AgroTech Histórico
Gestión del envío de invitaciones por correo electrónico
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para gestionar el envío de emails de invitaciones
    """
    
    @staticmethod
    def notificar_nueva_parcela_admin(invitacion, parcela):
        """
        Notificar al administrador cuando un cliente crea una parcela
        
        Args:
            invitacion: Instancia de ClienteInvitacion
            parcela: Instancia de Parcela recién creada
            
        Returns:
            dict: Resultado del envío
        """
        try:
            # Email del administrador
            admin_email = getattr(
                settings, 
                'ADMIN_EMAIL', 
                'agrotechdigitalcolombia@gmail.com'
            )
            
            # Preparar el contexto
            contexto = {
                'invitacion': invitacion,
                'parcela': parcela,
                'cliente': invitacion.nombre_cliente,
                'email_cliente': invitacion.email_cliente,
                'telefono_cliente': invitacion.telefono_cliente,
                'area_hectareas': parcela.area_hectareas,
                'tipo_cultivo': parcela.tipo_cultivo,
                'fecha_registro': parcela.fecha_registro,
                'empresa': 'AgroTech Histórico',
                'fecha_actual': timezone.now()
            }
            
            # Asunto del email
            asunto = f"🌾 Nueva Parcela Registrada - {invitacion.nombre_cliente}"
            
            # Mensaje de texto
            mensaje_texto = f"""
NUEVA PARCELA REGISTRADA - AGROTECH HISTÓRICO
{'=' * 60}

Cliente: {invitacion.nombre_cliente}
Email: {invitacion.email_cliente or 'No proporcionado'}
Teléfono: {invitacion.telefono_cliente or 'No proporcionado'}

DATOS DE LA PARCELA:
---
Nombre: {parcela.nombre}
Área: {parcela.area_hectareas:.2f} hectáreas
Tipo de Cultivo: {parcela.tipo_cultivo or 'No especificado'}
Fecha de Registro: {parcela.fecha_registro.strftime('%d/%m/%Y %H:%M')}

INVITACIÓN:
---
Token: {invitacion.token}
Costo del Servicio: ${invitacion.costo_servicio} COP
Estado de Pago: {'PAGADO' if invitacion.pagado else 'PENDIENTE'}

PRÓXIMOS PASOS:
---
1. Revisar los datos de la parcela en el sistema
2. Sincronizar con EOSDA para obtener datos satelitales
3. Contactar al cliente para confirmar el inicio del análisis
4. Verificar el estado del pago si está pendiente

Accede al sistema para gestionar esta parcela:
http://127.0.0.1:8000/informes/parcelas/{parcela.id}/

---
Notificación automática de AgroTech Histórico
{timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            # Intentar renderizar versión HTML si existe
            mensaje_html = None
            try:
                mensaje_html = render_to_string(
                    'informes/emails/notificacion_admin_parcela.html',
                    contexto
                )
            except Exception:
                pass  # Si no existe la plantilla, usar solo texto
            
            # Enviar email
            remitente = getattr(
                settings, 
                'DEFAULT_FROM_EMAIL', 
                'agrotechdigitalcolombia@gmail.com'
            )
            
            resultado = send_mail(
                subject=asunto,
                message=mensaje_texto,
                from_email=remitente,
                recipient_list=[admin_email],
                html_message=mensaje_html,
                fail_silently=False
            )
            
            if resultado:
                logger.info(f"Notificación enviada al admin sobre nueva parcela: {parcela.nombre}")
                return {
                    'exito': True,
                    'mensaje': f'Notificación enviada al administrador'
                }
            else:
                return {
                    'exito': False,
                    'error': 'El servidor no confirmó el envío de la notificación'
                }
                
        except Exception as e:
            logger.error(f"Error notificando al admin sobre nueva parcela: {str(e)}")
            return {
                'exito': False,
                'error': f'Error enviando notificación: {str(e)}'
            }
    
    @staticmethod
    def enviar_invitacion(invitacion, url_completa):
        """
        Enviar email de invitación a un cliente
        
        Args:
            invitacion: Instancia de ClienteInvitacion
            url_completa: URL completa de la invitación
        
        Returns:
            dict: Resultado del envío
        """
        try:
            # Validar que el email esté configurado
            if not invitacion.email_cliente:
                return {
                    'exito': False,
                    'error': 'El cliente no tiene email configurado'
                }
            
            # Validar configuración de email
            from django.conf import settings
            if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
                return {
                    'exito': False,
                    'error': 'Configuración de email no encontrada en el sistema'
                }
            
            if not hasattr(settings, 'EMAIL_HOST_PASSWORD') or not settings.EMAIL_HOST_PASSWORD:
                return {
                    'exito': False,
                    'error': 'Contraseña de email no configurada. Configure EMAIL_PASSWORD en .env'
                }
            
            # Configurar el contexto para la plantilla
            contexto = {
                'invitacion': invitacion,
                'url_invitacion': url_completa,
                'empresa': 'AgroTech Histórico',
                'fecha_actual': timezone.now(),
                'dias_vigencia': (invitacion.fecha_expiracion - timezone.now()).days
            }
            
            # Renderizar el contenido del email
            asunto = f"Invitación para análisis satelital agrícola - {invitacion.nombre_cliente}"
            
            mensaje_texto = render_to_string(
                'informes/emails/invitacion.txt',
                contexto
            )
            
            # Intentar renderizar versión HTML si existe la plantilla
            mensaje_html = None
            try:
                mensaje_html = render_to_string(
                    'informes/emails/invitacion.html',
                    contexto
                )
            except Exception as html_error:
                logger.warning(f"No se pudo cargar plantilla HTML: {html_error}")
            
            # Configurar remitente
            remitente = getattr(
                settings, 
                'DEFAULT_FROM_EMAIL', 
                'agrotechdigitalcolombia@gmail.com'
            )
            
            # Enviar el email con manejo detallado de errores
            from django.core.mail import send_mail
            from django.core.mail.backends.smtp import EmailBackend
            import socket
            import ssl
            
            try:
                resultado = send_mail(
                    subject=asunto,
                    message=mensaje_texto,
                    from_email=remitente,
                    recipient_list=[invitacion.email_cliente],
                    html_message=mensaje_html,
                    fail_silently=False
                )
                
                if resultado:
                    logger.info(f"Email enviado exitosamente a {invitacion.email_cliente}")
                    return {
                        'exito': True,
                        'mensaje': f'Invitación enviada exitosamente a {invitacion.email_cliente}'
                    }
                else:
                    return {
                        'exito': False,
                        'error': 'El servidor de correo no confirmó el envío'
                    }
                    
            except ssl.SSLError as ssl_error:
                error_msg = f"Error de SSL/TLS: {str(ssl_error)}"
                logger.error(f"Error SSL enviando email: {error_msg}")
                return {
                    'exito': False,
                    'error': f"Error de seguridad en el servidor de correo: {error_msg}. Verifique la configuración SSL/TLS."
                }
                
            except socket.timeout as timeout_error:
                error_msg = "Tiempo de espera agotado"
                logger.error(f"Timeout enviando email: {timeout_error}")
                return {
                    'exito': False,
                    'error': f"Tiempo de espera agotado conectando al servidor de correo. Verifique su conexión a internet."
                }
                
            except socket.gaierror as dns_error:
                error_msg = "Error de DNS"
                logger.error(f"Error DNS enviando email: {dns_error}")
                return {
                    'exito': False,
                    'error': f"No se pudo resolver el servidor de correo. Verifique su conexión a internet."
                }
                
            except Exception as email_error:
                error_msg = str(email_error)
                logger.error(f"Error general enviando email: {error_msg}")
                
                # Errores específicos de autenticación
                if "authentication" in error_msg.lower() or "login" in error_msg.lower():
                    return {
                        'exito': False,
                        'error': 'Error de autenticación: Verifique el usuario y contraseña del email. Use una contraseña de aplicación si tiene 2FA activado.'
                    }
                elif "certificate" in error_msg.lower():
                    return {
                        'exito': False,
                        'error': 'Error de certificado SSL: El servidor de correo tiene problemas de seguridad.'
                    }
                else:
                    return {
                        'exito': False,
                        'error': f'Error enviando email: {error_msg}'
                    }
                
        except Exception as e:
            logger.error(f"Error crítico enviando invitación por email: {str(e)}")
            return {
                'exito': False,
                'error': f'Error del sistema: {str(e)}'
            }
    
    @staticmethod
    def generar_mensaje_whatsapp(invitacion, url_completa):
        """
        Generar mensaje de WhatsApp para invitación
        
        Args:
            invitacion: Instancia de ClienteInvitacion
            url_completa: URL completa de la invitación
        
        Returns:
            str: Mensaje formateado para WhatsApp
        """
        dias_vigencia = (invitacion.fecha_expiracion - timezone.now()).days
        
        mensaje = f"""🌾 *AgroTech Histórico*

Hola {invitacion.nombre_cliente}!

Has sido invitado/a a registrar una parcela para análisis satelital agrícola.

📊 *Servicio:* {invitacion.descripcion_servicio}
💰 *Costo:* ${invitacion.costo_servicio} COP
⏱️ *Vigencia:* {dias_vigencia} días

Para registrar tu parcela, ingresa al siguiente enlace:
{url_completa}

¡Esperamos poder ayudarte con el análisis de tu cultivo!

_Mensaje automático de AgroTech Histórico_"""
        
        return mensaje
    
    @staticmethod
    def probar_configuracion_email(email_destino="agrotechdigitalcolombia@gmail.com"):
        """
        Probar la configuración de email enviando un mensaje de prueba
        
        Args:
            email_destino: Email donde enviar la prueba
            
        Returns:
            dict: Resultado de la prueba
        """
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            import socket
            import ssl
            
            # Validar configuración básica
            validacion = EmailService.validar_configuracion_email()
            if not validacion['valido']:
                return validacion
            
            # Preparar email de prueba
            asunto = "Prueba de configuración - AgroTech Histórico"
            mensaje = """
Esta es una prueba automática del sistema de email de AgroTech Histórico.

Si recibe este mensaje, la configuración de correo está funcionando correctamente.

Fecha: {fecha}
Sistema: AgroTech Histórico
Estado: Operativo

---
Este es un mensaje automático de prueba.
            """.format(fecha=timezone.now().strftime("%d/%m/%Y %H:%M:%S"))
            
            remitente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'agrotechdigitalcolombia@gmail.com')
            
            # Enviar email de prueba
            try:
                resultado = send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=remitente,
                    recipient_list=[email_destino],
                    fail_silently=False
                )
                
                if resultado:
                    return {
                        'exito': True,
                        'mensaje': f'Email de prueba enviado exitosamente a {email_destino}'
                    }
                else:
                    return {
                        'exito': False,
                        'error': 'El servidor no confirmó el envío del email de prueba'
                    }
                    
            except Exception as e:
                return {
                    'exito': False,
                    'error': f'Error enviando email de prueba: {str(e)}'
                }
                
        except Exception as e:
            return {
                'exito': False,
                'error': f'Error en prueba de email: {str(e)}'
            }
    
    @staticmethod
    def validar_configuracion_email():
        """
        Validar que la configuración de email esté correcta
        
        Returns:
            dict: Estado de la configuración
        """
        try:
            from django.conf import settings
            
            # Verificar configuración básica
            configuracion_requerida = [
                ('EMAIL_HOST', 'Servidor SMTP'),
                ('EMAIL_PORT', 'Puerto SMTP'),
                ('EMAIL_HOST_USER', 'Usuario de email'),
                ('EMAIL_HOST_PASSWORD', 'Contraseña de email')
            ]
            
            configuracion_faltante = []
            configuracion_valores = {}
            
            for config, descripcion in configuracion_requerida:
                valor = getattr(settings, config, None)
                if not valor:
                    configuracion_faltante.append(descripcion)
                else:
                    configuracion_valores[config] = valor
            
            if configuracion_faltante:
                return {
                    'valido': False,
                    'error': f'Configuración faltante: {", ".join(configuracion_faltante)}'
                }
            
            # Verificar configuración específica de AgroTech
            email_configurado = configuracion_valores.get('EMAIL_HOST_USER', '')
            if email_configurado != 'agrotechdigitalcolombia@gmail.com':
                return {
                    'valido': False,
                    'error': f'Email configurado: {email_configurado}, esperado: agrotechdigitalcolombia@gmail.com'
                }
            
            # Verificar configuración de servidor Gmail
            if configuracion_valores.get('EMAIL_HOST') != 'smtp.gmail.com':
                return {
                    'valido': False,
                    'error': f'Servidor SMTP: {configuracion_valores.get("EMAIL_HOST")}, esperado: smtp.gmail.com'
                }
                
            if configuracion_valores.get('EMAIL_PORT') != 587:
                return {
                    'valido': False,
                    'error': f'Puerto SMTP: {configuracion_valores.get("EMAIL_PORT")}, esperado: 587'
                }
            
            return {
                'valido': True,
                'mensaje': f'Configuración válida para {email_configurado}'
            }
            
        except Exception as e:
            return {
                'valido': False,
                'error': f'Error validando configuración: {str(e)}'
            }


# Instancia global del servicio
email_service = EmailService()