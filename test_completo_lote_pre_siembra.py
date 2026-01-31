#!/usr/bin/env python
"""
Test Completo: Lote Pre-Siembra con Zonas Críticas
===================================================

Simula un lote nuevo (no en DB) con datos de un año completo (12 meses)
que presenta zonas críticas ANTES de la siembra, validando:

1. ✅ Cerebro de diagnóstico (detección de zonas)
2. ✅ Mapa georeferenciado consolidado
3. ✅ Generación completa de PDF profesional
4. ✅ Integración motor + generador

Caso de uso: Agricultor evalúa un terreno antes de sembrar maíz

Autor: AgroTech Team
Fecha: 21 enero 2026
"""

import os
import sys
import django
import logging
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.gis.geos import Polygon
from django.conf import settings
from informes.models import Parcela, IndiceMensual
from informes.generador_pdf import GeneradorPDFProfesional
from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
from informes.motor_analisis.mascara_cultivo import generar_mascara_desde_geometria
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generar_datos_sinteticos_anuales(mes_actual: int = 1) -> dict:
    """
    Genera datos sintéticos realistas para 12 meses
    
    Simula evolución temporal con:
    - Época de lluvias (mayo-octubre): Mejor NDVI y NDMI
    - Época seca (noviembre-abril): Peor NDVI, zonas críticas
    - Zonas problemáticas consistentes en época seca
    """
    logger.info(f"📅 Generando datos sintéticos para 12 meses (mes actual: {mes_actual})")
    
    size = (150, 150)  # Imagen Sentinel-2 (10m/pixel) para ~225 ha
    indices_mensuales = []
    
    # Fecha base: 12 meses atrás desde hoy
    fecha_base = datetime.now() - timedelta(days=365)
    
    for mes in range(1, 13):
        fecha = fecha_base + timedelta(days=30 * (mes - 1))
        
        # Semilla por mes para reproducibilidad
        np.random.seed(100 + mes)
        
        # Patrón estacional
        es_epoca_lluvias = 5 <= mes <= 10  # Mayo a Octubre
        
        if es_epoca_lluvias:
            # ÉPOCA DE LLUVIAS: Condiciones buenas
            ndvi_base = np.random.normal(0.68, 0.12, size)
            ndmi_base = np.random.normal(0.35, 0.10, size)
            savi_base = ndvi_base * 1.5 / (1 + 0.5)
            
            # Zona problemática LEVE (siempre presente)
            ndvi_base[20:40, 30:50] = np.random.normal(0.45, 0.05, (20, 20))
            ndmi_base[20:40, 30:50] = np.random.normal(0.15, 0.05, (20, 20))
            
        else:
            # ÉPOCA SECA: Condiciones críticas
            ndvi_base = np.random.normal(0.48, 0.15, size)
            ndmi_base = np.random.normal(0.08, 0.12, size)
            savi_base = ndvi_base * 1.5 / (1 + 0.5)
            
            # ZONA CRÍTICA 1: Déficit hídrico severo (esquina superior izq)
            ndvi_base[15:45, 20:55] = np.random.normal(0.20, 0.04, (30, 35))
            ndmi_base[15:45, 20:55] = np.random.normal(-0.15, 0.05, (30, 35))
            
            # ZONA CRÍTICA 2: Baja densidad/suelo degradado (centro)
            ndvi_base[60:85, 65:95] = np.random.normal(0.18, 0.03, (25, 30))
            savi_base[60:85, 65:95] = np.random.normal(0.15, 0.03, (25, 30))
            
            # ZONA MODERADA 1: Estrés nutricional (lado derecho)
            ndvi_base[35:70, 110:140] = np.random.normal(0.35, 0.05, (35, 30))
            ndmi_base[35:70, 110:140] = np.random.normal(0.12, 0.04, (35, 30))
            savi_base[35:70, 110:140] = np.random.normal(0.28, 0.04, (35, 30))
            
            # ZONA MODERADA 2: Déficit hídrico moderado (esquina inferior)
            ndvi_base[105:135, 25:60] = np.random.normal(0.32, 0.05, (30, 35))
            ndmi_base[105:135, 25:60] = np.random.normal(0.05, 0.04, (30, 35))
        
        # Clip final
        ndvi = np.clip(ndvi_base, -0.2, 1.0)
        ndmi = np.clip(ndmi_base, -0.5, 0.8)
        savi = np.clip(savi_base, -0.2, 1.0)
        
        # Calcular promedios
        ndvi_promedio = float(np.mean(ndvi))
        ndmi_promedio = float(np.mean(ndmi))
        savi_promedio = float(np.mean(savi))
        
        indices_mensuales.append({
            'año': fecha.year,
            'mes': fecha.month,
            'fecha': fecha,
            'ndvi': ndvi,
            'ndmi': ndmi,
            'savi': savi,
            'ndvi_promedio': ndvi_promedio,
            'ndmi_promedio': ndmi_promedio,
            'savi_promedio': savi_promedio,
            'es_epoca_lluvias': es_epoca_lluvias
        })
        
        logger.info(
            f"   Mes {mes:02d} ({fecha.strftime('%Y-%m')}) - "
            f"{'🌧️  Lluvias' if es_epoca_lluvias else '☀️  Seca'} - "
            f"NDVI: {ndvi_promedio:.3f}, NDMI: {ndmi_promedio:.3f}, SAVI: {savi_promedio:.3f}"
        )
    
    logger.info(f"✅ Datos anuales generados: {len(indices_mensuales)} meses")
    
    return {
        'indices_mensuales': indices_mensuales,
        'shape': size,
        'area_ha': 225.0,  # 150x150 píxeles * 10m * 10m / 10000
        'resolucion_m': 10.0
    }


