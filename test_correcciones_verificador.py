#!/usr/bin/env python3
"""
Script de validación de las correcciones aplicadas al verificador legal
Prueba el manejo correcto de RUNAP nacional con reproyección y filtrado espacial
"""

import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verificador_legal import VerificadorRestriccionesLegales
from shapely.geometry import Point, mapping
import json

def test_carga_runap_nacional():
    """Test 1: Verificar que carga el shapefile nacional correctamente"""
    print("=" * 80)
    print("TEST 1: CARGA DE RUNAP NACIONAL")
    print("=" * 80)
    
    verificador = VerificadorRestriccionesLegales()
    
    print("\n🔍 Cargando áreas protegidas...")
    exito = verificador.cargar_areas_protegidas()
    
    if exito:
        print(f"\n✅ ÉXITO: Áreas protegidas cargadas correctamente")
        print(f"   📊 Total de áreas: {len(verificador.areas_protegidas)}")
        print(f"   🌍 CRS: {verificador.areas_protegidas.crs}")
        
        # Verificar confianza
        confianza = verificador.niveles_confianza['areas_protegidas']
        print(f"\n📋 Nivel de confianza:")
        print(f"   Tipo de dato: {confianza['tipo_dato']}")
        print(f"   Confianza: {confianza['confianza']}")
        print(f"   Razón: {confianza['razon']}")
        
        # Mostrar primeras áreas
        print(f"\n📍 Primeras 5 áreas protegidas:")
        for idx, row in verificador.areas_protegidas.head(5).iterrows():
            nombre = row.get('ap_nombre', row.get('NOMBRE', 'Sin nombre'))
            categoria = row.get('ap_categor', 'Sin categoría')
            print(f"   {idx+1}. {nombre} ({categoria})")
        
        return True
    else:
        print(f"\n❌ FALLO: No se pudieron cargar áreas protegidas")
        return False

def test_reproyeccion_automatica():
    """Test 2: Verificar que la reproyección funciona correctamente"""
    print("\n" + "=" * 80)
    print("TEST 2: REPROYECCIÓN AUTOMÁTICA")
    print("=" * 80)
    
    verificador = VerificadorRestriccionesLegales()
    verificador.cargar_areas_protegidas()
    
    if verificador.areas_protegidas is None:
        print("❌ No hay datos para probar")
        return False
    
    crs_actual = str(verificador.areas_protegidas.crs)
    print(f"\n🔍 Sistema de coordenadas actual: {crs_actual}")
    
    if 'EPSG:4326' in crs_actual or 'WGS 84' in crs_actual:
        print(f"✅ Reproyección exitosa a WGS84")
        return True
    else:
        print(f"❌ Reproyección falló, todavía en {crs_actual}")
        return False

def test_filtrado_espacial_casanare():
    """Test 3: Verificar filtrado espacial para una parcela en Casanare"""
    print("\n" + "=" * 80)
    print("TEST 3: FILTRADO ESPACIAL EN CASANARE")
    print("=" * 80)
    
    verificador = VerificadorRestriccionesLegales()
    verificador.cargar_areas_protegidas()
    
    if verificador.areas_protegidas is None:
        print("❌ No hay datos para probar")
        return False
    
    # Coordenadas de prueba en Casanare (cerca de Yopal)
    # Usar una coordenada que esté dentro de un área protegida conocida
    # Ejemplo: Cerca del DRMI Laguna la Primavera (5.4458°N, 70.4928°W)
    lat, lon = 5.45, -70.50
    
    print(f"\n📍 Parcela de prueba: {lat}°N, {lon}°W")
    
    # Crear geometría de parcela (cuadrado de ~100m x 100m)
    from shapely.geometry import box
    buffer = 0.001  # ~111m
    parcela_geom = box(lon - buffer, lat - buffer, lon + buffer, lat + buffer)
    
    print(f"   Área aproximada: {(buffer * 2 * 111320)**2 / 10000:.2f} ha")
    
    # Filtrar áreas protegidas que intersectan
    areas_cercanas = verificador.areas_protegidas[
        verificador.areas_protegidas.intersects(parcela_geom)
    ]
    
    print(f"\n✅ Áreas protegidas encontradas: {len(areas_cercanas)}")
    
    if len(areas_cercanas) > 0:
        print(f"\n📋 Detalles de áreas encontradas:")
        for idx, row in areas_cercanas.iterrows():
            nombre = row.get('ap_nombre', row.get('NOMBRE', 'Sin nombre'))
            categoria = row.get('ap_categor', 'Sin categoría')
            area_ha = row.get('area_ha_to', 'N/A')
            print(f"   {idx+1}. {nombre}")
            print(f"      Categoría: {categoria}")
            print(f"      Área: {area_ha} ha")
    else:
        print(f"   ℹ️  No se encontraron áreas protegidas en esta ubicación")
    
    return True

