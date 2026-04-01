#!/usr/bin/env python3
"""
Genera PDF con análisis de consumo de requests EOSDA para informe histórico.
Ejecutar: python generar_analisis_costos.py
"""

import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime

# Colores corporativos
VERDE = HexColor('#2E8B57')
VERDE_CLARO = HexColor('#E8F5E9')
NARANJA = HexColor('#FF7A00')
NARANJA_CLARO = HexColor('#FFF3E0')
GRIS = HexColor('#6C757D')
GRIS_CLARO = HexColor('#F8F9FA')
AZUL = HexColor('#1976D2')
ROJO = HexColor('#DC3545')


def crear_estilos():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'Titulo', parent=styles['Heading1'],
        fontSize=22, textColor=VERDE, spaceAfter=6,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'Subtitulo', parent=styles['Heading2'],
        fontSize=14, textColor=GRIS, spaceAfter=20,
        fontName='Helvetica', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=15, textColor=VERDE, spaceBefore=20, spaceAfter=10,
        fontName='Helvetica-Bold', borderPadding=(0, 0, 4, 0)
    ))
    styles.add(ParagraphStyle(
        'H3', parent=styles['Heading3'],
        fontSize=12, textColor=HexColor('#2c3e50'), spaceBefore=12, spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, textColor=HexColor('#333333'), spaceAfter=8,
        fontName='Helvetica', leading=14, alignment=TA_JUSTIFY
    ))
    styles.add(ParagraphStyle(
        'BodySmall', parent=styles['Normal'],
        fontSize=8.5, textColor=GRIS, spaceAfter=4,
        fontName='Helvetica', leading=11
    ))
    styles.add(ParagraphStyle(
        'Nota', parent=styles['Normal'],
        fontSize=9, textColor=AZUL, spaceAfter=8,
        fontName='Helvetica-Oblique', leftIndent=15, leading=12
    ))
    styles.add(ParagraphStyle(
        'Alerta', parent=styles['Normal'],
        fontSize=10, textColor=ROJO, spaceAfter=8,
        fontName='Helvetica-Bold', leftIndent=15
    ))
    styles.add(ParagraphStyle(
        'CeldaTabla', parent=styles['Normal'],
        fontSize=9, textColor=HexColor('#333333'),
        fontName='Helvetica', leading=12
    ))
    styles.add(ParagraphStyle(
        'CeldaHeader', parent=styles['Normal'],
        fontSize=9, textColor=white,
        fontName='Helvetica-Bold', leading=12
    ))
    styles.add(ParagraphStyle(
        'Numero', parent=styles['Normal'],
        fontSize=9, textColor=HexColor('#333333'),
        fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=12
    ))
    styles.add(ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=7.5, textColor=GRIS,
        fontName='Helvetica', alignment=TA_CENTER
    ))
    return styles


def tabla_estilizada(data, col_widths, header_color=VERDE):
    """Crea una tabla con estilo corporativo."""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DEE2E6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    t.setStyle(TableStyle(estilo))
    return t


def crear_barra_resumen(label, valor, total, color=VERDE):
    """Mini barra de progreso como Drawing."""
    d = Drawing(460, 28)
    pct = min(valor / total, 1.0) if total > 0 else 0
    d.add(Rect(0, 8, 460, 14, fillColor=GRIS_CLARO, strokeColor=None))
    d.add(Rect(0, 8, 460 * pct, 14, fillColor=color, strokeColor=None))
    d.add(String(5, 10, f"{label}: {valor:,} req", fontSize=8, fillColor=white, fontName='Helvetica-Bold'))
    d.add(String(390, 10, f"{pct*100:.0f}%", fontSize=8, fillColor=black, fontName='Helvetica-Bold'))
    return d


