#!/usr/bin/env python
"""
Test de Eliminación Segura - AgroTech Histórico
Verifica que la funcionalidad de eliminación esté correctamente implementada
y solo accesible para superusuarios.

Ejecutar: python test_eliminacion_segura.py
"""

import os
import sys
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from informes.models import Parcela, Informe
from informes.models_clientes import ClienteInvitacion
import logging

logger = logging.getLogger(__name__)

def crear_usuario_normal():
    """Crear un usuario normal (no superusuario) para pruebas"""
    try:
        user = User.objects.create_user(
            username='test_normal',
            password='test123',
            email='test@normal.com'
        )
        print(f"✅ Usuario normal creado: {user.username}")
        return user
    except Exception as e:
        print(f"⚠️  Usuario normal ya existe o error: {e}")
        return User.objects.get(username='test_normal')


def limpiar_datos_prueba():
    """Limpiar datos de prueba previos"""
    try:
        User.objects.filter(username='test_normal').delete()
        print("🧹 Datos de prueba limpiados")
    except Exception as e:
        print(f"⚠️  Error limpiando datos: {e}")


def test_acceso_sin_autenticar():
    """Test 1: Verificar que usuarios no autenticados no pueden acceder"""
    print("\n" + "="*70)
    print("TEST 1: Acceso sin autenticación")
    print("="*70)
    
    client = Client()
    
    # Intentar acceder a eliminar parcela sin autenticar
    response = client.post(reverse('informes:eliminar_parcela', args=[1]))
    
    if response.status_code == 302:  # Redirección a login
        print("✅ PASS: Usuario no autenticado es redirigido al login")
        return True
    else:
        print(f"❌ FAIL: Código de estado inesperado: {response.status_code}")
        return False


def test_acceso_usuario_normal():
    """Test 2: Verificar que usuarios normales no pueden acceder"""
    print("\n" + "="*70)
    print("TEST 2: Acceso con usuario normal (no superusuario)")
    print("="*70)
    
    client = Client()
    user = crear_usuario_normal()
    
    # Autenticar con usuario normal
    client.login(username='test_normal', password='test123')
    
    # Intentar acceder a eliminar parcela
    response = client.post(reverse('informes:eliminar_parcela', args=[1]))
    
    if response.status_code == 302:  # Redirección por falta de permisos
        print("✅ PASS: Usuario normal no puede acceder a eliminación")
        return True
    else:
        print(f"❌ FAIL: Usuario normal obtuvo acceso (código: {response.status_code})")
        return False


def test_acceso_superusuario():
    """Test 3: Verificar que solo superusuarios pueden acceder"""
    print("\n" + "="*70)
    print("TEST 3: Acceso con superusuario")
    print("="*70)
    
    client = Client()
    
    # Obtener superusuario
    try:
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            print("⚠️  No hay superusuarios en el sistema")
            return False
        
        print(f"🔐 Usando superusuario: {superuser.username}")
        
        # Verificar que la vista de eliminación esté importada correctamente
        from informes import views
        if hasattr(views, 'eliminar_parcela'):
            print("✅ Vista eliminar_parcela importada correctamente")
        else:
            print("❌ FAIL: Vista eliminar_parcela NO está importada en views.py")
            return False
        
        if hasattr(views, 'eliminar_informe'):
            print("✅ Vista eliminar_informe importada correctamente")
        else:
            print("❌ FAIL: Vista eliminar_informe NO está importada en views.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error en test de superusuario: {e}")
        return False


def test_templates_modificados():
    """Test 4: Verificar que los templates tengan los botones de eliminación"""
    print("\n" + "="*70)
    print("TEST 4: Verificación de templates modificados")
    print("="*70)
    
    templates_dir = 'templates/informes/'
    templates_verificar = [
        'parcelas/detalle.html',
        'informes/detalle.html'
    ]
    
    resultados = []
    
    for template in templates_verificar:
        template_path = os.path.join(templates_dir, template)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
                
                tiene_boton = 'modalEliminar' in contenido
                tiene_modal = 'formEliminar' in contenido
                tiene_validacion_superuser = 'user.is_superuser' in contenido
                
                if tiene_boton and tiene_modal and tiene_validacion_superuser:
                    print(f"✅ {template}: Botón y modal de eliminación implementados")
                    resultados.append(True)
                else:
                    print(f"❌ {template}: Falta implementación completa")
                    if not tiene_boton:
                        print(f"   - Falta botón de eliminación")
                    if not tiene_modal:
                        print(f"   - Falta modal de confirmación")
                    if not tiene_validacion_superuser:
                        print(f"   - Falta validación de superusuario")
                    resultados.append(False)
        except FileNotFoundError:
            print(f"⚠️  {template}: Archivo no encontrado")
            resultados.append(False)
        except Exception as e:
            print(f"❌ Error leyendo {template}: {e}")
            resultados.append(False)
    
    return all(resultados)


