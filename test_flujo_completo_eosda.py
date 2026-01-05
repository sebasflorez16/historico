#!/usr/bin/env python
"""
Script para probar el flujo completo de obtención de datos EOSDA
Crea una parcela de prueba, sincroniza con EOSDA y obtiene datos satelitales
"""

import os
import sys
import django
from datetime import date, timedelta
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.gis.geos import GEOSGeometry, Polygon
from informes.models import Parcela
from informes.services.eosda_api import EosdaAPIService
from django.contrib.auth.models import User

def crear_parcela_prueba():
    """Crea una parcela de prueba con geometría válida en Colombia"""
    print("=" * 70)
    print("1️⃣  CREANDO PARCELA DE PRUEBA")
    print("=" * 70)
    
    # Coordenadas de una zona agrícola en Colombia (Valle del Cauca)
    # Polígono pequeño para pruebas
    coords = [
        [-76.5321, 3.4372],  # lng, lat
        [-76.5315, 3.4372],
        [-76.5315, 3.4366],
        [-76.5321, 3.4366],
        [-76.5321, 3.4372]  # Cerrar polígono
    ]
    
    # Crear GeoJSON
    geojson = {
        "type": "Polygon",
        "coordinates": [coords]
    }
    
    # Crear geometría PostGIS
    geometria = GEOSGeometry(json.dumps(geojson), srid=4326)
    
    # Calcular área
    area_m2 = geometria.transform(3857, clone=True).area  # Transformar a metros
    area_ha = area_m2 / 10000
    
    # Crear parcela
    parcela = Parcela.objects.create(
        nombre="Parcela Test EOSDA",
        propietario="Test Usuario",
        geometria=geometria,
        coordenadas=json.dumps(geojson),
        area_hectareas=round(area_ha, 2),
        tipo_cultivo="café",
        fecha_inicio_monitoreo=date.today() - timedelta(days=365),
        activa=True
    )
    
    print(f"✅ Parcela creada:")
    print(f"   ID: {parcela.id}")
    print(f"   Nombre: {parcela.nombre}")
    print(f"   Área: {parcela.area_hectareas} ha")
    print(f"   Geometría: {parcela.geometria.geom_type}")
    print(f"   Puntos: {len(coords)}")
    print(f"   Centro: {parcela.geometria.centroid}")
    print()
    
    return parcela


def sincronizar_con_eosda(parcela):
    """Sincroniza la parcela con EOSDA Field Management API"""
    print("=" * 70)
    print("2️⃣  SINCRONIZANDO CON EOSDA")
    print("=" * 70)
    
    eosda_service = EosdaAPIService()
    
    # Verificar API key
    if not eosda_service.validar_configuracion():
        print("❌ ERROR: API key de EOSDA no configurada")
        return False
    
    print(f"✅ API key configurada: {eosda_service.api_key[:20]}...")
    print()
    
    # Sincronizar
    print("📡 Sincronizando parcela con EOSDA...")
    resultado = eosda_service.sincronizar_parcela_con_eosda(parcela)
    
    if resultado['exito']:
        print(f"✅ Sincronización exitosa!")
        print(f"   Field ID: {resultado['field_id']}")
        print(f"   Ya existía: {resultado.get('ya_existia', False)}")
        print()
        return True
    else:
        print(f"❌ Error en sincronización:")
        print(f"   {resultado['error']}")
        print()
        return False