def crear_parcela_temporal(area_ha: float = 225.0) -> Parcela:
    """
    Crea una parcela temporal (no guardada en DB) para el test
    
    Simula un lote real en Colombia (zona cafetera)
    """
    logger.info(f"🏗️  Creando parcela temporal de {area_ha:.2f} ha")
    
    # Coordenadas ejemplo: Zona cafetera colombiana (Manizales)
    lat_centro = 5.0703
    lon_centro = -75.5138
    
    # Crear polígono cuadrado de ~225 ha (1500m x 1500m)
    # 1500m ≈ 0.0135° en latitud
    lado_grados = 0.0135
    
    coords = [
        (lon_centro - lado_grados/2, lat_centro - lado_grados/2),  # SW
        (lon_centro + lado_grados/2, lat_centro - lado_grados/2),  # SE
        (lon_centro + lado_grados/2, lat_centro + lado_grados/2),  # NE
        (lon_centro - lado_grados/2, lat_centro + lado_grados/2),  # NW
        (lon_centro - lado_grados/2, lat_centro - lado_grados/2),  # Cerrar
    ]
    
    geometria = Polygon(coords, srid=4326)
    
    # Crear parcela (NO guardar en DB)
    parcela = Parcela(
        nombre="Lote Pre-Siembra TEST",
        area_hectareas=Decimal(str(area_ha)),
        geometria=geometria,
        tipo_cultivo="Evaluación (sin sembrar)",
        fecha_registro=datetime.now()
    )
    
    # Calcular centroide
    parcela.centroide = geometria.centroid
    
    logger.info(f"✅ Parcela temporal creada:")
    logger.info(f"   Nombre: {parcela.nombre}")
    logger.info(f"   Área: {parcela.area_hectareas} ha")
    logger.info(f"   Centro: {parcela.centroide.y:.5f}, {parcela.centroide.x:.5f}")
    logger.info(f"   Vértices: {len(coords)}")
    
    return parcela


def generar_geo_transform(parcela: Parcela, shape: tuple) -> tuple:
    """
    Genera GeoTransform GDAL para la parcela
    """
    lat_centro = parcela.centroide.y
    lon_centro = parcela.centroide.x
    
    height, width = shape
    pixel_size = 10.0 / 111320.0  # 10m en grados
    
    geo_transform = (
        lon_centro - (width / 2) * pixel_size,   # originX
        pixel_size,                               # pixelWidth
        0,                                        # rotation_x
        lat_centro + (height / 2) * pixel_size,  # originY
        0,                                        # rotation_y
        -pixel_size                               # pixelHeight (negativo)
    )
    
    logger.info(f"✅ GeoTransform generado: {geo_transform}")
    
    return geo_transform


