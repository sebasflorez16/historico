#!/usr/bin/env python
"""
Generador de PDF para Verificación Legal de Parcelas Agrícolas
Sistema completo de análisis de restricciones legales con mapas y tablas

Incluye:
- Mapa de la parcela con capas geográficas superpuestas
- Tablas detalladas de restricciones encontradas
- Gráficos de áreas afectadas
- Niveles de confianza por capa
- Recomendaciones legales
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Any, Optional

# ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, 
    Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas

# Matplotlib para mapas y gráficos
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPLPolygon
from matplotlib.collections import PatchCollection
import seaborn as sns

# GeoPandas para mapas
import geopandas as gpd
from shapely.geometry import shape

# Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales, ResultadoVerificacion


class GeneradorPDFLegal:
    """
    Generador de informes PDF para verificación legal de parcelas
    """
    
    def __init__(self):
        """Inicializa el generador de PDF"""
        self.width, self.height = A4
        self.margin = 2 * cm
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura los estilos personalizados para el PDF"""
        
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='TituloPersonalizado',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a472a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubtituloPersonalizado',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2e7d32'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para secciones
        self.styles.add(ParagraphStyle(
            name='SeccionPersonalizada',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#388e3c'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Estilo para advertencias
        self.styles.add(ParagraphStyle(
            name='Advertencia',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#d32f2f'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para éxitos
        self.styles.add(ParagraphStyle(
            name='Exito',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2e7d32'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
    
    def _crear_portada(self, parcela: Parcela, resultado: ResultadoVerificacion, departamento: str = "Casanare") -> List:
        """Crea la portada del informe"""
        elementos = []
        
        # Espacio inicial
        elementos.append(Spacer(1, 2*cm))
        
        # Título principal
        titulo = Paragraph(
            "📋 INFORME DE VERIFICACIÓN LEGAL",
            self.styles['TituloPersonalizado']
        )
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Subtítulo
        subtitulo = Paragraph(
            "Análisis de Restricciones Legales para Parcela Agrícola",
            self.styles['SubtituloPersonalizado']
        )
        elementos.append(subtitulo)
        elementos.append(Spacer(1, 2*cm))
        
        # Información de la parcela con ubicación
        centroide = parcela.geometria.centroid if parcela.geometria else None
        
        info_data = [
            ['Información de la Parcela', ''],
            ['Nombre:', parcela.nombre],
            ['Propietario:', parcela.propietario],
            ['Departamento:', departamento],
            ['Área total:', f'{resultado.area_total_ha:.2f} hectáreas'],
            ['Área cultivable:', f'{resultado.area_cultivable_ha["valor_ha"]:.2f} ha' if resultado.area_cultivable_ha['determinable'] else 'No determinable'],
            ['Coordenadas centro:', f'{centroide.y:.6f}°N, {centroide.x:.6f}°W' if centroide else 'N/A'],
            ['Fecha de verificación:', resultado.fecha_verificacion.split('T')[0]],
        ]
        
        info_table = Table(info_data, colWidths=[6*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elementos.append(info_table)
        elementos.append(Spacer(1, 2*cm))
        
        # Resultado principal
        cumple = resultado.cumple_normativa
        color = colors.HexColor('#2e7d32') if cumple else colors.HexColor('#d32f2f')
        texto_cumple = '✅ CUMPLE CON NORMATIVA AMBIENTAL' if cumple else '❌ NO CUMPLE - RESTRICCIONES ENCONTRADAS'
        
        resultado_box = Table([[texto_cumple]], colWidths=[14*cm])
        resultado_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elementos.append(resultado_box)
        elementos.append(Spacer(1, 1*cm))
        
        # Resumen de restricciones
        num_restricciones = len(resultado.restricciones_encontradas)
        area_restringida = resultado.area_restringida_ha
        porcentaje = resultado.porcentaje_restringido
        
        resumen_data = [
            ['Resumen de Restricciones', ''],
            ['Total de restricciones:', str(num_restricciones)],
            ['Área afectada:', f'{area_restringida:.2f} ha ({porcentaje:.1f}%)'],
        ]
        
        resumen_table = Table(resumen_data, colWidths=[6*cm, 8*cm])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#388e3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elementos.append(resumen_table)
        
        # Salto de página
        elementos.append(PageBreak())
        
        return elementos
    
    def _generar_mapa_parcela(self, parcela: Parcela, verificador: VerificadorRestriccionesLegales) -> BytesIO:
        """
        Genera un mapa de la parcela con las capas geográficas superpuestas
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Convertir geometría de la parcela a GeoDataFrame
        from shapely import wkt
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            parcela_geom = shape(parcela.geometria)
        
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        
        # Dibujar parcela (base)
        parcela_gdf.plot(ax=ax, facecolor='lightgreen', edgecolor='darkgreen', linewidth=2, alpha=0.5, label='Parcela')
        
        # Superponer capas geográficas si están cargadas
        bounds = parcela_gdf.total_bounds  # [minx, miny, maxx, maxy]
        
        # Red hídrica
        if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
            red_clip = verificador.red_hidrica.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
            if len(red_clip) > 0:
                red_clip.plot(ax=ax, color='blue', linewidth=1, alpha=0.7, label='Red Hídrica')
        
        # Áreas protegidas
        if verificador.areas_protegidas is not None and len(verificador.areas_protegidas) > 0:
            areas_clip = verificador.areas_protegidas.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
            if len(areas_clip) > 0:
                areas_clip.plot(ax=ax, facecolor='yellow', edgecolor='orange', linewidth=1, alpha=0.4, label='Áreas Protegidas')
        
        # Resguardos indígenas
        if verificador.resguardos_indigenas is not None and len(verificador.resguardos_indigenas) > 0:
            resguardos_clip = verificador.resguardos_indigenas.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
            if len(resguardos_clip) > 0:
                resguardos_clip.plot(ax=ax, facecolor='purple', edgecolor='darkviolet', linewidth=1, alpha=0.3, label='Resguardos Indígenas')
        
        # Páramos
        if verificador.paramos is not None and len(verificador.paramos) > 0:
            paramos_clip = verificador.paramos.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
            if len(paramos_clip) > 0:
                paramos_clip.plot(ax=ax, facecolor='lightblue', edgecolor='blue', linewidth=1, alpha=0.4, label='Páramos')
        
        # Configurar el mapa
        centroide = parcela_gdf.geometry.centroid.iloc[0]
        ax.set_title(f'Mapa de Verificación Legal\n{parcela.nombre}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud', fontsize=10)
        ax.set_ylabel('Latitud', fontsize=10)
        
        # Agregar leyenda
        ax.legend(loc='upper right', fontsize=8)
        
        # Agregar grid
        ax.grid(True, alpha=0.3)
        
        # Agregar anotación de coordenadas
        ax.text(0.02, 0.02, f'Centro: {centroide.y:.6f}°N, {centroide.x:.6f}°W', 
                transform=ax.transAxes, fontsize=8, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Guardar en BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer
    
    def _crear_seccion_mapa(self, parcela: Parcela, verificador: VerificadorRestriccionesLegales) -> List:
        """Crea la sección del mapa de la parcela"""
        elementos = []
        
        # Título de sección
        titulo = Paragraph("🗺️ MAPA DE LA PARCELA", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Descripción
        texto = Paragraph(
            "El siguiente mapa muestra la ubicación de la parcela y las capas geográficas verificadas "
            "(áreas protegidas, resguardos indígenas, red hídrica y páramos).",
            self.styles['TextoNormal']
        )
        elementos.append(texto)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Generar y agregar mapa
        try:
            img_buffer = self._generar_mapa_parcela(parcela, verificador)
            img = Image(img_buffer, width=16*cm, height=12*cm)
            elementos.append(img)
        except Exception as e:
            texto_error = Paragraph(
                f"⚠️ No se pudo generar el mapa: {str(e)}",
                self.styles['Advertencia']
            )
            elementos.append(texto_error)
        
        elementos.append(Spacer(1, 0.5*cm))
        elementos.append(PageBreak())
        
        return elementos
    
    def _crear_tabla_restricciones(self, resultado: ResultadoVerificacion) -> List:
        """Crea tabla detallada de restricciones encontradas"""
        elementos = []
        
        titulo = Paragraph("📊 DETALLE DE RESTRICCIONES LEGALES", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        if not resultado.restricciones_encontradas:
            texto = Paragraph(
                "✅ <b>No se encontraron restricciones legales</b> en la parcela. "
                "El 100% del área es potencialmente cultivable, sujeto a las regulaciones agrícolas generales.",
                self.styles['Exito']
            )
            elementos.append(texto)
        else:
            # Crear tabla con restricciones
            headers = ['Tipo', 'Nombre', 'Área (ha)', '% Parcela', 'Descripción']
            data = [headers]
            
            for rest in resultado.restricciones_encontradas:
                fila = [
                    rest.get('tipo', 'N/A'),
                    rest.get('nombre', 'N/A')[:30],  # Limitar longitud
                    f"{rest.get('area_interseccion_ha', 0):.2f}",
                    f"{rest.get('porcentaje_area_parcela', 0):.1f}%",
                    rest.get('descripcion', 'N/A')[:50]  # Limitar longitud
                ]
                data.append(fila)
            
            # Crear tabla
            tabla = Table(data, colWidths=[3*cm, 3.5*cm, 2*cm, 2*cm, 5.5*cm])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elementos.append(tabla)
        
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def _crear_seccion_confianza(self, resultado: ResultadoVerificacion) -> List:
        """Crea sección de niveles de confianza con información detallada"""
        elementos = []
        
        titulo = Paragraph("📈 NIVELES DE CONFIANZA DE LOS DATOS", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Mapeo de fuentes oficiales
        fuentes_oficiales = {
            'red_hidrica': 'IGAC - Inst. Geográfico Agustín Codazzi',
            'areas_protegidas': 'PNN - Parques Nacionales Naturales',
            'resguardos_indigenas': 'ANT - Agencia Nacional de Tierras',
            'paramos': 'SIAC - Sistema de Información Ambiental'
        }
        
        # Crear tabla de confianza
        headers = ['Capa Geográfica', 'Confianza', 'Fuente Oficial', 'Elementos', 'Observaciones']
        data = [headers]
        
        for capa, info in resultado.niveles_confianza.items():
            # Emoji según nivel de confianza
            emoji = '✅' if info['confianza'] == 'Alta' else '⚠️' if info['confianza'] == 'Media' else '❌'
            
            # Obtener nombre de fuente oficial
            fuente_oficial = fuentes_oficiales.get(capa, 'Desconocida')
            
            # Obtener número de elementos del desglose
            elementos_count = 'N/A'
            if 'desglose_areas' in resultado.__dict__ and 'areas_por_fuente' in resultado.desglose_areas:
                for area in resultado.desglose_areas['areas_por_fuente']:
                    if area.get('tipo', '').lower().replace(' ', '_') == capa:
                        elementos_count = str(area.get('elementos_verificados', 'N/A'))
                        break
            
            fila = [
                capa.replace('_', ' ').title(),
                f"{emoji} {info['confianza']}",
                fuente_oficial,
                elementos_count,
                info.get('razon', 'Sin observaciones')[:40]
            ]
            data.append(fila)
        
        tabla = Table(data, colWidths=[3.5*cm, 2.5*cm, 4*cm, 2*cm, 4*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#388e3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Centrar columna de elementos
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Nota explicativa
        nota = Paragraph(
            "<b>Nota:</b> Los niveles de confianza indican la calidad y completitud de los datos geográficos utilizados. "
            "Una confianza 'Alta' significa que se utilizaron fuentes oficiales nacionales completas y actualizadas. "
            "Todos los datos provienen de entidades gubernamentales colombianas reconocidas.",
            self.styles['TextoNormal']
        )
        elementos.append(nota)
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def _crear_seccion_advertencias(self, resultado: ResultadoVerificacion) -> List:
        """Crea sección de advertencias"""
        elementos = []
        
        if not resultado.advertencias:
            return elementos
        
        titulo = Paragraph("⚠️ ADVERTENCIAS", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        for adv in resultado.advertencias:
            texto = Paragraph(f"• {adv}", self.styles['Advertencia'])
            elementos.append(texto)
            elementos.append(Spacer(1, 0.2*cm))
        
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def _crear_seccion_recomendaciones(self, resultado: ResultadoVerificacion, parcela: Parcela) -> List:
        """Crea sección de recomendaciones legales"""
        elementos = []
        
        titulo = Paragraph("💡 RECOMENDACIONES LEGALES", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Generar recomendaciones basadas en los resultados
        if resultado.cumple_normativa:
            texto = Paragraph(
                "✅ <b>La parcela CUMPLE con la normativa ambiental vigente.</b><br/><br/>"
                "Se recomienda:<br/>"
                "• Mantener las condiciones actuales del terreno<br/>"
                "• Implementar buenas prácticas agrícolas<br/>"
                "• Realizar monitoreo periódico de la normativa ambiental<br/>"
                "• Consultar con autoridades ambientales locales antes de iniciar proyectos<br/>"
                "• Obtener las licencias y permisos requeridos para actividades agrícolas",
                self.styles['TextoNormal']
            )
        else:
            texto = Paragraph(
                "⚠️ <b>La parcela presenta RESTRICCIONES LEGALES.</b><br/><br/>"
                "Se recomienda:<br/>"
                "• Consultar con un abogado especializado en derecho ambiental<br/>"
                "• Contactar a las autoridades ambientales competentes<br/>"
                "• Evaluar la posibilidad de ajustar el proyecto para evitar áreas restringidas<br/>"
                "• Solicitar permisos especiales si son aplicables<br/>"
                "• Considerar alternativas de uso del suelo compatibles con las restricciones",
                self.styles['Advertencia']
            )
        
        elementos.append(texto)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Nota legal
        nota_legal = Paragraph(
            "<b>NOTA LEGAL:</b> Este informe es de carácter informativo y se basa en datos geográficos oficiales disponibles "
            "al momento de su generación. No constituye un dictamen legal vinculante. Para decisiones definitivas, se recomienda "
            "consultar con las autoridades ambientales competentes y obtener asesoría legal profesional.",
            self.styles['TextoNormal']
        )
        elementos.append(nota_legal)
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def _calcular_distancias_proximidad(self, parcela: Parcela, verificador: VerificadorRestriccionesLegales) -> Dict:
        """
        Calcula las distancias desde el centroide de la parcela a las zonas más cercanas
        """
        from shapely import wkt
        from shapely.ops import nearest_points
        
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            from shapely.geometry import shape
            parcela_geom = shape(parcela.geometria)
        
        centroide = parcela_geom.centroid
        
        distancias = {
            'area_protegida_mas_cercana': None,
            'resguardo_mas_cercano': None,
            'rio_mas_cercano': None,
            'paramo_mas_cercano': None
        }
        
        # Áreas protegidas
        if verificador.areas_protegidas is not None and len(verificador.areas_protegidas) > 0:
            min_dist = float('inf')
            nombre_cercano = None
            for idx, row in verificador.areas_protegidas.iterrows():
                dist = centroide.distance(row.geometry)
                if dist < min_dist:
                    min_dist = dist
                    # Intentar extraer nombre
                    for col in ['NOMBRE', 'nombre', 'NAME', 'name', 'NOMBRE_AP']:
                        if col in row and row[col]:
                            nombre_cercano = row[col]
                            break
            
            if min_dist < float('inf'):
                # Convertir grados a km (aproximado)
                dist_km = min_dist * 111  # 1 grado ≈ 111 km
                distancias['area_protegida_mas_cercana'] = {
                    'nombre': nombre_cercano or 'Área protegida',
                    'distancia_km': dist_km,
                    'dentro': min_dist == 0
                }
        
        # Resguardos indígenas
        if verificador.resguardos_indigenas is not None and len(verificador.resguardos_indigenas) > 0:
            min_dist = float('inf')
            nombre_cercano = None
            for idx, row in verificador.resguardos_indigenas.iterrows():
                dist = centroide.distance(row.geometry)
                if dist < min_dist:
                    min_dist = dist
                    for col in ['NOMBRE', 'nombre', 'NAME', 'name', 'NOM_RESG']:
                        if col in row and row[col]:
                            nombre_cercano = row[col]
                            break
            
            if min_dist < float('inf'):
                dist_km = min_dist * 111
                distancias['resguardo_mas_cercano'] = {
                    'nombre': nombre_cercano or 'Resguardo indígena',
                    'distancia_km': dist_km,
                    'dentro': min_dist == 0
                }
        
        # Red hídrica
        if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
            min_dist = float('inf')
            nombre_cercano = None
            for idx, row in verificador.red_hidrica.iterrows():
                dist = centroide.distance(row.geometry)
                if dist < min_dist:
                    min_dist = dist
                    for col in ['NOMBRE', 'nombre', 'NAME', 'name', 'TOPONI']:
                        if col in row and row[col]:
                            nombre_cercano = row[col]
                            break
            
            if min_dist < float('inf'):
                dist_km = min_dist * 111
                distancias['rio_mas_cercano'] = {
                    'nombre': nombre_cercano or 'Cauce de agua',
                    'distancia_km': dist_km,
                    'dentro': min_dist == 0
                }
        
        # Páramos
        if verificador.paramos is not None and len(verificador.paramos) > 0:
            min_dist = float('inf')
            nombre_cercano = None
            for idx, row in verificador.paramos.iterrows():
                dist = centroide.distance(row.geometry)
                if dist < min_dist:
                    min_dist = dist
                    for col in ['NOMBRE', 'nombre', 'NAME', 'name', 'COMPLEJO']:
                        if col in row and row[col]:
                            nombre_cercano = row[col]
                            break
            
            if min_dist < float('inf'):
                dist_km = min_dist * 111
                distancias['paramo_mas_cercano'] = {
                    'nombre': nombre_cercano or 'Complejo de páramo',
                    'distancia_km': dist_km,
                    'dentro': min_dist == 0
                }
        
        return distancias
    
    def _crear_seccion_proximidad(self, parcela: Parcela, verificador: VerificadorRestriccionesLegales) -> List:
        """Crea sección de análisis de proximidad"""
        elementos = []
        
        titulo = Paragraph("📍 ANÁLISIS DE PROXIMIDAD", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Descripción
        texto_intro = Paragraph(
            "Distancias desde el centro de la parcela a las zonas de interés más cercanas:",
            self.styles['TextoNormal']
        )
        elementos.append(texto_intro)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Calcular distancias
        distancias = self._calcular_distancias_proximidad(parcela, verificador)
        
        # Crear tabla de distancias
        headers = ['Tipo de Zona', 'Zona Más Cercana', 'Distancia', 'Estado']
        data = [headers]
        
        tipos_zonas = {
            'area_protegida_mas_cercana': ('Área Protegida', '🌳'),
            'resguardo_mas_cercano': ('Resguardo Indígena', '🏛️'),
            'rio_mas_cercano': ('Fuente Hídrica', '💧'),
            'paramo_mas_cercano': ('Páramo', '🏔️')
        }
        
        for key, (nombre_tipo, emoji) in tipos_zonas.items():
            if distancias[key] is not None:
                info = distancias[key]
                if info['dentro']:
                    dist_texto = '0 km (DENTRO)'
                    estado = '⚠️ Restricción'
                elif info['distancia_km'] < 1:
                    dist_texto = f'{info["distancia_km"]*1000:.0f} metros'
                    estado = '✅ Seguro'
                else:
                    dist_texto = f'{info["distancia_km"]:.2f} km'
                    estado = '✅ Seguro'
                
                fila = [
                    f"{emoji} {nombre_tipo}",
                    info['nombre'][:30],
                    dist_texto,
                    estado
                ]
            else:
                fila = [
                    f"{emoji} {nombre_tipo}",
                    'No hay en la región',
                    'N/A',
                    '✅ Sin restricción'
                ]
            
            data.append(fila)
        
        tabla = Table(data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 4*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Nota sobre retiros
        nota_retiros = Paragraph(
            "<b>Nota sobre retiros obligatorios:</b> Según el Decreto 1541/1978, se requieren retiros mínimos "
            "de 30-100 metros desde fuentes hídricas dependiendo del tipo de cauce. Las distancias reportadas "
            "son desde el centro de la parcela hasta el punto más cercano de cada zona.",
            self.styles['TextoNormal']
        )
        elementos.append(nota_retiros)
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def generar_pdf(self, parcela: Parcela, resultado: ResultadoVerificacion, 
                   verificador: VerificadorRestriccionesLegales, output_path: str) -> str:
        """
        Genera el PDF completo de verificación legal
        
        Args:
            parcela: Objeto Parcela de Django
            resultado: ResultadoVerificacion del verificador legal
            verificador: Instancia del VerificadorRestriccionesLegales (para acceder a capas)
            output_path: Ruta donde guardar el PDF
        
        Returns:
            Ruta del PDF generado
        """
        print(f"\n{'='*80}")
        print(f"📄 GENERANDO PDF DE VERIFICACIÓN LEGAL")
        print(f"{'='*80}\n")
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Crear documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Lista de elementos del PDF
        elementos = []
        
        # 1. Portada
        print("📋 Generando portada...")
        elementos.extend(self._crear_portada(parcela, resultado))
        
        # 2. Mapa de la parcela
        print("🗺️  Generando mapa de la parcela...")
        elementos.extend(self._crear_seccion_mapa(parcela, verificador))
        
        # 3. Tabla de restricciones
        print("📊 Generando tabla de restricciones...")
        elementos.extend(self._crear_tabla_restricciones(resultado))
        
        # 4. Niveles de confianza
        print("📈 Generando niveles de confianza...")
        elementos.extend(self._crear_seccion_confianza(resultado))
        
        # 5. Advertencias
        if resultado.advertencias:
            print("⚠️  Generando advertencias...")
            elementos.extend(self._crear_seccion_advertencias(resultado))
        
        # 6. Recomendaciones
        print("💡 Generando recomendaciones...")
        elementos.extend(self._crear_seccion_recomendaciones(resultado, parcela))
        
        # 7. Proximidad
        print("📍 Generando análisis de proximidad...")
        elementos.extend(self._crear_seccion_proximidad(parcela, verificador))
        
        # Construir PDF
        print("🔨 Construyendo documento PDF...")
        doc.build(elementos)
        
        print(f"\n✅ PDF generado exitosamente: {output_path}")
        print(f"   Tamaño: {os.path.getsize(output_path) / 1024:.2f} KB")
        print(f"{'='*80}\n")
        
        return output_path


def main():
    """Función principal para generar PDF de verificación legal"""
    print("\n" + "="*80)
    print("🏛️  GENERACIÓN DE PDF DE VERIFICACIÓN LEGAL - PARCELA CASANARE")
    print("="*80)
    
    # 1. Obtener la parcela
    try:
        parcela = Parcela.objects.get(id=6)
        print(f"\n✅ Parcela encontrada:")
        print(f"   ID: {parcela.id}")
        print(f"   Nombre: {parcela.nombre}")
        print(f"   Propietario: {parcela.propietario}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        
        if parcela.geometria:
            centroide = parcela.geometria.centroid
            print(f"   Centroide: {centroide.y:.6f}, {centroide.x:.6f}")
        else:
            print(f"   ❌ ERROR: La parcela no tiene geometría definida")
            return
            
    except Parcela.DoesNotExist:
        print(f"\n❌ ERROR: No se encontró la parcela con id=6")
        return
    
    # 2. Instanciar el verificador legal
    print(f"\n🔍 Iniciando verificación legal...")
    verificador = VerificadorRestriccionesLegales()
    
    # 2.1 Cargar todas las capas geográficas
    print(f"\n📥 Cargando capas geográficas...")
    verificador.cargar_red_hidrica()
    verificador.cargar_areas_protegidas()
    verificador.cargar_resguardos_indigenas()
    verificador.cargar_paramos()
    
    # 3. Ejecutar verificación completa
    print(f"\n📊 Ejecutando verificación de restricciones legales...")
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,
        nombre_parcela=parcela.nombre
    )
    
    # 4. Generar PDF
    output_dir = os.path.join(
        os.path.dirname(__file__),
        'media',
        'verificacion_legal'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(
        output_dir,
        f'verificacion_legal_parcela_{parcela.id}_{timestamp}.pdf'
    )
    
    generador = GeneradorPDFLegal()
    pdf_path = generador.generar_pdf(parcela, resultado, verificador, output_path)
    
    print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
    print(f"   PDF generado: {pdf_path}")
    print(f"\n" + "="*80)


if __name__ == "__main__":
    main()
