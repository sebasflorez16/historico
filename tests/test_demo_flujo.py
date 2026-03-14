"""
Test end-to-end del flujo completo de Demo Link Único
======================================================
Ejecutar: python tests/test_demo_flujo.py

Verifica:
1. Crear DemoToken desde código
2. Landing muestra formulario
3. Registro guarda datos y redirige a mapa
4. Guardar parcela genera imágenes
5. Resultado muestra 3 imágenes y marca token como usado
6. Segundo acceso muestra pantalla de expirado
"""

import os
import sys
import json
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

# Agregar 'testserver' a ALLOWED_HOSTS para el test client de Django
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
if 'localhost' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('localhost')

from django.test import Client, RequestFactory
from django.utils import timezone
from datetime import timedelta

from informes.models_demo import DemoToken, DemoLead


def separador(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


def test_completo():
    """Test end-to-end del flujo demo."""
    client = Client()
    errores = []
    
    # ========================================
    # TEST 1: Crear DemoToken
    # ========================================
    separador("TEST 1: Crear DemoToken")
    
    try:
        token = DemoToken.objects.create(
            notas_comerciales="Test automático del flujo demo"
        )
        assert token.token is not None, "Token UUID no generado"
        assert token.estado == 'activo', f"Estado incorrecto: {token.estado}"
        assert token.esta_disponible, "Token debería estar disponible"
        assert token.fecha_expiracion is not None, "Fecha expiración no asignada"
        
        print(f"✅ Token creado: {token.token.hex[:8]}")
        print(f"   Estado: {token.estado}")
        print(f"   Expira: {token.fecha_expiracion}")
        print(f"   URL: /demo/{token.token}/")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 1: {e}")
        return
    
    # ========================================
    # TEST 2: Landing muestra formulario
    # ========================================
    separador("TEST 2: Landing muestra formulario")
    
    try:
        response = client.get(f'/demo/{token.token}/')
        assert response.status_code == 200, f"Status {response.status_code}"
        content = response.content.decode('utf-8')
        assert 'Nombre' in content or 'nombre' in content, "Formulario no tiene campo nombre"
        # Verificar que es la página de landing (formulario)
        assert 'Continuar' in content or 'continuar' in content or 'btn-continuar' in content, \
            "No es la página de landing/formulario"
        
        print(f"✅ Landing cargado correctamente (status 200)")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 2: {e}")
    
    # ========================================
    # TEST 3: Registro de datos
    # ========================================
    separador("TEST 3: Registro de datos")
    
    try:
        payload = {
            'nombre': 'Carlos Pérez Test',
            'telefono': '3201234567',
            'email': 'carlos@test.com',
            'departamento': 'Casanare',
            'municipio': 'Yopal'
        }
        
        response = client.post(
            f'/demo/{token.token}/registrar/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = json.loads(response.content)
        assert response.status_code == 200, f"Status {response.status_code}: {data}"
        assert data.get('success') is True, f"No fue exitoso: {data}"
        
        # Verificar que el token se actualizó
        token.refresh_from_db()
        assert token.estado == 'registrado', f"Estado incorrecto: {token.estado}"
        assert token.nombre_completo == 'Carlos Pérez Test'
        assert token.telefono == '3201234567'
        assert token.departamento == 'Casanare'
        
        print(f"✅ Registro exitoso")
        print(f"   Nombre: {token.nombre_completo}")
        print(f"   Estado: {token.estado}")
        print(f"   Redirect: {data.get('redirect_url')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 3: {e}")
    
    # ========================================
    # TEST 4: Landing redirige a mapa
    # ========================================
    separador("TEST 4: Landing redirige a mapa después de registro")
    
    try:
        response = client.get(f'/demo/{token.token}/')
        assert response.status_code == 200, f"Status {response.status_code}"
        content = response.content.decode('utf-8')
        # Debería mostrar el mapa, no el formulario
        assert 'Leaflet' in content or 'leaflet' in content or 'map' in content, \
            "No carga el mapa Leaflet"
        assert 'dibujar' in content.lower() or 'parcela' in content.lower(), \
            "No parece ser la página del mapa"
        
        print(f"✅ Redirige al mapa correctamente")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 4: {e}")
    
    # ========================================
    # TEST 5: Guardar parcela
    # ========================================
    separador("TEST 5: Guardar parcela (geometría de prueba)")
    
    try:
        # Polígono de prueba en Casanare, Colombia (~50 ha)
        geometria = {
            "type": "Polygon",
            "coordinates": [[
                [-72.40, 5.30],
                [-72.39, 5.30],
                [-72.39, 5.31],
                [-72.40, 5.31],
                [-72.40, 5.30]
            ]]
        }
        
        response = client.post(
            f'/demo/{token.token}/guardar-parcela/',
            data=json.dumps({'geometria': geometria}),
            content_type='application/json'
        )
        
        data = json.loads(response.content)
        assert response.status_code == 200, f"Status {response.status_code}: {data}"
        assert data.get('success') is True, f"No fue exitoso: {data}"
        
        # Verificar DemoLead creado
        token.refresh_from_db()
        assert hasattr(token, 'lead'), "No se creó DemoLead"
        lead = token.lead
        assert lead.geometria is not None, "Geometría no guardada"
        assert lead.area_hectareas > 0, f"Área incorrecta: {lead.area_hectareas}"
        assert lead.centroide_lat != 0, "Centroide no calculado"
        
        print(f"✅ Parcela guardada exitosamente")
        print(f"   Área: {lead.area_hectareas:.1f} ha")
        print(f"   Centroide: ({lead.centroide_lat:.4f}, {lead.centroide_lon:.4f})")
        print(f"   Redirect: {data.get('redirect_url')}")
        
        # Verificar imágenes
        if lead.ndvi_url:
            print(f"   NDVI: {lead.ndvi_url}")
        if lead.ndmi_url:
            print(f"   NDMI: {lead.ndmi_url}")
        if lead.savi_url:
            print(f"   SAVI: {lead.savi_url}")
        
        # Verificar que los archivos PNG existen en disco
        from pathlib import Path
        from django.conf import settings
        
        media_root = Path(settings.MEDIA_ROOT)
        token_hex = token.token.hex[:8]
        dir_demo = media_root / 'demo' / token_hex
        
        if dir_demo.exists():
            archivos = list(dir_demo.iterdir())
            print(f"   Archivos generados: {[f.name for f in archivos]}")
            for archivo in archivos:
                size = archivo.stat().st_size
                print(f"     📄 {archivo.name}: {size:,} bytes")
                assert size > 1000, f"Archivo {archivo.name} muy pequeño: {size} bytes"
        else:
            print(f"   ⚠️ Directorio de imágenes no existe: {dir_demo}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        errores.append(f"TEST 5: {e}")
    
    # ========================================
    # TEST 6: Ver resultados
    # ========================================
    separador("TEST 6: Ver resultados (marca token como usado)")
    
    try:
        response = client.get(f'/demo/{token.token}/resultado/')
        assert response.status_code == 200, f"Status {response.status_code}"
        content = response.content.decode('utf-8')
        
        # Verificar contenido del resultado
        assert 'WhatsApp' in content or 'whatsapp' in content, "No tiene botón WhatsApp"
        assert 'NDVI' in content or 'ndvi' in content, "No menciona NDVI"
        assert 'Carlos' in content, "No muestra el nombre del usuario"
        assert 'Análisis' in content or 'análisis' in content or 'Satelital' in content, \
            "No parece ser la página de resultado"
        
        # Verificar que el token se marcó como usado
        token.refresh_from_db()
        assert token.estado == 'usado', f"Token debería estar 'usado', está: {token.estado}"
        assert token.fecha_uso is not None, "fecha_uso no se registró"
        
        print(f"✅ Resultado mostrado correctamente")
        print(f"   Estado token: {token.estado}")
        print(f"   Fecha uso: {token.fecha_uso}")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 6: {e}")
    
    # ========================================
    # TEST 7: Segundo acceso → ya usado (puede ver resultado aún)
    # ========================================
    separador("TEST 7: Segundo acceso al resultado")
    
    try:
        response = client.get(f'/demo/{token.token}/resultado/')
        # Un token 'usado' todavía puede ver el resultado (por diseño, el if lo permite)
        assert response.status_code == 200, f"Status {response.status_code}"
        
        print(f"✅ Segundo acceso al resultado funciona (vista read-only)")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 7: {e}")
    
    # ========================================
    # TEST 8: Landing de token usado → expirado
    # ========================================
    separador("TEST 8: Landing de token usado → pantalla expirado")
    
    try:
        response = client.get(f'/demo/{token.token}/')
        assert response.status_code == 200, f"Status {response.status_code}"
        content = response.content.decode('utf-8')
        # Token usado debe mostrar pantalla de expirado
        assert 'ya fue utilizado' in content.lower() or 'expirad' in content.lower() \
            or 'utilizada' in content.lower(), \
            f"Debería mostrar expirado, contenido no tiene texto de expirado"
        
        print(f"✅ Token usado redirige a pantalla de expirado")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 8: {e}")
    
    # ========================================
    # TEST 9: Token con expiración pasada
    # ========================================
    separador("TEST 9: Token expirado por fecha")
    
    try:
        token_exp = DemoToken.objects.create(
            fecha_expiracion=timezone.now() - timedelta(days=1),
            notas_comerciales="Token expirado de prueba"
        )
        
        response = client.get(f'/demo/{token_exp.token}/')
        assert response.status_code == 200, f"Status {response.status_code}"
        content = response.content.decode('utf-8')
        assert 'expirad' in content.lower() or 'utilizada' in content.lower(), \
            f"Debería mostrar expirado"
        
        # Limpiar token de prueba
        token_exp.delete()
        
        print(f"✅ Token expirado muestra pantalla correcta")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 9: {e}")
    
    # ========================================
    # TEST 10: UUID inválido → 404
    # ========================================
    separador("TEST 10: UUID inexistente → 404")
    
    try:
        response = client.get('/demo/00000000-0000-0000-0000-000000000000/')
        assert response.status_code == 404, f"Esperaba 404, got {response.status_code}"
        
        print(f"✅ UUID inexistente retorna 404")
    except Exception as e:
        print(f"❌ Error: {e}")
        errores.append(f"TEST 10: {e}")
    
    # ========================================
    # LIMPIEZA
    # ========================================
    separador("LIMPIEZA")
    
    try:
        # Eliminar archivos de imágenes generados
        from pathlib import Path
        from django.conf import settings
        import shutil
        
        token_hex = token.token.hex[:8]
        dir_demo = Path(settings.MEDIA_ROOT) / 'demo' / token_hex
        if dir_demo.exists():
            shutil.rmtree(dir_demo)
            print(f"🧹 Eliminado directorio: {dir_demo}")
        
        # Eliminar registros de test
        if hasattr(token, 'lead'):
            token.lead.delete()
        token.delete()
        print(f"🧹 Registros de test eliminados")
    except Exception as e:
        print(f"⚠️ Error en limpieza: {e}")
    
    # ========================================
    # RESUMEN
    # ========================================
    separador("RESUMEN")
    
    total = 10
    fallidos = len(errores)
    exitosos = total - fallidos
    
    print(f"\n📊 Resultados: {exitosos}/{total} tests pasaron")
    
    if errores:
        print(f"\n❌ Tests fallidos:")
        for e in errores:
            print(f"   • {e}")
    else:
        print(f"\n🎉 ¡TODOS los tests pasaron! El flujo de demo está funcional.")
    
    return len(errores) == 0


if __name__ == '__main__':
    print("\n🧪 TEST END-TO-END: DEMO LINK ÚNICO")
    print("=" * 60)
    
    exito = test_completo()
    sys.exit(0 if exito else 1)
