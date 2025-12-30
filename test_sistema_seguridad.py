#!/usr/bin/env python
"""
Script de prueba para verificar el sistema de seguridad de AgroTech Histórico
Verifica configuración de sesiones, middleware, y modelos de invitación
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from informes.models_clientes import ClienteInvitacion
from django.utils import timezone


def print_header(text):
    """Imprimir encabezado formateado"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_result(test_name, passed, details=""):
    """Imprimir resultado de prueba"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"      {details}")


def test_session_configuration():
    """Verificar configuración de sesiones"""
    print_header("🔐 VERIFICACIÓN DE CONFIGURACIÓN DE SESIONES")
    
    tests = [
        ("SESSION_COOKIE_AGE", settings.SESSION_COOKIE_AGE == 900, 
         f"Configurado: {settings.SESSION_COOKIE_AGE}s (15 min)"),
        
        ("SESSION_SAVE_EVERY_REQUEST", settings.SESSION_SAVE_EVERY_REQUEST, 
         "Sesión se renueva en cada request"),
        
        ("SESSION_EXPIRE_AT_BROWSER_CLOSE", settings.SESSION_EXPIRE_AT_BROWSER_CLOSE, 
         "Sesión expira al cerrar navegador"),
        
        ("SESSION_COOKIE_HTTPONLY", settings.SESSION_COOKIE_HTTPONLY, 
         "Protección contra XSS habilitada"),
        
        ("SESSION_ABSOLUTE_TIMEOUT", hasattr(settings, 'SESSION_ABSOLUTE_TIMEOUT'), 
         f"Timeout absoluto: {getattr(settings, 'SESSION_ABSOLUTE_TIMEOUT', 'N/A')}s (2h)"),
        
        ("SESSION_ENGINE", settings.SESSION_ENGINE == 'django.contrib.sessions.backends.db', 
         f"Motor: {settings.SESSION_ENGINE}"),
        
        ("CSRF_COOKIE_HTTPONLY", settings.CSRF_COOKIE_HTTPONLY, 
         "Protección CSRF habilitada"),
    ]
    
    for test_name, passed, details in tests:
        print_result(test_name, passed, details)
    
    return all(t[1] for t in tests)


def test_middleware_configuration():
    """Verificar middleware de seguridad"""
    print_header("🛡️ VERIFICACIÓN DE MIDDLEWARE")
    
    middleware_list = settings.MIDDLEWARE
    
    tests = [
        ("SecurityMiddleware", "django.middleware.security.SecurityMiddleware" in middleware_list,
         "Middleware de seguridad de Django"),
        
        ("SessionMiddleware", "django.contrib.sessions.middleware.SessionMiddleware" in middleware_list,
         "Middleware de sesiones"),
        
        ("AuthenticationMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware" in middleware_list,
         "Middleware de autenticación"),
        
        ("SessionAbsoluteTimeoutMiddleware", "informes.middleware.SessionAbsoluteTimeoutMiddleware" in middleware_list,
         "Middleware personalizado de timeout absoluto"),
    ]
    
    for test_name, passed, details in tests:
        print_result(test_name, passed, details)
    
    return all(t[1] for t in tests)


def test_invitation_model():
    """Verificar modelo de invitaciones"""
    print_header("📧 VERIFICACIÓN DE MODELO DE INVITACIONES")
    
    try:
        # Verificar que el modelo tiene los campos de seguridad
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='informes_clienteinvitacion'
            """)
            columns = [row[0] for row in cursor.fetchall()]
        
        tests = [
            ("Campo 'intentos_uso'", 'intentos_uso' in columns,
             "Control de intentos de uso"),
            
            ("Campo 'max_intentos'", 'max_intentos' in columns,
             "Límite máximo de intentos"),
            
            ("Campo 'bloqueada'", 'bloqueada' in columns,
             "Flag de bloqueo de seguridad"),
            
            ("Campo 'ip_ultimo_intento'", 'ip_ultimo_intento' in columns,
             "Auditoría de IP"),
            
            ("Campo 'parcela_id'", 'parcela_id' in columns,
             "Relación única con parcela"),
        ]
        
        for test_name, passed, details in tests:
            print_result(test_name, passed, details)
        
        # Verificar métodos del modelo
        dummy_user = User.objects.filter(is_superuser=True).first()
        if dummy_user:
            invitacion = ClienteInvitacion(
                token='test_security_token',
                nombre_cliente='Test Cliente',
                email_cliente='test@test.com',
                fecha_expiracion=timezone.now() + timedelta(days=7),
                creado_por=dummy_user,
                costo_servicio=0
            )
            
            method_tests = [
                ("Método 'puede_usarse'", hasattr(invitacion, 'puede_usarse'),
                 "Validación de uso disponible"),
                
                ("Método 'registrar_intento'", hasattr(invitacion, 'registrar_intento'),
                 "Registro de intentos de uso"),
                
                ("Método 'marcar_como_utilizada'", hasattr(invitacion, 'marcar_como_utilizada'),
                 "Invalidación de token"),
                
                ("Propiedad 'esta_expirada'", hasattr(invitacion, 'esta_expirada'),
                 "Verificación de expiración"),
            ]
            
            for test_name, passed, details in method_tests:
                print_result(test_name, passed, details)
        
        return True
        
    except Exception as e:
        print_result("Modelo ClienteInvitacion", False, f"Error: {str(e)}")
        return False