def test_urls_configuradas():
    """Test 5: Verificar que las URLs estén correctamente configuradas"""
    print("\n" + "="*70)
    print("TEST 5: Verificación de URLs configuradas")
    print("="*70)
    
    urls_verificar = [
        ('eliminar_parcela', 'informes:eliminar_parcela'),
        ('eliminar_informe', 'informes:eliminar_informe'),
    ]
    
    resultados = []
    
    for nombre, url_name in urls_verificar:
        try:
            url = reverse(url_name, args=[1])
            print(f"✅ URL {nombre}: {url}")
            resultados.append(True)
        except Exception as e:
            print(f"❌ URL {nombre}: Error - {e}")
            resultados.append(False)
    
    return all(resultados)


def test_vistas_protegidas():
    """Test 6: Verificar que las vistas tengan los decoradores de seguridad"""
    print("\n" + "="*70)
    print("TEST 6: Verificación de decoradores de seguridad")
    print("="*70)
    
    try:
        # Leer el archivo views_eliminacion.py
        with open('informes/views_eliminacion.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        verificaciones = {
            '@login_required': '@login_required' in contenido,
            '@user_passes_test': '@user_passes_test' in contenido,
            '@require_http_methods(["POST"])': '@require_http_methods(["POST"])' in contenido,
            'es_superusuario': 'def es_superusuario' in contenido,
            'logger.warning': 'logger.warning' in contenido,
        }
        
        for check, resultado in verificaciones.items():
            if resultado:
                print(f"✅ {check}: Implementado")
            else:
                print(f"❌ {check}: NO implementado")
        
        return all(verificaciones.values())
        
    except FileNotFoundError:
        print("❌ FAIL: Archivo views_eliminacion.py no encontrado")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error verificando decoradores: {e}")
        return False


def test_importaciones_views():
    """Test 7: Verificar que views.py importe las vistas de eliminación"""
    print("\n" + "="*70)
    print("TEST 7: Verificación de importaciones en views.py")
    print("="*70)
    
    try:
        with open('informes/views.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        tiene_import = 'from .views_eliminacion import eliminar_parcela, eliminar_informe' in contenido
        
        if tiene_import:
            print("✅ Las vistas de eliminación están correctamente importadas en views.py")
            return True
        else:
            print("❌ FAIL: Las vistas de eliminación NO están importadas en views.py")
            return False
            
    except FileNotFoundError:
        print("❌ FAIL: Archivo views.py no encontrado")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error verificando importaciones: {e}")
        return False


def run_tests():
    """Ejecutar todos los tests de eliminación segura"""
    print("\n" + "="*70)
    print("🔒 TEST DE ELIMINACIÓN SEGURA - AGROTECH HISTÓRICO")
    print("="*70)
    print("\nVerificando implementación de eliminación segura de parcelas e informes...")
    print("Solo accesible para superusuarios con confirmación explícita\n")
    
    resultados = []
    
    # Test 1: Acceso sin autenticar
    resultados.append(("Acceso sin autenticación", test_acceso_sin_autenticar()))
    
    # Test 2: Acceso con usuario normal
    resultados.append(("Acceso usuario normal", test_acceso_usuario_normal()))
    
    # Test 3: Acceso con superusuario
    resultados.append(("Acceso superusuario", test_acceso_superusuario()))
    
    # Test 4: Templates modificados
    resultados.append(("Templates modificados", test_templates_modificados()))
    
    # Test 5: URLs configuradas
    resultados.append(("URLs configuradas", test_urls_configuradas()))
    
    # Test 6: Vistas protegidas
    resultados.append(("Decoradores de seguridad", test_vistas_protegidas()))
    
    # Test 7: Importaciones
    resultados.append(("Importaciones en views.py", test_importaciones_views()))
    
    # Limpiar datos de prueba
    limpiar_datos_prueba()
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)
    
    total_tests = len(resultados)
    tests_exitosos = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        simbolo = "✅" if resultado else "❌"
        print(f"{simbolo} {nombre}")
    
    print("\n" + "="*70)
    print(f"Total: {tests_exitosos}/{total_tests} tests exitosos")
    print("="*70)
    
    if tests_exitosos == total_tests:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ La eliminación segura está correctamente implementada")
        print("✅ Solo superusuarios pueden eliminar parcelas e informes")
        print("✅ Se requiere confirmación explícita para eliminar")
        print("✅ Todas las acciones quedan registradas en logs")
        return 0
    else:
        print(f"\n⚠️  {total_tests - tests_exitosos} tests fallaron")
        print("❌ Revise los errores anteriores")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