def obtener_datos_satelitales(parcela):
    """Obtiene datos satelitales históricos de EOSDA"""
    print("=" * 70)
    print("3️⃣  OBTENIENDO DATOS SATELITALES")
    print("=" * 70)
    
    eosda_service = EosdaAPIService()
    
    # Definir rango de fechas (últimos 3 meses para prueba rápida)
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=90)
    
    print(f"📅 Período: {fecha_inicio} a {fecha_fin}")
    print(f"📊 Índices: NDVI, NDMI, SAVI")
    print()
    
    # Obtener usuario admin para el registro
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        usuario = User.objects.first()
    
    print(f"👤 Usuario: {usuario.username if usuario else 'Sin usuario'}")
    print()
    
    # Verificar geometría antes de la llamada
    print("🔍 Verificando geometría antes de llamar API:")
    if parcela.geometria:
        geojson = json.loads(parcela.geometria.geojson)
        print(f"   ✅ Geometría PostGIS disponible")
        print(f"   Tipo: {geojson.get('type')}")
        coords = geojson.get('coordinates', [[]])[0]
        print(f"   Puntos: {len(coords)}")
        print(f"   Primer punto: {coords[0]}")
    elif parcela.coordenadas:
        print(f"   ✅ Coordenadas de respaldo disponibles")
    else:
        print(f"   ❌ Sin geometría")
        return None
    print()
    
    # Llamar API
    print("📡 Llamando a EOSDA API...")
    print("-" * 70)
    
    datos = eosda_service.obtener_datos_optimizado(
        parcela=parcela,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        indices=['NDVI', 'NDMI', 'SAVI'],
        usuario=usuario,
        max_nubosidad=50
    )
    
    print("-" * 70)
    print()
    
    # Analizar resultados
    if 'error' in datos:
        print(f"❌ Error obteniendo datos:")
        print(f"   {datos['error']}")
        return None
    
    resultados = datos.get('resultados', [])
    print(f"✅ Datos recibidos:")
    print(f"   Total escenas: {len(resultados)}")
    print(f"   Method: {datos.get('metodo', 'N/A')}")
    print(f"   Field ID: {datos.get('field_id', 'N/A')}")
    print()
    
    if resultados:
        print(f"📊 Muestra de primera escena:")
        primera = resultados[0]
        print(f"   Fecha: {primera.get('date', 'N/A')}")
        print(f"   Nubosidad: {primera.get('cloud', 'N/A')}%")
        print(f"   View ID: {primera.get('view_id', 'N/A')}")
        
        indexes = primera.get('indexes', {})
        if 'NDVI' in indexes:
            print(f"   NDVI: avg={indexes['NDVI'].get('average')}, min={indexes['NDVI'].get('min')}, max={indexes['NDVI'].get('max')}")
        if 'NDMI' in indexes:
            print(f"   NDMI: avg={indexes['NDMI'].get('average')}, min={indexes['NDMI'].get('min')}, max={indexes['NDMI'].get('max')}")
        if 'SAVI' in indexes:
            print(f"   SAVI: avg={indexes['SAVI'].get('average')}, min={indexes['SAVI'].get('min')}, max={indexes['SAVI'].get('max')}")
        print()
    
    return datos


def main():
    """Ejecutar prueba completa"""
    print()
    print("🧪 TEST COMPLETO DEL FLUJO EOSDA")
    print("=" * 70)
    print()
    
    try:
        # 1. Crear parcela
        parcela = crear_parcela_prueba()
        
        # 2. Sincronizar con EOSDA
        if not sincronizar_con_eosda(parcela):
            print("⚠️  No se pudo sincronizar, abortando prueba")
            return
        
        # Recargar parcela para obtener datos actualizados
        parcela.refresh_from_db()
        
        # 3. Obtener datos satelitales
        datos = obtener_datos_satelitales(parcela)
        
        if datos and datos.get('resultados'):
            print("=" * 70)
            print("✅ PRUEBA EXITOSA - FLUJO COMPLETO FUNCIONANDO")
            print("=" * 70)
            print(f"   ✓ Parcela creada")
            print(f"   ✓ Sincronizada con EOSDA (field_id: {parcela.eosda_field_id})")
            print(f"   ✓ Datos satelitales obtenidos ({len(datos['resultados'])} escenas)")
            print()
        else:
            print("=" * 70)
            print("⚠️  PRUEBA INCOMPLETA")
            print("=" * 70)
            print(f"   ✓ Parcela creada")
            print(f"   ✓ Sincronizada con EOSDA")
            print(f"   ✗ Sin datos satelitales o error en API")
            print()
        
        # Cleanup opcional
        respuesta = input("¿Eliminar parcela de prueba? (s/N): ")
        if respuesta.lower() == 's':
            parcela.delete()
            print("🗑️  Parcela eliminada")
        else:
            print(f"ℹ️  Parcela conservada (ID: {parcela.id})")
        
    except KeyboardInterrupt:
        print("\n⚠️  Prueba cancelada por usuario")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
