"""
Helper para integración del Cerebro de Diagnóstico en el PDF
===========================================================

Funciones de utilidad para agregar el diagnóstico unificado al informe PDF.

Uso:
    from informes.helpers.diagnostico_pdf_helper import (
        generar_tabla_desglose_severidad,
        agregar_seccion_diagnostico_unificado
    )
"""

from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import inch
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


def generar_tabla_desglose_severidad(desglose: dict, estilos: dict = None) -> Table:
    """
    Genera tabla profesional con desglose de áreas por severidad
    
    Args:
        desglose: Dict con keys 'critica', 'moderada', 'leve' (valores en ha)
        estilos: Dict de estilos de ReportLab (opcional)
    
    Returns:
        Table de ReportLab lista para agregar al PDF
    
    Ejemplo:
        >>> desglose = {'critica': 12.5, 'moderada': 3.2, 'leve': 1.1}
        >>> tabla = generar_tabla_desglose_severidad(desglose)
        >>> story.append(tabla)
    """
    # Calcular total
    total = sum(desglose.values())
    
    if total == 0:
        # Si no hay áreas afectadas, retornar tabla simple
        data = [
            ['Estado del Lote', 'Área (ha)'],
            ['Sin zonas críticas detectadas', '0.00']
        ]
        tabla = Table(data, colWidths=[350, 100])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        return tabla
    
    # Tabla con desglose completo
    data = [
        ['Nivel de Severidad', 'Área (ha)', '% del Total', 'Prioridad'],
    ]
    
    # Fila Crítica
    if desglose['critica'] > 0:
        data.append([
            '🔴 Crítica',
            f"{desglose['critica']:.2f}",
            f"{(desglose['critica'] / total * 100):.1f}%",
            'INMEDIATA'
        ])
    
    # Fila Moderada
    if desglose['moderada'] > 0:
        data.append([
            '🟠 Moderada',
            f"{desglose['moderada']:.2f}",
            f"{(desglose['moderada'] / total * 100):.1f}%",
            'Alta'
        ])
    
    # Fila Leve
    if desglose['leve'] > 0:
        data.append([
            '🟡 Leve',
            f"{desglose['leve']:.2f}",
            f"{(desglose['leve'] / total * 100):.1f}%",
            'Monitoreo'
        ])
    
    # Fila Total
    data.append([
        'TOTAL AFECTADO',
        f"{total:.2f}",
        '100%',
        '-'
    ])
    
    # Crear tabla
    tabla = Table(data, colWidths=[200, 80, 80, 90])
    
    # Aplicar estilos
    style_commands = [
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Fila Total
        ('BACKGROUND', (0, len(data)-1), (-1, len(data)-1), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, len(data)-1), (-1, len(data)-1), colors.whitesmoke),
        ('FONTNAME', (0, len(data)-1), (-1, len(data)-1), 'Helvetica-Bold'),
        
        # Estilo general
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, len(data)-2), [colors.white, colors.HexColor('#F8F9FA')])
    ]
    
    # Colores específicos por severidad
    row = 1
    if desglose['critica'] > 0:
        style_commands.extend([
            ('BACKGROUND', (0, row), (0, row), colors.HexColor('#FFCCCC')),
            ('TEXTCOLOR', (0, row), (-1, row), colors.HexColor('#C0392B')),
            ('FONTNAME', (0, row), (0, row), 'Helvetica-Bold'),
        ])
        row += 1
    
    if desglose['moderada'] > 0:
        style_commands.extend([
            ('BACKGROUND', (0, row), (0, row), colors.HexColor('#FFE5CC')),
            ('TEXTCOLOR', (0, row), (-1, row), colors.HexColor('#D35400')),
        ])
        row += 1
    
    if desglose['leve'] > 0:
        style_commands.extend([
            ('BACKGROUND', (0, row), (0, row), colors.HexColor('#FFF9CC')),
            ('TEXTCOLOR', (0, row), (-1, row), colors.HexColor('#9A7D0A')),
        ])
    
    tabla.setStyle(TableStyle(style_commands))
    
    return tabla