def generar_pdf():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'informes_generados', 'analisis_costos_eosda.pdf')
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    
    doc = SimpleDocTemplate(
        ruta, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.6*inch, bottomMargin=0.6*inch
    )
    
    s = crear_estilos()
    story = []
    
    # ═══════════════════════════════════════
    # PORTADA
    # ═══════════════════════════════════════
    story.append(Spacer(1, 1.2*inch))
    story.append(Paragraph("AGROTECH", s['Titulo']))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="60%", color=NARANJA, thickness=3, spaceAfter=10))
    story.append(Paragraph(
        "Análisis de Consumo de Requests<br/>EOSDA API — Informe Histórico",
        s['Subtitulo']
    ))
    story.append(Spacer(1, 30))
    
    # Info portada
    info_data = [
        ['Escenario', '5,000 hectáreas de palma de aceite'],
        ['Producto', 'Informe Histórico con Timeline Visual'],
        ['Índices', 'NDVI + NDMI + SAVI + NDRE + EVI (5 índices)'],
        ['Período tipo', '12 meses de datos históricos'],
        ['Fecha análisis', datetime.now().strftime('%d de %B de %Y')],
    ]
    t_info = Table(info_data, colWidths=[130, 330])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), VERDE),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, HexColor('#E0E0E0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_info)
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════
    # 1. CÓMO FUNCIONA EL INFORME HISTÓRICO
    # ═══════════════════════════════════════
    story.append(Paragraph("1. Flujo de un Informe Histórico", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    story.append(Paragraph(
        "Cuando se genera un informe histórico para una parcela, el sistema ejecuta "
        "las siguientes operaciones contra la API de EOSDA:",
        s['Body']
    ))
    
    flujo_data = [
        ['Paso', 'Operación', 'Requests', 'Detalle'],
        ['1', 'Sincronizar parcela\n(Field Management)', '1-2',
         'Solo la primera vez. Crea field_id en EOSDA.\nSi ya existe: 0 requests.'],
        ['2', 'Statistics API\n(Datos históricos)', '2',
         '5 índices ÷ 3 máx/petición = 2 lotes.\n1 POST por lote = 2 requests.'],
        ['3', 'Polling resultados\n(GET task status)', '6-12',
         '~3-6 intentos de polling por lote.\nCada poll = 1 GET request.'],
        ['4', 'Imágenes satelitales\n(Field Imagery API)', '21-42',
         '3 req/imagen × 5 índices × ~1-3 escenas/mes\nSolo si se solicita la mejor escena.'],
        ['5', 'Guardar en caché', '0',
         'Se guardan resultados en PostgreSQL.\nDuración: 7 días. Subsiguientes consultas = 0 req.'],
    ]
    
    t_flujo = tabla_estilizada(flujo_data, [35, 120, 55, 250])
    story.append(t_flujo)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Nota: 1 request de Statistics API cubre hasta 20,000 hectáreas y 365 días "
        "de datos en una sola llamada. Esto significa que una parcela de 5,000 ha "
        "NO requiere más requests que una de 100 ha.",
        s['Nota']
    ))
    
    # ═══════════════════════════════════════
    # 2. CONSUMO POR PARCELA (1 INFORME)
    # ═══════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Consumo por Parcela — 1 Informe Histórico", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    story.append(Paragraph("Escenario: 1 parcela, 12 meses, 5 índices (NDVI+NDMI+SAVI+NDRE+EVI)", s['H3']))
    
    consumo_data = [
        ['Operación', 'Sin Caché', 'Con Caché\n(repetición)', 'Notas'],
        ['Statistics API (POST)', '2', '0', '2 lotes de 3+2 índices'],
        ['Polling status (GET)', '~10', '0', '~5 polls × 2 lotes'],
        ['Imágenes por mes (POST+GET)', '~21', '0', '3 req × 5 índices × ~1.4 escenas'],
        ['Total por parcela', '~33', '0', 'Caché = 7 días de validez'],
    ]
    
    t_consumo = tabla_estilizada(consumo_data, [150, 70, 80, 160])
    # Resaltar fila total
    t_consumo.setStyle(TableStyle([
        ('BACKGROUND', (0, -1), (-1, -1), VERDE_CLARO),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t_consumo)
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Sin descargar imágenes (solo estadísticas para PDF): ~12 requests por parcela.",
        s['Nota']
    ))
    
    # ═══════════════════════════════════════
    # 3. ESCENARIOS DE 5,000 HECTÁREAS
    # ═══════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph("3. Escenarios para 5,000 Hectáreas", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    story.append(Paragraph(
        "Dependiendo de cómo se organicen las 5,000 ha en parcelas, "
        "el consumo varía significativamente:",
        s['Body']
    ))
    
    escenarios_data = [
        ['Organización', 'Parcelas', 'Req/Parcela', 'Total 1er\nInforme',
         'Repeticiones\n(caché)', 'Con imágenes'],
        ['1 bloque de 5,000 ha', '1', '~12', '~12', '0', '~33'],
        ['10 lotes de 500 ha', '10', '~12', '~120', '0', '~330'],
        ['25 lotes de 200 ha', '25', '~12', '~300', '0', '~825'],
        ['50 lotes de 100 ha', '50', '~12', '~600', '0', '~1,650'],
    ]
    
    t_esc = tabla_estilizada(escenarios_data, [115, 55, 65, 65, 70, 80])
    story.append(t_esc)
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Importante: Los valores de 'Con imágenes' asumen descarga de la mejor "
        "escena mensual para cada índice. Sin imágenes el consumo es ~65% menor.",
        s['Nota']
    ))
    
    story.append(Paragraph(
        "Recomendación: Organizar en 10-25 lotes para balance entre granularidad y eficiencia.",
        s['Alerta']
    ))
    
    # ═══════════════════════════════════════
    # 4. DESGLOSE DETALLADO — 50 PARCELAS
    # ═══════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Desglose Detallado — Peor Caso (50 parcelas)", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    story.append(Paragraph("Generación única del informe histórico completo (12 meses, 5 índices, con imágenes):", s['Body']))
    
    desglose_data = [
        ['Componente', 'Fórmula', 'Requests'],
        ['Sincronización inicial', '50 parcelas × 2 req', '100'],
        ['Statistics API', '50 parcelas × 2 lotes', '100'],
        ['Polling resultados', '50 parcelas × 2 lotes × 5 polls', '500'],
        ['Imágenes satelitales', '50 parcelas × 5 índices × 1 escena × 3 req', '750'],
        ['', '', ''],
        ['TOTAL 1ra generación', '', '1,450'],
        ['TOTAL 2da generación (caché)', 'Todo desde caché 7 días', '0'],
        ['TOTAL regeneración (caché expirado)', 'Solo datos nuevos', '~1,350'],
    ]
    
    t_desg = tabla_estilizada(desglose_data, [160, 180, 80])
    t_desg.setStyle(TableStyle([
        ('BACKGROUND', (0, 6), (-1, 6), VERDE_CLARO),
        ('FONTNAME', (0, 6), (-1, 8), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 7), (-1, 7), HexColor('#E3F2FD')),
        ('BACKGROUND', (0, 8), (-1, 8), NARANJA_CLARO),
        ('SPAN', (0, 5), (-1, 5)),
        ('LINEABOVE', (0, 6), (-1, 6), 1.5, VERDE),
    ]))
    story.append(t_desg)
    
    # Barras visuales
    story.append(Spacer(1, 15))
    story.append(Paragraph("Distribución de requests:", s['H3']))
    story.append(crear_barra_resumen("Sincronización", 100, 1450, GRIS))
    story.append(Spacer(1, 3))
    story.append(crear_barra_resumen("Statistics API", 100, 1450, AZUL))
    story.append(Spacer(1, 3))
    story.append(crear_barra_resumen("Polling", 500, 1450, NARANJA))
    story.append(Spacer(1, 3))
    story.append(crear_barra_resumen("Imágenes", 750, 1450, ROJO))
    
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "El 52% del consumo es por imágenes satelitales. Si el informe histórico "
        "no necesita imágenes individuales por mes (solo estadísticas), el consumo "
        "baja a ~700 requests.",
        s['Nota']
    ))
    
    # ═══════════════════════════════════════
    # 5. CACHÉ Y OPTIMIZACIÓN
    # ═══════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("5. Sistema de Caché Implementado", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    cache_data = [
        ['Mecanismo', 'Ahorro', 'Cómo funciona'],
        ['Caché PostgreSQL\n(CacheDatosEOSDA)', 'Hasta 100%\nen repeticiones',
         'Guarda respuestas completas por field_id + fechas + índices.\n'
         'TTL: 7 días. Key: SHA256 de los parámetros.'],
        ['Reutilización view_id', '~15 req/imagen',
         'Statistics API retorna view_id de cada escena.\n'
         'Se guarda en IndiceMensual para no buscar de nuevo.'],
        ['Imágenes en disco', '3 req/imagen',
         'Una vez descargada, la imagen se guarda como archivo.\n'
         'No se vuelve a descargar nunca.'],
        ['Batch splitting', 'Reduce errores',
         'Divide 5 índices en lotes de 3+2 automáticamente.\n'
         'Pausa de 5s entre lotes para evitar rate limits.'],
    ]
    
    t_cache = tabla_estilizada(cache_data, [110, 80, 270])
    story.append(t_cache)
    
    # ═══════════════════════════════════════
    # 6. PLANES Y COSTOS EOSDA
    # ═══════════════════════════════════════
    story.append(Spacer(1, 15))
    story.append(Paragraph("6. Planes EOSDA y Costo Estimado", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    story.append(Paragraph(
        "EOSDA no publica precios fijos (pricing custom vía sales). "
        "Estos son estimados basados en el mercado de APIs satelitales:",
        s['Body']
    ))
    
    planes_data = [
        ['Plan', 'Requests', 'Costo USD/mes', '¿Alcanza?'],
        ['Trial (gratis)', '1,000 total', '$0', 'Solo para 1 parcela de prueba'],
        ['Starter', '~10,000/mes', '~$100-200', 'Sí — cubre 50 parcelas con margen'],
        ['Professional', '~50,000/mes', '~$300-500', 'Sobra — para crecimiento futuro'],
        ['Enterprise', 'Ilimitado', 'Negociable', 'Para +10,000 ha'],
    ]
    
    t_planes = tabla_estilizada(planes_data, [90, 90, 100, 180])
    t_planes.setStyle(TableStyle([
        ('BACKGROUND', (0, 2), (-1, 2), VERDE_CLARO),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
    ]))
    story.append(t_planes)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Contacto EOSDA: api.support@eosda.com — Mencionar volumen de 5,000-8,000 ha "
        "para negociar precio corporativo.",
        s['Nota']
    ))
    
    # ═══════════════════════════════════════
    # 7. RESUMEN EJECUTIVO
    # ═══════════════════════════════════════
    story.append(Spacer(1, 15))
    story.append(Paragraph("7. Resumen Ejecutivo", s['H2']))
    story.append(HRFlowable(width="100%", color=VERDE, thickness=1, spaceAfter=10))
    
    resumen_data = [
        ['Métrica', 'Valor'],
        ['Requests por 1 informe histórico (1 parcela)', '~33 (con imágenes) / ~12 (solo stats)'],
        ['Requests totales — 50 parcelas, 1ra generación', '~1,450'],
        ['Requests totales — repetición dentro de 7 días', '0 (caché)'],
        ['Requests mensuales estimados (monitoreo)', '~1,450/mes'],
        ['Plan EOSDA recomendado', 'Starter (~$100-200/mes)'],
        ['Costo por hectárea/mes', '$0.02 - $0.04 USD'],
        ['Costo anual total estimado API', '$1,200 - $2,400 USD'],
        ['', ''],
        ['Ingreso potencial ($1/ha/mes)', '$5,000 USD/mes'],
        ['Margen bruto', '~96%'],
    ]
    
    t_resumen = tabla_estilizada(resumen_data, [240, 220], header_color=HexColor('#2c3e50'))
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, -2), (-1, -1), VERDE_CLARO),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -2), (-1, -1), VERDE),
        ('SPAN', (0, 8), (-1, 8)),
        ('LINEABOVE', (0, 9), (-1, 9), 1, NARANJA),
    ]))
    story.append(t_resumen)
    
    # ═══════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", color=GRIS, thickness=0.5, spaceAfter=8))
    story.append(Paragraph(
        f"AgroTech — Análisis de Costos EOSDA API | Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Basado en documentación oficial EOSDA + código fuente del sistema",
        s['Footer']
    ))
    story.append(Paragraph(
        "Los precios de planes EOSDA son estimados. Consultar api.support@eosda.com para cotización oficial.",
        s['Footer']
    ))
    
    # BUILD
    doc.build(story)
    print(f"\n✅ PDF generado: {ruta}")
    print(f"   Tamaño: {os.path.getsize(ruta) / 1024:.0f} KB")
    return ruta


if __name__ == '__main__':
    ruta = generar_pdf()
    # Abrir automáticamente en macOS
    os.system(f'open "{ruta}"')