def test_verificacion_completa_casanare():
    """Test 4: Verificación completa de una parcela en Casanare"""
    print("\n" + "=" * 80)
    print("TEST 4: VERIFICACIÓN COMPLETA (CASANARE)")
    print("=" * 80)
    
    verificador = VerificadorRestriccionesLegales()
    
    # Cargar todas las capas
    print("\n🔄 Cargando capas geográficas...")
    verificador.cargar_areas_protegidas()
    verificador.cargar_resguardos_indigenas()
    verificador.cargar_paramos()
    
    # Parcela de prueba (fuera de áreas protegidas)
    lat, lon = 5.35, -70.85
    
    print(f"\n📍 Parcela de prueba: {lat}°N, {lon}°W")
    
    # Crear geometría
    from shapely.geometry import box
    buffer = 0.01  # ~1.1 km
    parcela_geom = box(lon - buffer, lat - buffer, lon + buffer, lat + buffer)
    area_ha = (buffer * 2 * 111320)**2 / 10000
    
    print(f"   Área aproximada: {area_ha:.2f} ha")
    
    # Ejecutar verificación
    print(f"\n🔍 Ejecutando verificación legal...")
    resultado = verificador.verificar_parcela(
        parcela_id=1,
        geometria_parcela=mapping(parcela_geom),
        nombre_parcela="Parcela de Prueba Casanare"
    )
    
    # Mostrar resultados
    print(f"\n" + "=" * 80)
    print("RESULTADOS DE VERIFICACIÓN")
    print("=" * 80)
    
    print(f"\n✅ Cumple normativa: {'SÍ' if resultado.cumple_normativa else 'NO'}")
    print(f"📊 Área total: {resultado.area_total_ha:.2f} ha")
    
    if resultado.area_cultivable_ha['determinable']:
        print(f"🌾 Área cultivable: {resultado.area_cultivable_ha['valor_ha']:.2f} ha")
    else:
        print(f"⚠️  Área cultivable: {resultado.area_cultivable_ha['nota']}")
    
    print(f"🚫 Área restringida: {resultado.area_restringida_ha:.2f} ha")
    print(f"📈 Porcentaje restringido: {resultado.porcentaje_restringido:.2f}%")
    
    print(f"\n🔍 Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
    for i, rest in enumerate(resultado.restricciones_encontradas, 1):
        print(f"\n   {i}. {rest['tipo'].upper()}")
        print(f"      Nombre: {rest.get('nombre', 'N/A')}")
        if 'categoria' in rest:
            print(f"      Categoría: {rest['categoria']}")
        print(f"      Área afectada: {rest['area_afectada_ha']:.4f} ha")
        print(f"      Normativa: {rest['normativa']}")
    
    if resultado.advertencias:
        print(f"\n⚠️  ADVERTENCIAS ({len(resultado.advertencias)}):")
        for adv in resultado.advertencias:
            print(f"   • {adv}")
    
    print(f"\n📋 Niveles de confianza:")
    for capa, datos in resultado.niveles_confianza.items():
        if datos['cargada']:
            print(f"   • {capa.replace('_', ' ').title()}: {datos['confianza']} ({datos['razon']})")
        else:
            print(f"   • {capa.replace('_', ' ').title()}: No cargada")
    
    return resultado.cumple_normativa

def main():
    print("🔍 VALIDACIÓN DE CORRECCIONES AL VERIFICADOR LEGAL")
    print("=" * 80)
    
    resultados = {
        'carga_runap': False,
        'reproyeccion': False,
        'filtrado_espacial': False,
        'verificacion_completa': False
    }
    
    try:
        resultados['carga_runap'] = test_carga_runap_nacional()
        resultados['reproyeccion'] = test_reproyeccion_automatica()
        resultados['filtrado_espacial'] = test_filtrado_espacial_casanare()
        resultados['verificacion_completa'] = test_verificacion_completa_casanare()
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 80)
    
    total_tests = len(resultados)
    tests_exitosos = sum(1 for v in resultados.values() if v)
    
    print(f"\n📊 Tests ejecutados: {total_tests}")
    print(f"✅ Tests exitosos: {tests_exitosos}")
    print(f"❌ Tests fallidos: {total_tests - tests_exitosos}")
    
    print(f"\nDetalle:")
    for nombre, exito in resultados.items():
        icono = "✅" if exito else "❌"
        print(f"   {icono} {nombre.replace('_', ' ').title()}")
    
    if tests_exitosos == total_tests:
        print(f"\n🎉 TODAS LAS CORRECCIONES VALIDADAS EXITOSAMENTE")
        return 0
    else:
        print(f"\n⚠️  ALGUNAS CORRECCIONES FALLARON - REVISAR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