def test_invitation_security_logic():
    """Verificar lógica de seguridad de invitaciones"""
    print_header("🔒 VERIFICACIÓN DE LÓGICA DE SEGURIDAD")
    
    try:
        # Buscar un superusuario
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            print_result("Superusuario requerido", False, "Crear un superusuario primero")
            return False
        
        # 1. Crear invitación de prueba
        test_token = f'security_test_{timezone.now().timestamp()}'
        invitacion = ClienteInvitacion.objects.create(
            token=test_token,
            nombre_cliente='Cliente de Prueba de Seguridad',
            email_cliente='security_test@agrotech.com',
            fecha_expiracion=timezone.now() + timedelta(days=7),
            creado_por=superuser,
            costo_servicio=0
        )
        
        print(f"\n📝 Invitación de prueba creada: {test_token}")
        
        # Test 1: Invitación nueva debe poder usarse
        test1 = invitacion.puede_usarse
        print_result("Invitación nueva puede usarse", test1, 
                    f"Estado: {invitacion.estado}, Intentos: {invitacion.intentos_uso}")
        
        # Test 2: Registrar intentos
        invitacion.registrar_intento('192.168.1.100')
        invitacion.refresh_from_db()
        test2 = invitacion.intentos_uso == 1 and invitacion.ip_ultimo_intento == '192.168.1.100'
        print_result("Registrar intento funciona", test2,
                    f"Intentos: {invitacion.intentos_uso}, IP: {invitacion.ip_ultimo_intento}")
        
        # Test 3: Aún puede usarse después de 1 intento
        test3 = invitacion.puede_usarse
        print_result("Puede usarse después de 1 intento", test3,
                    f"Intentos restantes: {invitacion.max_intentos - invitacion.intentos_uso}")
        
        # Test 4: Registrar más intentos hasta el límite
        invitacion.registrar_intento('192.168.1.101')
        invitacion.registrar_intento('192.168.1.102')
        invitacion.refresh_from_db()
        test4 = invitacion.intentos_uso == 3 and invitacion.bloqueada
        print_result("Bloqueo automático tras 3 intentos", test4,
                    f"Intentos: {invitacion.intentos_uso}, Bloqueada: {invitacion.bloqueada}")
        
        # Test 5: No puede usarse después del bloqueo
        test5 = not invitacion.puede_usarse
        print_result("No puede usarse después de bloqueo", test5,
                    f"Estado: {invitacion.estado}, Bloqueada: {invitacion.bloqueada}")
        
        # Test 6: Crear nueva invitación para probar marcado como utilizada
        invitacion2 = ClienteInvitacion.objects.create(
            token=f'security_test2_{timezone.now().timestamp()}',
            nombre_cliente='Cliente de Prueba 2',
            email_cliente='security_test2@agrotech.com',
            fecha_expiracion=timezone.now() + timedelta(days=7),
            creado_por=superuser,
            costo_servicio=0
        )
        
        invitacion2.marcar_como_utilizada()
        invitacion2.refresh_from_db()
        test6 = (invitacion2.estado == 'utilizada' and 
                invitacion2.bloqueada and 
                not invitacion2.puede_usarse)
        print_result("Invalidación de token funciona", test6,
                    f"Estado: {invitacion2.estado}, Bloqueada: {invitacion2.bloqueada}")
        
        # Test 7: Invitación expirada
        invitacion3 = ClienteInvitacion.objects.create(
            token=f'security_test3_{timezone.now().timestamp()}',
            nombre_cliente='Cliente de Prueba 3',
            email_cliente='security_test3@agrotech.com',
            fecha_expiracion=timezone.now() - timedelta(days=1),  # Expirada
            creado_por=superuser,
            costo_servicio=0
        )
        
        test7 = invitacion3.esta_expirada and not invitacion3.puede_usarse
        print_result("Detección de expiración funciona", test7,
                    f"Expirada: {invitacion3.esta_expirada}, Puede usarse: {invitacion3.puede_usarse}")
        
        # Limpieza
        print(f"\n🧹 Limpiando invitaciones de prueba...")
        invitacion.delete()
        invitacion2.delete()
        invitacion3.delete()
        print("✅ Limpieza completada")
        
        return all([test1, test2, test3, test4, test5, test6, test7])
        
    except Exception as e:
        print_result("Lógica de seguridad", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "🔐"*35)
    print("  VERIFICACIÓN DE SISTEMA DE SEGURIDAD - AGROTECH HISTÓRICO")
    print("🔐"*35)
    print(f"\n📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Entorno: {'DESARROLLO' if settings.DEBUG else 'PRODUCCIÓN'}")
    
    results = []
    
    # Ejecutar pruebas
    results.append(("Configuración de Sesiones", test_session_configuration()))
    results.append(("Middleware de Seguridad", test_middleware_configuration()))
    results.append(("Modelo de Invitaciones", test_invitation_model()))
    results.append(("Lógica de Seguridad", test_invitation_security_logic()))
    
    # Resumen
    print_header("📊 RESUMEN DE VERIFICACIÓN")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  Total: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("  🎉 ¡Todas las verificaciones pasaron exitosamente!")
        print("  🔒 El sistema de seguridad está correctamente configurado")
    else:
        print("  ⚠️  Algunas verificaciones fallaron")
        print("  🔧 Revisa la configuración y los errores reportados")
    
    print(f"{'='*70}\n")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
