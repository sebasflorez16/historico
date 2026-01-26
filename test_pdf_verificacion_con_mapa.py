#!/usr/bin/env python
"""
Test completo de generación de PDF con verificación legal Y mapa visual mejorado
Incluye diagnósticos detallados antes de generar el PDF
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
from pathlib import Path
import json

# Importar módulos de verificación
from verificador_legal import VerificadorRestriccionesLegales, ResultadoVerificacion
from pdf_verificacion_legal import agregar_seccion_verificacion_legal


def diagnosticar_datos_red_hidrica():
    """Diagnóstico de los datos de red hídrica descargados"""
    
    print(f"\n{'='*100}")
    print(f"🔍 DIAGNÓSTICO 1: VALIDACIÓN DE DATOS DE RED HÍDRICA")
    print(f"{'='*100}\n")
    
    directorio = Path('datos_geograficos/red_hidrica')
    
    if not directorio.exists():
        print(f"❌ ERROR: Directorio {directorio} no existe")
        return None
    
    shapefiles = list(directorio.glob('*.shp'))
    
    if not shapefiles:
        print(f"❌ ERROR: No se encontraron shapefiles en {directorio}")
        return None
    
    print(f"✅ Shapefiles encontrados: {len(shapefiles)}")
    
    import geopandas as gpd
    
    for i, shp_path in enumerate(shapefiles, 1):
        print(f"\n--- Shapefile {i}/{len(shapefiles)} ---")
        print(f"   Archivo: {shp_path.name}")
        print(f"   Tamaño: {shp_path.stat().st_size / 1024:.1f} KB")
        
        try:
            gdf = gpd.read_file(str(shp_path))
            
            print(f"   ✅ Elementos: {len(gdf)}")
            print(f"   CRS: {gdf.crs}")
            
            # Tipos de geometría
            tipos_geom = gdf.geometry.geom_type.value_counts()
            print(f"   Tipos de geometría:")
            for tipo, count in tipos_geom.items():
                print(f"      • {tipo}: {count}")
                
                # VALIDACIÓN CRÍTICA
                if tipo in ['Polygon', 'MultiPolygon']:
                    print(f"      ⚠️  ADVERTENCIA: {tipo} NO es red de drenaje")
                    print(f"          Estos son polígonos de zonificación, NO ríos/quebradas")
                elif tipo in ['LineString', 'MultiLineString']:
                    print(f"      ✅ CORRECTO: {tipo} representa cauces lineales")
            
            # Columnas
            print(f"   Columnas disponibles:")
            for col in gdf.columns:
                if col != 'geometry':
                    print(f"      • {col}")
            
            # Sample de primer elemento
            if len(gdf) > 0:
                print(f"   Muestra del primer elemento:")
                primer = gdf.iloc[0]
                for col in gdf.columns:
                    if col != 'geometry':
                        val = primer.get(col, 'N/A')
                        if val and str(val) != 'None' and str(val) != 'nan':
                            print(f"      {col}: {val}")
            
        except Exception as e:
            print(f"   ❌ Error leyendo shapefile: {e}")
    
    return shapefiles[0]  # Retornar primer shapefile


def diagnosticar_parcela_restricciones(parcela_id: int, verificador):
    """Diagnóstico detallado de restricciones en una parcela"""
    
    print(f"\n{'='*100}")
    print(f"🔍 DIAGNÓSTICO 2: ANÁLISIS DE RESTRICCIONES EN PARCELA")
    print(f"{'='*100}\n")
    
    parcela = Parcela.objects.get(id=parcela_id)
    
    print(f"📍 Parcela: {parcela.nombre}")
    print(f"   Área registrada: {parcela.area_hectareas:.2f} ha")
    print(f"   Cultivo: {parcela.tipo_cultivo}")
    print(f"   Propietario: {parcela.propietario}")
    
    # Verificar geometría
    from shapely import wkt
    import geopandas as gpd
    
    geom = wkt.loads(parcela.geometria.wkt)
    print(f"\n✅ Geometría válida: {geom.geom_type}")
    print(f"   Bounds: {geom.bounds}")
    
    # Calcular área en métrica
    gdf = gpd.GeoDataFrame([{'geometry': geom}], crs='EPSG:4326')
    gdf_metric = gdf.to_crs('EPSG:3116')
    area_m2 = gdf_metric.iloc[0].geometry.area
    area_ha = area_m2 / 10000
    
    print(f"\n📊 Área calculada (EPSG:3116 - métrica):")
    print(f"   {area_m2:,.2f} m² = {area_ha:.4f} ha")
    print(f"   Diferencia con registro: {abs(area_ha - parcela.area_hectareas):.4f} ha")
    
    # Verificar fuentes hídricas cercanas
    if verificador.red_hidrica is not None:
        print(f"\n🌊 Buscando fuentes hídricas cercanas (radio 5km)...")
        
        buffer_busqueda = gdf_metric.buffer(5000)
        buffer_wgs84 = gpd.GeoDataFrame(
            [{'geometry': buffer_busqueda.iloc[0]}],
            crs='EPSG:3116'
        ).to_crs('EPSG:4326')
        
        red_cercana = verificador.red_hidrica[
            verificador.red_hidrica.intersects(buffer_wgs84.iloc[0].geometry)
        ]
        
        print(f"   ✅ Fuentes hídricas cercanas: {len(red_cercana)}")
        
        if len(red_cercana) > 0:
            print(f"\n   Detalle de fuentes cercanas:")
            for idx, fuente in red_cercana.iterrows():
                nombre = fuente.get('NOMBRE', fuente.get('nombre', 'Sin nombre'))
                tipo_geom = fuente.geometry.geom_type
                
                # Calcular distancia
                fuente_gdf = gpd.GeoDataFrame(
                    [{'geometry': fuente.geometry}],
                    crs='EPSG:4326'
                ).to_crs('EPSG:3116')
                
                distancia_m = gdf_metric.iloc[0].geometry.distance(fuente_gdf.iloc[0].geometry)
                
                print(f"      {idx+1}. {nombre}")
                print(f"         Tipo: {tipo_geom}")
                print(f"         Distancia: {distancia_m:.2f} m")
                
                if distancia_m < 30:
                    print(f"         🚨 DENTRO del retiro de 30m")
                elif distancia_m < 100:
                    print(f"         ⚠️  CERCA del límite de retiro")
                else:
                    print(f"         ✅ Fuera de retiro obligatorio")
        else:
            print(f"   ℹ️  No hay fuentes hídricas en el radio de búsqueda")
    
    return parcela


def generar_pdf_prueba(parcela_id: int):
    """Genera PDF de prueba con verificación legal y mapa mejorado"""
    
    print(f"\n{'='*100}")
    print(f"📄 GENERANDO PDF CON MAPA MEJORADO Y DIAGNÓSTICOS")
    print(f"{'='*100}\n")
    
    # Cargar parcela
    parcela = Parcela.objects.get(id=parcela_id)
    print(f"📍 Parcela: {parcela.nombre} ({parcela.area_hectareas:.2f} ha)")
    
    # Ejecutar verificación legal
    print(f"\n🔍 Ejecutando verificación legal...")
    verificador = VerificadorRestriccionesLegales()
    verificador.cargar_red_hidrica()
    verificador.cargar_areas_protegidas()
    verificador.cargar_resguardos_indigenas()
    verificador.cargar_paramos()
    
    # Verificar parcela
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,
        nombre_parcela=parcela.nombre
    )
    
    if resultado:
        print(f"✅ Verificación completada")
        print(f"   • Cumple: {'SÍ' if resultado.cumple_normativa else 'NO'}")
        print(f"   • Restricciones: {len(resultado.restricciones_encontradas)}")
        
        # NUEVO: Manejar area_cultivable como estructura
        if isinstance(resultado.area_cultivable_ha, dict):
            if resultado.area_cultivable_ha['determinable']:
                print(f"   • Área cultivable: {resultado.area_cultivable_ha['valor_ha']:.2f} ha (preliminar)")
            else:
                print(f"   • Área cultivable: NO DETERMINABLE ({resultado.area_cultivable_ha['nota']})")
        else:
            print(f"   • Área cultivable: {resultado.area_cultivable_ha:.2f} ha")
        
        print(f"   • Área restringida: {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}%)")
        
        # Mostrar detalle de restricciones
        if resultado.restricciones_encontradas:
            print(f"\n   Detalle de restricciones encontradas:")
            for i, rest in enumerate(resultado.restricciones_encontradas, 1):
                print(f"      {i}. {rest.get('nombre', 'Sin nombre')}")
                print(f"         Tipo: {rest.get('tipo', 'N/A')}")
                print(f"         Subtipo: {rest.get('subtipo', 'N/A')}")
                print(f"         Retiro: {rest.get('retiro_minimo_m', 'N/A')}m")
                print(f"         Área afectada: {rest.get('area_afectada_ha', 0):.4f} ha")
                print(f"         Distancia real: {rest.get('distancia_real_m', 'N/A')}m")
                print(f"         Tipo geometría: {rest.get('tipo_geometria', 'N/A')}")
                # NUEVO: Mostrar justificación si existe
                if 'justificacion_retiro' in rest:
                    print(f"         Justificación: {rest.get('justificacion_retiro')}")
    else:
        print(f"❌ Error en verificación")
        return None
    
    # Crear PDF
    output_path = f'test_verificacion_legal_mapa_parcela_{parcela_id}.pdf'
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Crear story
    story = []
    styles = getSampleStyleSheet()
    
    # Título del documento
    titulo = Paragraph(
        f"<b>INFORME DE VERIFICACIÓN LEGAL MEJORADO</b><br/>{parcela.nombre}",
        styles['Title']
    )
    story.append(titulo)
    story.append(Spacer(1, 0.3*inch))
    
    # Info básica
    info = f"""
    <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
    <b>Parcela:</b> {parcela.nombre}<br/>
    <b>Propietario:</b> {parcela.propietario}<br/>
    <b>Cultivo:</b> {parcela.tipo_cultivo}<br/>
    <b>Área Registrada:</b> {parcela.area_hectareas:.2f} hectáreas
    """
    story.append(Paragraph(info, styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # ===== AGREGAR SECCIÓN DE VERIFICACIÓN LEGAL CON MAPA MEJORADO =====
    print(f"\n📄 Generando PDF con mapa mejorado incluido...")
    agregar_seccion_verificacion_legal(
        story=story,
        resultado_verificacion=resultado,
        styles=styles,
        parcela=parcela,
        verificador=verificador  # Pasar verificador para red hídrica
    )
    
    # Construir PDF
    doc.build(story)
    
    # Mostrar resultado
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n{'='*100}")
        print(f"✅ PDF GENERADO EXITOSAMENTE CON MEJORAS")
        print(f"{'='*100}")
        print(f"📁 Archivo: {output_path}")
        print(f"📏 Tamaño: {size_mb:.2f} MB")
        print(f"📊 Restricciones: {len(resultado.restricciones_encontradas)}")
        print(f"🗺️  Mapa mejorado: SÍ (con fuentes hídricas + metadata)")
        print(f"⚠️  Disclaimer incompleto: {'SÍ' if resultado.advertencias else 'NO'}")
        print(f"{'='*100}\n")
        return output_path
    else:
        print(f"❌ Error: PDF no generado")
        return None


if __name__ == '__main__':
    print(f"\n{'#'*100}")
    print(f"{'#'*100}")
    print(f"##  TEST COMPLETO: VERIFICACIÓN LEGAL CON MAPA MEJORADO")
    print(f"##  Incluye diagnósticos + validaciones + PDF final")
    print(f"{'#'*100}")
    print(f"{'#'*100}\n")
    
    # PASO 1: Diagnosticar datos de red hídrica
    shp_path = diagnosticar_datos_red_hidrica()
    
    if not shp_path:
        print(f"\n❌ No se pueden ejecutar tests sin datos de red hídrica")
        sys.exit(1)
    
    # PASO 2: Diagnosticar parcela y restricciones
    verificador = VerificadorRestriccionesLegales()
    verificador.cargar_red_hidrica()
    
    parcela = diagnosticar_parcela_restricciones(parcela_id=1, verificador=verificador)
    
    # PASO 3: Generar PDF final con todas las mejoras
    pdf_path = generar_pdf_prueba(parcela_id=1)
    
    if pdf_path:
        print(f"\n✅ PROCESO COMPLETADO")
        print(f"\n🔍 Para ver el PDF mejorado ejecuta:")
        print(f"   open {pdf_path}")
        print(f"\n📋 El PDF ahora incluye:")
        print(f"   ✅ Red hídrica dibujada en azul")
        print(f"   ✅ Metadata completa (fuente, fecha, CRS)")
        print(f"   ✅ Detalles de distancia real a fuentes")
        print(f"   ✅ Tipo de geometría de cada fuente")
        print(f"   ✅ Disclaimer si verificación incompleta")
        print(f"   ✅ Advertencia si datos son polígonos (incorrectos)")
    else:
        print(f"\n❌ ERROR: No se pudo generar el PDF")
        sys.exit(1)
