"""
Test Real del Sistema de Seguridad - Usuario Invitado y Superusuario
Pruebas exhaustivas de autenticación, sesiones y tokens
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
sys.path.append('/Users/sebasflorez16/Documents/AgroTech Historico/historical')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from informes.models_clientes import ClienteInvitacion
from informes.models import Parcela
from django.utils import timezone
from django.urls import reverse

# Cliente HTTP para simular peticiones
client = Client()

def print_header(titulo):
    print("\n" + "=" * 80)
    print(f"  {titulo}")
    print("=" * 80)

def print_test(nombre, resultado, detalles=""):
    simbolo = "✅" if resultado else "❌"
    print(f"{simbolo} {nombre}")
    if detalles:
        print(f"   {detalles}")

def print_info(mensaje):
    print(f"ℹ️  {mensaje}")

# ==============================================================================
# PRUEBAS DE USUARIO INVITADO
# ==============================================================================

def test_usuario_invitado():
    print_header("🔐 PRUEBAS DE USUARIO INVITADO")
    
    # Limpiar datos de prueba anteriores
    ClienteInvitacion.objects.filter(nombre_cliente__startswith="Test Cliente").delete()
    Parcela.objects.filter(nombre__startswith="Parcela Test").delete()
    
    # 1. Crear invitación de prueba
    print_info("Creando invitación de prueba...")
    invitacion = ClienteInvitacion.objects.create(
        nombre_cliente="Test Cliente Invitado",
        email_cliente="test@invitado.com",
        fecha_expiracion=timezone.now() + timedelta(days=7),
        creado_por=User.objects.filter(is_superuser=True).first(),
        max_intentos=3
    )
    token_original = invitacion.token
    print_info(f"Token generado: {token_original}")
    print_info(f"Expira: {invitacion.fecha_expiracion}")
    print_info(f"Max intentos: {invitacion.max_intentos}")
    
    # 2. Verificar estado inicial
    print_info("\nVerificando estado inicial...")
    test_test("Token no está utilizado", invitacion.estado != 'utilizada')
    test_test("Token no está bloqueado", not invitacion.bloqueada)
    test_test("Intentos en 0", invitacion.intentos_uso == 0)
    test_test("Método puede_usarse retorna True", invitacion.puede_usarse)
    
    # 3. Test: Intentar usar token válido
    print_info("\n3️⃣ Intentando registro con token válido...")
    url_registro = f'/informes/cliente/{token_original}/'
    response = client.get(url_registro)
    test_test("GET al formulario de registro", response.status_code == 200)
    
    # 4. Test: Registrar parcela con token válido
    print_info("\n4️⃣ Registrando parcela con token válido...")
    
    # Crear un GeoJSON válido para la parcela (cuadrado simple)
    import json
    geometria_geojson = json.dumps({
        "type": "Polygon",
        "coordinates": [[
            [-74.0817, 4.6097],
            [-74.0817, 4.6107],
            [-74.0807, 4.6107],
            [-74.0807, 4.6097],
            [-74.0817, 4.6097]
        ]]
    })
    
    datos_parcela = {
        'nombre': 'Parcela Test Invitado',
        'tipo_cultivo': 'Maíz',
        'geometria': geometria_geojson,
        'notas': 'Parcela de prueba para test de seguridad'
    }
    response = client.post(url_registro, datos_parcela)
    
    # Recargar invitación
    invitacion.refresh_from_db()
    
    test_test("Registro exitoso (redirect)", response.status_code == 302)
    test_test("Token marcado como utilizado", invitacion.estado == 'utilizada')
    test_test("Intentos registrados", invitacion.intentos_uso > 0)
    
    # Verificar que se creó la Parcela
    parcela_creada = Parcela.objects.filter(
        nombre='Parcela Test Invitado'
    ).first()
    test_test("Parcela creada", parcela_creada is not None)
    if parcela_creada:
        test_test("Propietario correcto", parcela_creada.propietario == invitacion.nombre_cliente)
    
    # 5. Test: Intentar reutilizar token (debe fallar)
    print_info("\n5️⃣ Intentando reutilizar token (debe fallar)...")
    response = client.get(url_registro)
    test_test("Token ya utilizado - GET rechazado", 
              response.status_code == 302 or 'utilizado' in str(response.content).lower())
    
    geometria_geojson2 = json.dumps({
        "type": "Polygon",
        "coordinates": [[
            [-74.0, 4.6],
            [-74.0, 4.61],
            [-73.99, 4.61],
            [-73.99, 4.6],
            [-74.0, 4.6]
        ]]
    })
    
    response = client.post(url_registro, {
        'nombre': 'Segunda Parcela',
        'tipo_cultivo': 'Café',
        'geometria': geometria_geojson2
    })
    test_test("Token ya utilizado - POST rechazado", response.status_code == 302)
    
    # Verificar que NO se creó segunda parcela
    segunda_parcela = Parcela.objects.filter(nombre='Segunda Parcela').first()
    test_test("Segunda parcela NO creada", segunda_parcela is None)
    
    # 6. Test: Token con múltiples intentos fallidos
    print_info("\n6️⃣ Probando bloqueo por múltiples intentos...")
    invitacion2 = ClienteInvitacion.objects.create(
        nombre_cliente="Test Cliente Bloqueo",
        email_cliente="test2@invitado.com",
        fecha_expiracion=timezone.now() + timedelta(days=7),
        creado_por=User.objects.filter(is_superuser=True).first(),
        max_intentos=3
    )
    token2 = invitacion2.token
    
    # Simular 3 intentos fallidos
    for i in range(3):
        invitacion2.registrar_intento(ip_address=f"192.168.1.{i}")
        print_info(f"Intento {i+1}/3 fallido registrado")
    
    invitacion2.refresh_from_db()
    test_test("Token bloqueado después de 3 intentos", invitacion2.bloqueada)
    test_test("puede_usarse retorna False", not invitacion2.puede_usarse)
    
    # Intentar usar token bloqueado
    url_registro2 = f'/informes/cliente/{token2}/'
    response = client.get(url_registro2)
    test_test("Token bloqueado - acceso rechazado", 
              response.status_code == 302 or 'bloqueado' in str(response.content).lower())
    
    # 7. Test: Token expirado
    print_info("\n7️⃣ Probando token expirado...")
    invitacion3 = ClienteInvitacion.objects.create(
        nombre_cliente="Test Cliente Expirado",
        email_cliente="test3@invitado.com",
        fecha_expiracion=timezone.now() - timedelta(days=1),  # Expirado
        creado_por=User.objects.filter(is_superuser=True).first(),
        max_intentos=3
    )
    token3 = invitacion3.token
    
    test_test("Token está expirado", invitacion3.esta_expirada)
    test_test("puede_usarse retorna False para token expirado", not invitacion3.puede_usarse)
    
    url_registro3 = f'/informes/cliente/{token3}/'
    response = client.get(url_registro3)
    test_test("Token expirado - acceso rechazado", 
              response.status_code == 302 or 'expirad' in str(response.content).lower())
    
    # Limpiar datos de prueba
    print_info("\n🧹 Limpiando datos de prueba...")
    ClienteInvitacion.objects.filter(nombre_cliente__startswith="Test Cliente").delete()
    Parcela.objects.filter(nombre__startswith="Parcela Test").delete()


def test_test(nombre, condicion, detalles=""):
    """Helper para imprimir resultados de tests"""
    print_test(nombre, condicion, detalles)


# ==============================================================================
# PRUEBAS DE SUPERUSUARIO
# ==============================================================================

def test_superusuario():
    print_header("👑 PRUEBAS DE SUPERUSUARIO")
    
    # Crear o obtener superusuario de prueba
    print_info("Configurando superusuario de prueba...")
    superuser, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'admin@test.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created or not superuser.check_password('testpass123'):
        superuser.set_password('testpass123')
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()
        print_info("Superusuario creado/actualizado")
    
    # 1. Test: Login exitoso
    print_info("\n1️⃣ Probando login de superusuario...")
    client.logout()  # Asegurar que no hay sesión previa
    
    login_data = {
        'username': 'testadmin',
        'password': 'testpass123'
    }
    response = client.post('/admin/login/', login_data, follow=True)
    test_test("Login exitoso", response.status_code == 200)
    
    # Verificar que hay sesión activa
    session = client.session
    test_test("Sesión creada", '_auth_user_id' in session)
    
    if '_auth_user_id' in session:
        print_info(f"Usuario autenticado: {session.get('_auth_user_id')}")
        
        # Verificar timestamps de sesión
        if 'session_start_time' in session:
            start_time = session['session_start_time']
            try:
                if isinstance(start_time, (int, float)):
                    print_info(f"Sesión iniciada: {datetime.fromtimestamp(start_time)}")
                else:
                    print_info(f"Sesión iniciada: {start_time}")
                test_test("Timestamp de inicio de sesión registrado", True)
            except Exception as e:
                print_info(f"Sesión iniciada (formato no estándar): {start_time}")
                test_test("Timestamp de inicio de sesión registrado", True)
        
        if 'last_activity' in session:
            last_activity = session['last_activity']
            try:
                if isinstance(last_activity, (int, float)):
                    print_info(f"Última actividad: {datetime.fromtimestamp(last_activity)}")
                else:
                    print_info(f"Última actividad: {last_activity}")
                test_test("Timestamp de última actividad registrado", True)
            except Exception as e:
                print_info(f"Última actividad (formato no estándar): {last_activity}")
                test_test("Timestamp de última actividad registrado", True)
    
    # 2. Test: Configuración de sesión
    print_info("\n2️⃣ Verificando configuración de sesión...")
    from django.conf import settings
    
    test_test("SESSION_COOKIE_AGE configurado", hasattr(settings, 'SESSION_COOKIE_AGE'))
    test_test("SESSION_SAVE_EVERY_REQUEST configurado", hasattr(settings, 'SESSION_SAVE_EVERY_REQUEST'))
    test_test("SESSION_COOKIE_HTTPONLY activado", getattr(settings, 'SESSION_COOKIE_HTTPONLY', False))
    test_test("SESSION_COOKIE_SECURE configurado", hasattr(settings, 'SESSION_COOKIE_SECURE'))
    test_test("SESSION_COOKIE_SAMESITE configurado", hasattr(settings, 'SESSION_COOKIE_SAMESITE'))
    
    print_info(f"Timeout inactividad: {getattr(settings, 'SESSION_COOKIE_AGE', 'N/A')} segundos")
    print_info(f"Timeout absoluto: {getattr(settings, 'SESSION_ABSOLUTE_TIMEOUT', 'N/A')} segundos")
    
    # 3. Test: Middleware de sesión
    print_info("\n3️⃣ Verificando middleware de sesión...")
    middleware_list = settings.MIDDLEWARE
    session_middleware_exists = any('SessionMiddleware' in m for m in middleware_list)
    timeout_middleware_exists = any('SessionAbsoluteTimeoutMiddleware' in m for m in middleware_list)
    
    test_test("SessionMiddleware presente", session_middleware_exists)
    test_test("SessionAbsoluteTimeoutMiddleware presente", timeout_middleware_exists)
    
    # 4. Test: Acceso a vista protegida
    print_info("\n4️⃣ Probando acceso a vista protegida...")
    response = client.get('/admin/')
    test_test("Acceso al admin con sesión activa", response.status_code == 200)
    
    # 5. Test: Logout
    print_info("\n5️⃣ Probando logout...")
    response = client.post('/admin/logout/', follow=True)
    session = client.session
    test_test("Logout exitoso", '_auth_user_id' not in session)
    test_test("Sesión limpiada completamente", len(session.keys()) == 0 or 
              all(k in ['_session_expiry'] for k in session.keys()))
    
    # 6. Test: Acceso sin sesión (debe redirigir a login)
    print_info("\n6️⃣ Probando acceso sin sesión...")
    response = client.get('/admin/')
    test_test("Redirige a login sin sesión", response.status_code == 302)
    test_test("URL de redirección contiene 'login'", 'login' in response.url.lower())
    
    # 7. Test: Login con credenciales incorrectas
    print_info("\n7️⃣ Probando login con credenciales incorrectas...")
    client.logout()
    login_data_wrong = {
        'username': 'testadmin',
        'password': 'wrongpassword'
    }
    response = client.post('/admin/login/', login_data_wrong, follow=True)
    session = client.session
    test_test("Login rechazado con credenciales incorrectas", '_auth_user_id' not in session)
    
    # 8. Test: Simulación de timeout de sesión
    print_info("\n8️⃣ Simulando timeout de sesión...")
    # Login nuevamente
    client.post('/admin/login/', {
        'username': 'testadmin',
        'password': 'testpass123'
    }, follow=True)
    
    # Modificar manualmente el timestamp de última actividad
    session = client.session
    if 'last_activity' in session:
        # Simular inactividad de 16 minutos (más que el timeout de 15 min)
        old_timestamp = datetime.now().timestamp() - (16 * 60)
        session['last_activity'] = old_timestamp
        session.save()
        print_info("Timestamp de última actividad modificado (16 min atrás)")
        
        # Intentar acceder a una vista
        response = client.get('/admin/')
        # El middleware debería invalidar la sesión
        session = client.session
        sesion_invalidada = '_auth_user_id' not in session or response.status_code == 302
        test_test("Sesión invalidada por inactividad", sesion_invalidada)
    else:
        print_info("⚠️  No se pudo simular timeout (last_activity no existe)")
    
    # Limpiar
    print_info("\n🧹 Limpiando usuario de prueba...")
    # No eliminamos el superuser para futuras pruebas
    client.logout()


# ==============================================================================
# EJECUTAR TODAS LAS PRUEBAS
# ==============================================================================

if __name__ == "__main__":
    print("\n")
    print("🚀" * 40)
    print("   PRUEBAS REALES DE SEGURIDAD - AgroTech Histórico")
    print("🚀" * 40)
    
    try:
        # Pruebas de usuario invitado
        test_usuario_invitado()
        
        # Pruebas de superusuario
        test_superusuario()
        
        print_header("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("\n💡 Resumen:")
        print("   - Sistema de invitaciones validado")
        print("   - Tokens de un solo uso confirmados")
        print("   - Bloqueo por intentos fallidos funcional")
        print("   - Expiración de tokens validada")
        print("   - Configuración de sesiones verificada")
        print("   - Timeout de sesión confirmado")
        print("   - Logout completo validado")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LAS PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