def agregar_seccion_diagnostico_unificado(
    story: list,
    diagnostico,
    estilos: dict,
    ubicacion: str = 'completa'
):
    """
    Agrega la sección completa del diagnóstico unificado al story del PDF
    
    Args:
        story: Lista de elementos del PDF (platypus story)
        diagnostico: Objeto DiagnosticoUnificado
        estilos: Dict de estilos de ReportLab
        ubicacion: 'completa', 'resumen' o 'detalle'
    
    Ubicaciones:
        - 'completa': Agrega todo (resumen + mapa + detalle)
        - 'resumen': Solo resumen ejecutivo + tabla + mapa
        - 'detalle': Solo diagnóstico técnico detallado
    
    Ejemplo:
        >>> from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
        >>> diagnostico = ejecutar_diagnostico_unificado(...)
        >>> agregar_seccion_diagnostico_unificado(story, diagnostico, estilos, 'completa')
    """
    try:
        if ubicacion in ['completa', 'resumen']:
            # === SECCIÓN RESUMEN ===
            story.append(PageBreak())
            story.append(Paragraph(
                "DIAGNÓSTICO UNIFICADO - MAPA DE SEVERIDAD",
                estilos.get('Heading1', estilos['Normal'])
            ))
            story.append(Spacer(1, 0.2*inch))
            
            # Resumen ejecutivo
            story.append(Paragraph(
                diagnostico.resumen_ejecutivo,
                estilos.get('BodyText', estilos['Normal'])
            ))
            story.append(Spacer(1, 0.3*inch))
            
            # Tabla de desglose
            if diagnostico.desglose_severidad:
                story.append(Paragraph(
                    "<b>Desglose de Áreas por Severidad</b>",
                    estilos.get('Heading3', estilos['Normal'])
                ))
                story.append(Spacer(1, 0.1*inch))
                
                tabla = generar_tabla_desglose_severidad(
                    diagnostico.desglose_severidad,
                    estilos
                )
                story.append(tabla)
                story.append(Spacer(1, 0.3*inch))
            
            # Mapa consolidado
            if diagnostico.mapa_diagnostico_path and os.path.exists(diagnostico.mapa_diagnostico_path):
                story.append(Paragraph(
                    "<b>Mapa Consolidado de Zonas Críticas</b>",
                    estilos.get('Heading3', estilos['Normal'])
                ))
                story.append(Spacer(1, 0.1*inch))
                
                try:
                    img = Image(
                        diagnostico.mapa_diagnostico_path,
                        width=6*inch,
                        height=4.3*inch
                    )
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Pie de foto
                    story.append(Paragraph(
                        "<i>Figura: Mapa consolidado mostrando zonas clasificadas por severidad. "
                        "Las zonas rojas requieren intervención inmediata.</i>",
                        estilos.get('Caption', estilos['Normal'])
                    ))
                    story.append(Spacer(1, 0.3*inch))
                    
                except Exception as e:
                    logger.error(f"Error agregando mapa diagnóstico al PDF: {str(e)}")
                    story.append(Paragraph(
                        f"<i>Error al cargar mapa: {str(e)}</i>",
                        estilos['Normal']
                    ))
            
            # Información de zona prioritaria
            if diagnostico.zona_prioritaria:
                story.append(Paragraph(
                    "<b>Zona Prioritaria de Intervención</b>",
                    estilos.get('Heading3', estilos['Normal'])
                ))
                story.append(Spacer(1, 0.1*inch))
                
                lat, lon = diagnostico.zona_prioritaria.centroide_geo
                info_zona = (
                    f"<b>Diagnóstico:</b> {diagnostico.zona_prioritaria.etiqueta_comercial}<br/>"
                    f"<b>Área:</b> {diagnostico.zona_prioritaria.area_hectareas:.2f} hectáreas<br/>"
                    f"<b>Severidad:</b> {diagnostico.zona_prioritaria.severidad*100:.0f}%<br/>"
                    f"<b>Coordenadas:</b> {lat:.6f}, {lon:.6f}<br/>"
                    f"<b>Confianza:</b> {diagnostico.zona_prioritaria.confianza*100:.0f}%"
                )
                story.append(Paragraph(info_zona, estilos.get('BodyText', estilos['Normal'])))
                story.append(Spacer(1, 0.3*inch))
        
        if ubicacion in ['completa', 'detalle']:
            # === SECCIÓN DETALLE ===
            story.append(PageBreak())
            story.append(Paragraph(
                "DIAGNÓSTICO TÉCNICO DETALLADO",
                estilos.get('Heading1', estilos['Normal'])
            ))
            story.append(Spacer(1, 0.2*inch))
            
            # Diagnóstico detallado
            story.append(Paragraph(
                diagnostico.diagnostico_detallado,
                estilos.get('BodyText', estilos['Normal'])
            ))
            story.append(Spacer(1, 0.3*inch))
            
            # Metadata adicional
            story.append(Paragraph(
                "<b>Información Técnica del Análisis</b>",
                estilos.get('Heading3', estilos['Normal'])
            ))
            story.append(Spacer(1, 0.1*inch))
            
            metadata_text = (
                f"<b>Fecha de análisis:</b> {diagnostico.timestamp.strftime('%d/%m/%Y %H:%M')}<br/>"
                f"<b>Zonas críticas detectadas:</b> {diagnostico.metadata.get('num_zonas', 0)}<br/>"
                f"<b>Eficiencia del lote:</b> {diagnostico.eficiencia_lote:.1f}%<br/>"
                f"<b>Área total afectada:</b> {diagnostico.area_afectada_total:.2f} ha<br/>"
                f"<b>Tipo de informe:</b> {diagnostico.metadata.get('tipo_informe', 'N/A').title()}<br/>"
                f"<b>Resolución espacial:</b> {diagnostico.metadata.get('resolucion_m', 10.0)}m/pixel"
            )
            story.append(Paragraph(metadata_text, estilos.get('BodyText', estilos['Normal'])))
            story.append(Spacer(1, 0.3*inch))
        
        logger.info(f"✅ Sección de diagnóstico unificado agregada al PDF (ubicación: {ubicacion})")
        
    except Exception as e:
        logger.error(f"❌ Error agregando sección de diagnóstico al PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Agregar mensaje de error al PDF
        story.append(Paragraph(
            f"<b>Error al generar sección de diagnóstico:</b> {str(e)}",
            estilos.get('Normal', estilos['Normal'])
        ))


def obtener_resumen_metricas_diagnostico(diagnostico) -> dict:
    """
    Extrae métricas clave del diagnóstico para uso en contextos
    
    Args:
        diagnostico: Objeto DiagnosticoUnificado
    
    Returns:
        Dict con métricas principales
    
    Ejemplo:
        >>> metricas = obtener_resumen_metricas_diagnostico(diagnostico)
        >>> print(metricas['eficiencia_lote'])
        69.3
    """
    return {
        'eficiencia_lote': diagnostico.eficiencia_lote,
        'num_zonas_criticas': len(diagnostico.zonas_criticas),
        'area_afectada_total': diagnostico.area_afectada_total,
        'area_critica': diagnostico.desglose_severidad.get('critica', 0.0),
        'area_moderada': diagnostico.desglose_severidad.get('moderada', 0.0),
        'area_leve': diagnostico.desglose_severidad.get('leve', 0.0),
        'tiene_zona_prioritaria': diagnostico.zona_prioritaria is not None,
        'zona_prioritaria_tipo': diagnostico.zona_prioritaria.tipo_diagnostico if diagnostico.zona_prioritaria else None,
        'zona_prioritaria_area': diagnostico.zona_prioritaria.area_hectareas if diagnostico.zona_prioritaria else 0.0,
        'zona_prioritaria_severidad': diagnostico.zona_prioritaria.severidad if diagnostico.zona_prioritaria else 0.0,
        'timestamp': diagnostico.timestamp,
        'mapa_path': diagnostico.mapa_diagnostico_path
    }
