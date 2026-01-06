"""
Script para verificar que el sistema de imágenes usa caché correctamente
SIN consumir requests de EOSDA
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.models_configuracion import CacheDatosEOSDA
import json

def verificar_cache_disponible():
    """
    Verifica que hay caché de Statistics API disponible
    """
    print("=" * 80)
    print("🔍 VERIFICACIÓN DE CACHÉ PARA IMÁGENES SATELITALES")
    print("=" * 80)
    
    # 1. Buscar parcelas con datos
    parcelas = Parcela.objects.filter(
        eosda_sincronizada=True,
        eosda_field_id__isnull=False
    )
    
    print(f"\n📊 Parcelas sincronizadas: {parcelas.count()}")
    
    for parcela in parcelas:
        print(f"\n📍 Parcela: {parcela.nombre}")
        print(f"   EOSDA Field ID: {parcela.eosda_field_id}")
        
        # 2. Verificar registros mensuales
        registros = IndiceMensual.objects.filter(
            parcela=parcela,
            fuente_datos='EOSDA'
        ).order_by('-año', '-mes')[:3]
        
        print(f"   📅 Registros mensuales: {registros.count()}")
        
        for registro in registros:
            print(f"\n   🗓️  {registro.año}-{registro.mes:02d}:")
            print(f"      NDVI: {registro.ndvi_promedio:.3f}" if registro.ndvi_promedio else "      NDVI: N/A")
            
            # 3. Verificar caché de Statistics
            cache_valido = CacheDatosEOSDA.objects.filter(
                field_id=parcela.eosda_field_id
            ).order_by('-creado_en').first()
            
            if cache_valido and cache_valido.datos_json:
                # El caché puede estar como dict o como string
                if isinstance(cache_valido.datos_json, str):
                    datos = json.loads(cache_valido.datos_json)
                else:
                    datos = cache_valido.datos_json
                
                resultados = datos.get('resultados', [])
                
                # Buscar escenas para ese mes
                escenas_mes = []
                for escena in resultados:
                    fecha = escena.get('date', '')
                    if fecha.startswith(f"{registro.año}-{registro.mes:02d}"):
                        escenas_mes.append({
                            'fecha': fecha,
                            'cloud': escena.get('cloud', 100),
                            'id': escena.get('id')
                        })
                
                if escenas_mes:
                    print(f"      ✅ Caché disponible: {len(escenas_mes)} escena(s)")
                    mejor_escena = min(escenas_mes, key=lambda x: x['cloud'])
                    print(f"      🌟 Mejor escena: {mejor_escena['fecha']} (nubosidad: {mejor_escena['cloud']}%)")
                    print(f"      📷 Imagen NDVI: {'✅ Descargada' if registro.imagen_ndvi else '📥 Puede descargarse (7 requests)'}")
                    print(f"      📷 Imagen NDMI: {'✅ Descargada' if registro.imagen_ndmi else '📥 Puede descargarse (7 requests)'}")
                    print(f"      📷 Imagen SAVI: {'✅ Descargada' if registro.imagen_savi else '📥 Puede descargarse (7 requests)'}")
                else:
                    print(f"      ⚠️  Sin escenas en caché para este mes")
            else:
                print(f"      ❌ Sin caché de Statistics API")
                print(f"      💡 Ejecuta 'Obtener Datos Históricos' primero")
    
    print("\n" + "=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)
    print("\n✅ Sistema optimizado:")
    print("   • Si hay caché: ~7 requests por imagen (1 POST + 6 GET)")
    print("   • Sin caché: Sistema rechaza la descarga (0 requests desperdiciados)")
    print("\n💡 Flujo recomendado:")
    print("   1. Obtener Datos Históricos (crea caché)")
    print("   2. Descargar imágenes específicas según necesidad")
    print("   3. Las imágenes se reusan en múltiples reportes\n")


if __name__ == "__main__":
    try:
        verificar_cache_disponible()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
