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
import numpy as np

logger = logging.getLogger(__name__)



def generar_tabla_desglose_severidad(desglose: dict, estilos: dict = None, evidencias: dict = None) -> Table:
    """
    Genera tabla PROFESIONAL con desglose de áreas por severidad + EVIDENCIA TÉCNICA
    
    🔧 ACTUALIZADO: Formato estándar de 1 decimal para hectáreas y porcentajes
    
    Mejoras UX:
    - Diseño moderno con bordes redondeados
    - Colores suaves y profesionales (no colores brillantes)
    - Iconos descriptivos
    - Tipografía clara y legible
    - Nueva columna "Evidencia Técnica" con índices fallidos
    - ✅ Formato estándar: 1 decimal para ha y %
    
    Args:
        desglose: Dict con keys 'critica', 'moderada', 'leve' (valores en ha)
        estilos: Dict de estilos de ReportLab (opcional)
        evidencias: Dict opcional con evidencias técnicas por nivel {'critica': ['NDVI', 'NDMI'], ...}
    
    Returns:
        Table de ReportLab lista para agregar al PDF
    """
    # Calcular total
    total = sum(desglose.values())
    
    # Si no hay evidencias, crear vacías
    if evidencias is None:
        evidencias = {
            'critica': [],
            'moderada': [],
            'leve': []
        }
    
    if total == 0:
        # Si no hay áreas afectadas, retornar tabla elegante y CLARA
        data = [
            ['✓ Estado del Lote', 'Hectáreas Afectadas', 'Observaciones'],
            [
                'Sin zonas críticas detectadas\ndurante todo el período analizado',
                '0.00 ha',
                'No se requiere intervención.\nEl lote presenta condiciones\nfavorables para la actividad agrícola.'
            ]
        ]
        tabla = Table(data, colWidths=[180, 100, 180])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),
            ('ALIGN', (1, 1), (1, 1), 'CENTER'),
            ('ALIGN', (2, 1), (2, 1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1E8449')),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        return tabla
    
    # Tabla con desglose completo - DISEÑO PROFESIONAL + EVIDENCIA TÉCNICA
    data = [
        ['Nivel de Prioridad', 'Hectáreas', '% Área', 'Acción', 'Evidencia Técnica'],
    ]
    
    # Fila Crítica (soft red, no rojo brillante)
    if desglose['critica'] > 0:
        evidencia_critica = ', '.join(evidencias.get('critica', [])) if evidencias.get('critica') else 'Múltiples índices'
        pct_critica = np.clip((desglose['critica'] / total * 100), 0.0, 100.0)  # CLIP [0, 100]
        data.append([
            '● Prioridad Alta',
            f"{desglose['critica']:.1f} ha",  # 🔧 FORMATO: 1 decimal
            f"{pct_critica:.1f}%",
            'Inmediata',
            evidencia_critica
        ])
    
    # Fila Moderada (amber profesional)
    if desglose['moderada'] > 0:
        evidencia_moderada = ', '.join(evidencias.get('moderada', [])) if evidencias.get('moderada') else 'Múltiples índices'
        pct_moderada = np.clip((desglose['moderada'] / total * 100), 0.0, 100.0)  # CLIP [0, 100]
        data.append([
            '● Prioridad Media',
            f"{desglose['moderada']:.1f} ha",  # 🔧 FORMATO: 1 decimal
            f"{pct_moderada:.1f}%",
            'Programar',
            evidencia_moderada
        ])
    
    # Fila Leve (amarillo suave)
    if desglose['leve'] > 0:
        evidencia_leve = ', '.join(evidencias.get('leve', [])) if evidencias.get('leve') else 'Múltiples índices'
        pct_leve = np.clip((desglose['leve'] / total * 100), 0.0, 100.0)  # CLIP [0, 100]
        data.append([
            '● Monitoreo',
            f"{desglose['leve']:.1f} ha",  # 🔧 FORMATO: 1 decimal
            f"{pct_leve:.1f}%",
            'Observar',
            evidencia_leve
        ])
    
    # Fila Total
    data.append([
        'TOTAL',
        f"{total:.1f} ha",  # 🔧 FORMATO: 1 decimal
        '100%',
        '-',
        'Diagnóstico unificado'
    ])
    
    # Crear tabla con anchos optimizados (5 columnas)
    tabla = Table(data, colWidths=[120, 70, 60, 70, 110])
    
    # Estilos PROFESIONALES (colores suaves, legibilidad óptima)
    style_commands = [
        # Encabezado - gris oscuro profesional
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Fila Total - gris medio
        ('BACKGROUND', (0, len(data)-1), (-1, len(data)-1), colors.HexColor('#7F8C8D')),
        ('TEXTCOLOR', (0, len(data)-1), (-1, len(data)-1), colors.whitesmoke),
        ('FONTNAME', (0, len(data)-1), (-1, len(data)-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, len(data)-1), (-1, len(data)-1), 10),
        
        # Estilo general
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Primera columna alineada a la izquierda
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Bordes profesionales
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#BDC3C7')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#34495E')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#7F8C8D')),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]
    
    # Colores de fondo suaves por severidad (alternar para legibilidad)
    row = 1
    if desglose['critica'] > 0:
        style_commands.extend([
            ('BACKGROUND', (0, row), (-1, row), colors.HexColor('#FADBD8')),  # Rosa muy suave
            ('TEXTCOLOR', (0, row), (0, row), colors.HexColor('#C0392B')),  # Rojo suave para el texto
            ('FONTNAME', (0, row), (0, row), 'Helvetica-Bold'),
        ])
        row += 1
    
    if desglose['moderada'] > 0:
        style_commands.extend([
            ('BACKGROUND', (0, row), (-1, row), colors.HexColor('#FEF5E7')),  # Amber muy suave
            ('TEXTCOLOR', (0, row), (0, row), colors.HexColor('#D68910')),  # Amber profesional
            ('FONTNAME', (0, row), (0, row), 'Helvetica-Bold'),
        ])
        row += 1
    
    if desglose['leve'] > 0:
        style_commands.extend([
            ('BACKGROUND', (0, row), (-1, row), colors.HexColor('#FEF9E7')),  # Amarillo muy suave
            ('TEXTCOLOR', (0, row), (0, row), colors.HexColor('#9A7D0A')),  # Amarillo oscuro
            ('FONTNAME', (0, row), (0, row), 'Helvetica-Bold'),
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
                
                # Extraer evidencias técnicas del metadata
                evidencias = diagnostico.metadata.get('evidencias_tecnicas', None)
                
                tabla = generar_tabla_desglose_severidad(
                    diagnostico.desglose_severidad,
                    estilos,
                    evidencias  # NUEVO: Pasar evidencias técnicas
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