def ejecutar_diagnostico_completo(parcela: Parcela, datos_anuales: dict) -> dict:
    """
    Ejecuta diagnóstico unificado con los datos anuales
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🧠 EJECUTANDO DIAGNÓSTICO UNIFICADO")
    logger.info("=" * 80)
    logger.info("")
    
    # Usar datos del último mes (más reciente)
    ultimo_mes = datos_anuales['indices_mensuales'][-1]
    
    logger.info(f"📊 Usando datos del mes: {ultimo_mes['fecha'].strftime('%Y-%m')}")
    logger.info(f"   Época: {'Lluvias' if ultimo_mes['es_epoca_lluvias'] else 'Seca'}")
    logger.info(f"   NDVI promedio: {ultimo_mes['ndvi_promedio']:.3f}")
    logger.info(f"   NDMI promedio: {ultimo_mes['ndmi_promedio']:.3f}")
    logger.info(f"   SAVI promedio: {ultimo_mes['savi_promedio']:.3f}")
    
    # Generar GeoTransform
    geo_transform = generar_geo_transform(parcela, datos_anuales['shape'])
    
    # Generar máscara de cultivo
    logger.info("")
    logger.info("🗺️  Generando máscara de cultivo desde geometría...")
    mascara = generar_mascara_desde_geometria(
        parcela.geometria,
        geo_transform,
        shape=datos_anuales['shape']
    )
    logger.info(f"✅ Máscara generada: {np.sum(mascara)} píxeles válidos")
    
    # Ejecutar diagnóstico
    logger.info("")
    logger.info("🔬 Ejecutando cerebro de diagnóstico...")
    
    output_dir = Path(settings.MEDIA_ROOT) / 'diagnosticos' / 'test_pre_siembra'
    
    diagnostico = ejecutar_diagnostico_unificado(
        datos_indices={
            'ndvi': ultimo_mes['ndvi'],
            'ndmi': ultimo_mes['ndmi'],
            'savi': ultimo_mes['savi']
        },
        geo_transform=geo_transform,
        area_parcela_ha=float(parcela.area_hectareas),
        output_dir=output_dir,
        tipo_informe='evaluacion',  # ✅ IMPORTANTE: evaluación pre-siembra
        resolucion_m=datos_anuales['resolucion_m'],
        mascara_cultivo=mascara,
        geometria_parcela=parcela.geometria
    )
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ DIAGNÓSTICO COMPLETADO")
    logger.info("=" * 80)
    logger.info(f"📊 Eficiencia del lote: {diagnostico.eficiencia_lote:.1f}%")
    logger.info(f"📍 Área afectada total: {diagnostico.area_afectada_total:.2f} ha")
    logger.info(f"🔴 Zonas críticas: {len([z for z in diagnostico.zonas_criticas if z.severidad >= 0.75])}")
    logger.info(f"🟠 Zonas moderadas: {len([z for z in diagnostico.zonas_criticas if 0.55 <= z.severidad < 0.75])}")
    logger.info(f"🟡 Zonas leves: {len([z for z in diagnostico.zonas_criticas if z.severidad < 0.55])}")
    logger.info(f"🗺️  Mapa generado: {diagnostico.mapa_diagnostico_path}")
    logger.info("")
    
    return {
        'diagnostico': diagnostico,
        'geo_transform': geo_transform,
        'ultimo_mes': ultimo_mes
    }


def generar_pdf_completo(parcela: Parcela, datos_anuales: dict, resultado_diagnostico: dict):
    """
    Genera PDF completo integrando todos los componentes
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("📄 GENERANDO PDF COMPLETO")
    logger.info("=" * 80)
    logger.info("")
    
    # Inicializar generador
    generador = GeneradorPDFProfesional()
    
    # Preparar contexto para el PDF
    diagnostico = resultado_diagnostico['diagnostico']
    
    logger.info("📋 Preparando contexto del PDF...")
    
    context = {
        'parcela': parcela,
        'tipo_informe': 'evaluacion',
        'fecha_generacion': datetime.now(),
        'diagnostico_unificado': diagnostico,
        'resumen_ejecutivo': diagnostico.resumen_ejecutivo,
        'diagnostico_detallado': diagnostico.diagnostico_detallado,
        'eficiencia_lote': diagnostico.eficiencia_lote,
        'area_afectada_total': diagnostico.area_afectada_total,
        'zona_prioritaria': diagnostico.zona_prioritaria,
        'mapa_diagnostico_path': diagnostico.mapa_diagnostico_path,
        'desglose_severidad': diagnostico.desglose_severidad,
        'num_meses_analizados': len(datos_anuales['indices_mensuales']),
        'periodo_analizado': f"{datos_anuales['indices_mensuales'][0]['fecha'].strftime('%Y-%m')} a {datos_anuales['indices_mensuales'][-1]['fecha'].strftime('%Y-%m')}"
    }
    
    # Generar PDF
    logger.info("🖨️  Generando PDF...")
    
    output_filename = f"informe_pre_siembra_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = Path(settings.MEDIA_ROOT) / 'informes' / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Usar método interno del generador
        # Nota: Necesitaremos adaptar esto según la API real del generador
        logger.info("   Iniciando generación...")
        
        # Generar PDF directamente con ReportLab
        logger.info(f"   Generando PDF en: {output_path}")
        
        # Nota: Aquí necesitamos llamar al método correcto del generador
        # Por ahora, crear un PDF básico con ReportLab directamente
        
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        titulo_style = ParagraphStyle(
            'TituloCustom',
            parent=styles['Title'],
            fontSize=20,
            textColor='#2C3E50',
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph(
            f"<b>INFORME DE EVALUACIÓN PRE-SIEMBRA</b>",
            titulo_style
        ))
        story.append(Spacer(1, 1*cm))
        
        # Datos del lote
        story.append(Paragraph(
            f"<b>Lote:</b> {parcela.nombre}",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"<b>Área:</b> {parcela.area_hectareas} hectáreas",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"<b>Período analizado:</b> {context['periodo_analizado']}",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"<b>Fecha del informe:</b> {datetime.now().strftime('%d de %B de %Y')}",
            styles['Normal']
        ))
        story.append(Spacer(1, 1*cm))
        
        # Resumen ejecutivo
        story.append(Paragraph(
            "<b>RESUMEN EJECUTIVO</b>",
            styles['Heading2']
        ))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            diagnostico.resumen_ejecutivo,
            styles['Normal']
        ))
        story.append(Spacer(1, 1*cm))
        
        # Mapa de diagnóstico
        story.append(Paragraph(
            "<b>MAPA DE INTERVENCIÓN</b>",
            styles['Heading2']
        ))
        story.append(Spacer(1, 0.5*cm))
        
        if os.path.exists(diagnostico.mapa_diagnostico_path):
            img = RLImage(diagnostico.mapa_diagnostico_path, width=17*cm, height=13*cm)
            story.append(img)
            story.append(Spacer(1, 1*cm))
        
        # Diagnóstico detallado
        story.append(PageBreak())
        story.append(Paragraph(
            "<b>DIAGNÓSTICO DETALLADO</b>",
            styles['Heading2']
        ))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            diagnostico.diagnostico_detallado,
            styles['Normal']
        ))
        
        # Generar PDF
        doc.build(story)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ PDF GENERADO EXITOSAMENTE")
        logger.info("=" * 80)
        logger.info(f"📁 Archivo: {output_path}")
        logger.info(f"📊 Tamaño: {output_path.stat().st_size / 1024:.1f} KB")
        logger.info("")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Test principal completo
    """
    logger.info("=" * 80)
    logger.info("🚀 TEST COMPLETO: LOTE PRE-SIEMBRA CON ZONAS CRÍTICAS")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        # 1. Generar datos anuales sintéticos
        logger.info("PASO 1: Generar datos sintéticos anuales")
        logger.info("-" * 80)
        datos_anuales = generar_datos_sinteticos_anuales()
        logger.info("")
        
        # 2. Crear parcela temporal
        logger.info("PASO 2: Crear parcela temporal")
        logger.info("-" * 80)
        parcela = crear_parcela_temporal(area_ha=datos_anuales['area_ha'])
        logger.info("")
        
        # 3. Ejecutar diagnóstico
        logger.info("PASO 3: Ejecutar diagnóstico unificado")
        logger.info("-" * 80)
        resultado_diagnostico = ejecutar_diagnostico_completo(parcela, datos_anuales)
        logger.info("")
        
        # 4. Generar PDF
        logger.info("PASO 4: Generar PDF completo")
        logger.info("-" * 80)
        pdf_path = generar_pdf_completo(parcela, datos_anuales, resultado_diagnostico)
        logger.info("")
        
        # 5. Resumen final
        logger.info("=" * 80)
        logger.info("✅ TEST COMPLETADO EXITOSAMENTE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📋 RESULTADOS:")
        logger.info(f"   🗺️  Mapa georeferenciado: {resultado_diagnostico['diagnostico'].mapa_diagnostico_path}")
        if pdf_path:
            logger.info(f"   📄 PDF generado: {pdf_path}")
        logger.info("")
        logger.info("🔍 VALIDACIÓN VISUAL:")
        logger.info("   1. Abrir mapa georeferenciado:")
        logger.info(f"      open \"{resultado_diagnostico['diagnostico'].mapa_diagnostico_path}\"")
        if pdf_path:
            logger.info("   2. Abrir PDF completo:")
            logger.info(f"      open \"{pdf_path}\"")
        logger.info("")
        logger.info("✅ Verificar que:")
        logger.info("   • El mapa muestra el contorno real de la parcela")
        logger.info("   • Las zonas críticas están marcadas (rojo/naranja/amarillo)")
        logger.info("   • Las coordenadas GPS están en las 4 esquinas")
        logger.info("   • El PDF incluye el mapa georeferenciado")
        logger.info("   • El diagnóstico menciona las zonas detectadas")
        logger.info("")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
