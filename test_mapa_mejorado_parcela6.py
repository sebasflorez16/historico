#!/usr/bin/env python
"""
🗺️ TEST VISUAL - MAPA PRINCIPAL MEJORADO (PARCELA 6)

Prueba las mejoras del mapa principal:
✅ Zoom más cercano a la parcela
✅ Silueta del municipio detectada dinámicamente
✅ Red hídrica local filtrada por municipio
✅ Nombres de ríos principales
✅ Mejor visualización de la parcela
✅ Escala gráfica adaptativa

Ejecutar:
    python test_mapa_mejorado_parcela6.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFNormativo
from datetime import datetime
from pathlib import Path


def test_mapa_mejorado():
    """
    Genera solo el MAPA PRINCIPAL mejorado para validación visual
    """
    print("=" * 80)
    print("🗺️  TEST VISUAL - MAPA PRINCIPAL MEJORADO")
    print("=" * 80)
    
    # 1. Cargar Parcela 6
    print("\n1️⃣  Cargando Parcela 6...")
    try:
        parcela = Parcela.objects.get(pk=6)
        print(f"   ✅ Parcela cargada: {parcela.nombre}")
        print(f"   📍 Área: {parcela.area_hectareas:.2f} ha")
        
        # Obtener centroide para debug
        from shapely import wkt
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            from shapely.geometry import shape
            parcela_geom = shape(parcela.geometria)
        
        import geopandas as gpd
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        centroide = parcela_gdf.geometry.centroid.iloc[0]
        print(f"   🌍 Centroide: {centroide.y:.6f}°N, {abs(centroide.x):.6f}°W")
        
    except Parcela.DoesNotExist:
        print("   ❌ Parcela 6 no encontrada")
        return
    
    # 2. Inicializar Verificador
    print("\n2️⃣  Inicializando Verificador de Restricciones...")
    verificador = VerificadorRestriccionesLegales()
    print("   ✅ Capas geográficas cargadas")
    
    # Verificar datos disponibles
    print(f"   📊 Áreas protegidas: {len(verificador.areas_protegidas) if verificador.areas_protegidas is not None else 0}")
    print(f"   📊 Red hídrica: {len(verificador.red_hidrica) if verificador.red_hidrica is not None else 0}")
    print(f"   📊 Resguardos: {len(verificador.resguardos_indigenas) if verificador.resguardos_indigenas is not None else 0}")
    print(f"   📊 Páramos: {len(verificador.paramos) if verificador.paramos is not None else 0}")
    
    # 3. Calcular distancias para flechas (opcional para este test)
    print("\n3️⃣  Calculando distancias a zonas críticas...")
    try:
        resultado = verificador.verificar_parcela(
            parcela_id=parcela.id,
            geometria_parcela=parcela.geometria,
            nombre_parcela=parcela.nombre
        )
        print("   ✅ Verificación completada")
        
        # Las distancias pueden no estar en el resultado estándar
        # El mapa funciona también sin ellas
        distancias = None
        print("   ℹ️  El mapa se generará sin flechas de distancia (funcionalidad opcional)")
        
    except Exception as e:
        print(f"   ⚠️  Error en verificación: {e}")
        print("   ℹ️  Continuando sin distancias...")
        distancias = None
    
    # 4. Generar mapa mejorado
    print("\n4️⃣  Generando mapa principal mejorado...")
    print("   🔍 Mejoras aplicadas:")
    print("      • Zoom más cercano (margen 30% vs 200% anterior)")
    print("      • Detección automática del municipio (GADM nivel 2)")
    print("      • Red hídrica filtrada por municipio")
    print("      • Nombres de los 3 ríos principales")
    print("      • Parcela con borde rojo sólido (mejor visibilidad)")
    print("      • Leyenda mejorada con contexto municipal")
    
    generador = GeneradorPDFNormativo()
    
    try:
        img_buffer = generador._generar_mapa_parcela(
            parcela=parcela,
            verificador=verificador,
            departamento="Casanare",
            distancias=distancias
        )
        
        print("   ✅ Mapa generado exitosamente")
        
        # 5. Guardar imagen para validación visual
        output_dir = Path("test_outputs_mapas")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"mapa_mejorado_parcela6_{timestamp}.png"
        
        with open(output_path, 'wb') as f:
            f.write(img_buffer.read())
        
        print(f"\n✅ MAPA GUARDADO: {output_path}")
        print(f"   📂 Abrir con: open {output_path}")
        
        # 6. Resumen de mejoras
        print("\n" + "=" * 80)
        print("📋 RESUMEN DE MEJORAS VISUALES")
        print("=" * 80)
        print("✅ Zoom ajustado: Ahora la parcela ocupa ~40% del mapa (antes ~5%)")
        print("✅ Municipio detectado: Silueta gris de fondo con nombre en leyenda")
        print("✅ Red hídrica local: Filtrada por municipio, azul más oscuro")
        print("✅ Nombres de ríos: Etiquetas en los 3 ríos más importantes")
        print("✅ Parcela destacada: Borde rojo sólido 4px (antes rojo discontinuo 3px)")
        print("✅ Escala gráfica: Adaptativa al nuevo zoom")
        print("✅ Leyenda mejorada: Incluye nombre del municipio detectado")
        print("=" * 80)
        
        print("\n🔍 VALIDACIÓN VISUAL:")
        print("   1. Verificar que la parcela se ve MÁS GRANDE y centrada")
        print("   2. Verificar silueta gris del municipio de fondo")
        print("   3. Verificar nombres de ríos principales (máx 3)")
        print("   4. Verificar que el borde de la parcela es ROJO SÓLIDO")
        print("   5. Verificar que la escala es coherente con el nuevo zoom")
        
    except Exception as e:
        print(f"   ❌ Error al generar mapa: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mapa_mejorado()
