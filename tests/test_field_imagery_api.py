"""
Test completo de Field Imagery API de EOSDA
Verifica descarga de imágenes satelitales NDVI, NDMI, SAVI
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.services.eosda_api import EosdaAPIService
from informes.models import Parcela, IndiceMensual
from datetime import datetime

def test_field_imagery_api():
    """
    Test completo de descarga de imágenes satelitales
    """
    print("=" * 80)
    print("🧪 TEST FIELD IMAGERY API - DESCARGA DE IMÁGENES SATELITALES")
    print("=" * 80)
    
    # 1. Seleccionar parcela de prueba
    parcela = Parcela.objects.filter(
        eosda_sincronizada=True,
        eosda_field_id__isnull=False
    ).first()
    
    if not parcela:
        print("❌ ERROR: No hay parcelas sincronizadas con EOSDA")
        return
    
    print(f"\n📍 Parcela seleccionada: {parcela.nombre}")
    print(f"   EOSDA Field ID: {parcela.eosda_field_id}")
    
    # 2. Seleccionar registro mensual reciente
    registro = IndiceMensual.objects.filter(
        parcela=parcela,
        fuente_datos='EOSDA'
    ).order_by('-año', '-mes').first()
    
    if not registro:
        print("❌ ERROR: No hay registros mensuales para esta parcela")
        return
    
    print(f"\n📅 Registro seleccionado: {registro.año}-{registro.mes:02d}")
    print(f"   NDVI: {registro.ndvi_promedio:.3f}")
    print(f"   Nubosidad: {registro.nubosidad_promedio:.1f}%")
    
    # 3. Verificar estado actual de imágenes
    print("\n📊 Estado actual de imágenes:")
    print(f"   NDVI: {'✅ Descargada' if registro.imagen_ndvi else '📥 Pendiente'}")
    print(f"   NDMI: {'✅ Descargada' if registro.imagen_ndmi else '📥 Pendiente'}")
    print(f"   SAVI: {'✅ Descargada' if registro.imagen_savi else '📥 Pendiente'}")
    
    # 4. Test descarga de imagen NDVI
    print("\n" + "=" * 80)
    print("📷 TEST 1: Descargar imagen NDVI")
    print("=" * 80)
    
    eosda_service = EosdaAPIService()
    
    # Test con diferentes límites de nubosidad
    for max_nubosidad in [30.0, 50.0]:
        print(f"\n🔍 Intentando descarga con nubosidad máxima: {max_nubosidad}%")
        
        resultado = eosda_service.descargar_imagen_satelital(
            field_id=parcela.eosda_field_id,
            indice='NDVI',
            max_nubosidad=max_nubosidad
        )
        
        if resultado:
            print(f"✅ ÉXITO - Imagen NDVI descargada")
            print(f"   📅 Fecha imagen: {resultado.get('fecha')}")
            print(f"   ☁️  Nubosidad: {resultado.get('nubosidad')}%")
            print(f"   🆔 View ID: {resultado.get('view_id')}")
            print(f"   📦 Tamaño: {len(resultado.get('imagen', b''))} bytes")
            print(f"   🖼️  Tipo: {resultado.get('content_type')}")
            
            # Guardar imagen de prueba
            test_filename = f"test_ndvi_{parcela.eosda_field_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            test_path = os.path.join('/tmp', test_filename)
            
            with open(test_path, 'wb') as f:
                f.write(resultado['imagen'])
            
            print(f"   💾 Imagen guardada en: {test_path}")
            print(f"   ℹ️  Puedes verificar la imagen manualmente")
            
            break  # Salir después del primer éxito
        else:
            print(f"⚠️  No se encontró imagen con nubosidad ≤{max_nubosidad}%")
    
    # 5. Test descarga de imagen NDMI
    print("\n" + "=" * 80)
    print("📷 TEST 2: Descargar imagen NDMI")
    print("=" * 80)
    
    resultado_ndmi = eosda_service.descargar_imagen_satelital(
        field_id=parcela.eosda_field_id,
        indice='NDMI',
        max_nubosidad=50.0
    )
    
    if resultado_ndmi:
        print(f"✅ ÉXITO - Imagen NDMI descargada")
        print(f"   📅 Fecha: {resultado_ndmi.get('fecha')}")
        print(f"   ☁️  Nubosidad: {resultado_ndmi.get('nubosidad')}%")
        print(f"   📦 Tamaño: {len(resultado_ndmi.get('imagen', b''))} bytes")
    else:
        print("⚠️  No se pudo descargar imagen NDMI")
    
    # 6. Test descarga de imagen SAVI
    print("\n" + "=" * 80)
    print("📷 TEST 3: Descargar imagen SAVI")
    print("=" * 80)
    
    resultado_savi = eosda_service.descargar_imagen_satelital(
        field_id=parcela.eosda_field_id,
        indice='SAVI',
        max_nubosidad=50.0
    )
    
    if resultado_savi:
        print(f"✅ ÉXITO - Imagen SAVI descargada")
        print(f"   📅 Fecha: {resultado_savi.get('fecha')}")
        print(f"   ☁️  Nubosidad: {resultado_savi.get('nubosidad')}%")
        print(f"   📦 Tamaño: {len(resultado_savi.get('imagen', b''))} bytes")
    else:
        print("⚠️  No se pudo descargar imagen SAVI")
    
    # 7. Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DEL TEST")
    print("=" * 80)
    
    resultados_exitosos = sum([
        1 if resultado else 0,
        1 if resultado_ndmi else 0,
        1 if resultado_savi else 0
    ])
    
    print(f"\n✅ Imágenes descargadas exitosamente: {resultados_exitosos}/3")
    print(f"⚠️  Imágenes fallidas: {3 - resultados_exitosos}/3")
    
    if resultados_exitosos > 0:
        print("\n🎉 Field Imagery API funcionando correctamente")
        print("   Las imágenes se pueden descargar desde la interfaz web")
        print("   usando el dropdown y botón en cada fila de datos")
    else:
        print("\n❌ No se pudieron descargar imágenes")
        print("   Posibles causas:")
        print("   - No hay escenas con nubosidad baja en los últimos 60 días")
        print("   - Problema con la API de EOSDA")
        print("   - API Key no tiene permisos para Field Imagery")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_field_imagery_api()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
