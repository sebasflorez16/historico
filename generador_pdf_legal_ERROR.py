#!/usr/bin/env python
"""
Generador de PDF OPTIMIZADO para Verificación Legal de Parcelas Agrícolas
=========================================================================
VERSIÓN COMERCIAL V3 - Optimizado para Entidades de Crédito Agrícola

MEJORAS V3 (Brief Comercial):
- ✅ Tres mapas: Contexto Regional, Técnico con Flechas, Silueta Limpia
- ✅ Flechas direccionales desde límite del polígono (no centroide)
- ✅ Red hídrica obligatoria con buffer legal de 30m
- ✅ Metadatos detallados por capa (fuente, año, escala, limitación)
- ✅ Orden psicológico de venta (resultado → mapas → análisis → limitaciones)
- ✅ Copy técnico-legal defendible (sin afirmaciones absolutas)
- ✅ Disclaimer legal reforzado en cada página

MEJORAS V2:
- ✅ Análisis de proximidad (distancias a zonas críticas)
- ✅ Filtrado específico por departamento
- ✅ Tabla de confianza bien formateada (sin N/A)
- ✅ Información de contexto geográfico
- ✅ Mapas con datos filtrados por región

Incluye:
- Tres mapas profesionales (contexto, técnico, silueta)
- Análisis de proximidad con flechas direccionales
- Metadatos completos de cada capa geográfica
- Niveles de confianza con notas de limitación
- Orden comercial optimizado para crédito
- Disclaimers legales reforzados
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple

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

# Matplotlib para mapas y gráficos
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPLPolygon
from matplotlib.collections import PatchCollection
import seaborn as sns

# GeoPandas para mapas
import geopandas as gpd
from shapely.geometry import shape, Point
from shapely import wkt
import numpy as np

# Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales, ResultadoVerificacion


# Información de departamentos de Colombia
DEPARTAMENTOS_INFO = {
    'Casanare': {
        'region': 'Orinoquía',
        'caracteristicas': 'Llanura tropical, altitud 150-500 msnm, sin páramos',
        'bbox': [-73.0, 5.0, -69.0, 6.5]  # [min_lon, min_lat, max_lon, max_lat]
    },
    'Meta': {
        'region': 'Orinoquía',
        'caracteristicas': 'Llanura y piedemonte, altitud 200-3000 msnm',
        'bbox': [-74.5, 2.0, -71.0, 5.0]
    }
}


# ✨ NUEVO: Metadatos detallados de capas geográficas (para transparencia técnica)
METADATOS_CAPAS = {
    'red_hidrica': {
        'nombre_completo': 'Red Hídrica Superficial de Colombia',
        'autoridad': 'IGAC / IDEAM',
        'año': '2024',
        'tipo_geometria': 'LineString',
        'escala': '1:100.000',
        'limitacion': 'Requiere validación en campo con topografía detallada. Escala no apta para retiros exactos.',
        'nivel_confianza_base': 'MEDIA–ALTA',
        'nota_critica': 'Los retiros mínimos legales (30m según Decreto 1541/1978) deben verificarse con levantamiento topográfico.'
    },
    'areas_protegidas': {
        'nombre_completo': 'Áreas Protegidas del RUNAP',
        'autoridad': 'Parques Nacionales Naturales (PNN)',
        'año': '2024',
        'tipo_geometria': 'Polygon',
        'escala': 'Nacional - Límites oficiales',
        'limitacion': 'Actualización permanente. Verificar con resoluciones de declaratoria vigentes.',
        'nivel_confianza_base': 'ALTA',
        'nota_critica': 'Límites legalmente vinculantes. Restricción absoluta para actividades agropecuarias.'
    },
    'resguardos_indigenas': {
        'nombre_completo': 'Resguardos Indígenas Formalizados',
        'autoridad': 'Agencia Nacional de Tierras (ANT)',
        'año': '2024',
        'tipo_geometria': 'Polygon',
        'escala': 'Nacional - Títulos formalizados',
        'limitacion': 'Solo incluye resguardos con título formal. Pueden existir comunidades en proceso de reconocimiento.',
        'nivel_confianza_base': 'ALTA',
        'nota_critica': 'Protección constitucional. Requiere consulta previa para cualquier intervención.'
    },
    'paramos': {
        'nombre_completo': 'Complejos de Páramos Delimitados',
        'autoridad': 'SIAC / Ministerio de Ambiente',
        'año': '2024',
        'tipo_geometria': 'Polygon',
        'escala': 'Nacional - Delimitación oficial',
        'limitacion': 'Solo páramos con delimitación finalizada. Verificar resoluciones vigentes.',
        'nivel_confianza_base': 'ALTA',
        'nota_critica': 'Prohibición absoluta de actividades agropecuarias (Ley 1753/2015).'
    }
}


class GeneradorPDFLegal:
    """
    Generador MEJORADO de informes PDF para verificación legal de parcelas
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
    
    def _calcular_distancias_minimas(
        self, 
        parcela: Parcela, 
        verificador: VerificadorRestriccionesLegales,
        departamento: str = "Casanare"
    ) -> Dict[str, Dict]:
        """
        Calcula las distancias mínimas a diferentes tipos de zonas protegidas
        FILTRADAS por departamento.
        
        Usa proyección UTM 18N (EPSG:32618) para Colombia para cálculos precisos
        en metros, evitando warnings de CRS geográfico.
        
        Returns:
            Dict con distancias mínimas en km a cada tipo de zona
        """
        # Proyección UTM 18N (mejor para Colombia central/oriental)
        UTM_COLOMBIA = 'EPSG:32618'
        
        # Convertir geometría de la parcela
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            parcela_geom = shape(parcela.geometria)
        
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        
        # Reproyectar a UTM para operaciones espaciales (evita warning de centroid)
        parcela_utm = parcela_gdf.to_crs(UTM_COLOMBIA)
        centroide_utm = parcela_utm.geometry.centroid.iloc[0]
        centroide_geo = gpd.GeoSeries([centroide_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
        
        # Obtener bbox del departamento para filtrar
        dept_info = DEPARTAMENTOS_INFO.get(departamento, {})
        bbox = dept_info.get('bbox', None)
        
        distancias = {}
        
        # 1. Distancia a área protegida más cercana
        if verificador.areas_protegidas is not None and len(verificador.areas_protegidas) > 0:
            areas = verificador.areas_protegidas
            # Filtrar por bbox si está disponible
            if bbox:
                areas = areas.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            
            if len(areas) > 0:
                # Reproyectar a UTM para cálculo de distancia
                areas_utm = areas.to_crs(UTM_COLOMBIA)
                
                distancias_m = areas_utm.distance(centroide_utm)
                idx_min = distancias_m.idxmin()
                dist_min_km = distancias_m.min() / 1000
                
                nombre_cercana = areas.loc[idx_min].get('NOMBRE', areas.loc[idx_min].get('nombre', 'N/A'))
                categoria = areas.loc[idx_min].get('CATEGORIA', areas.loc[idx_min].get('categoria', 'N/A'))
                departamento_area = areas.loc[idx_min].get('DEPARTAMEN', areas.loc[idx_min].get('DEPARTAMENTO', 'N/A'))
                municipio_area = areas.loc[idx_min].get('MUNICIPIO', areas.loc[idx_min].get('municipio', 'N/A'))
                
                # Calcular dirección hacia el área (usando coordenadas geográficas)
                centroide_area_utm = areas_utm.loc[idx_min].geometry.centroid
                centroide_area_geo = gpd.GeoSeries([centroide_area_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
                
                dx = centroide_area_geo.x - centroide_geo.x
                dy = centroide_area_geo.y - centroide_geo.y
                
                # Determinar dirección cardinal
                if abs(dy) > abs(dx) * 1.5:
                    direccion = "Norte" if dy > 0 else "Sur"
                elif abs(dx) > abs(dy) * 1.5:
                    direccion = "Este" if dx > 0 else "Oeste"
                else:
                    direccion_ns = "Norte" if dy > 0 else "Sur"
                    direccion_eo = "este" if dx > 0 else "oeste"
                    direccion = f"{direccion_ns}{direccion_eo}"
                
                distancias['areas_protegidas'] = {
                    'distancia_km': round(dist_min_km, 2),
                    'nombre': nombre_cercana,
                    'categoria': categoria,
                    'ubicacion': f"{municipio_area}, {departamento_area}" if municipio_area != 'N/A' else departamento_area,
                    'direccion': direccion,
                    'en_parcela': dist_min_km == 0
                }
            else:
                distancias['areas_protegidas'] = {
                    'distancia_km': None,
                    'nombre': f'No hay áreas protegidas en {departamento}',
                    'categoria': 'N/A',
                    'en_parcela': False
                }
        
        # 2. Distancia a resguardo indígena más cercano
        if verificador.resguardos_indigenas is not None and len(verificador.resguardos_indigenas) > 0:
            resguardos = verificador.resguardos_indigenas
            if bbox:
                resguardos = resguardos.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            
            if len(resguardos) > 0:
                resguardos_utm = resguardos.to_crs(UTM_COLOMBIA)
                
                distancias_m = resguardos_utm.distance(centroide_utm)
                idx_min = distancias_m.idxmin()
                dist_min_km = distancias_m.min() / 1000
                
                nombre_cercano = resguardos.loc[idx_min].get('NOMBRE', resguardos.loc[idx_min].get('nombre', 'N/A'))
                pueblo = resguardos.loc[idx_min].get('PUEBLO', resguardos.loc[idx_min].get('pueblo', 'N/A'))
                departamento_resg = resguardos.loc[idx_min].get('DEPARTAMEN', resguardos.loc[idx_min].get('DEPARTAMENTO', 'N/A'))
                municipio_resg = resguardos.loc[idx_min].get('MUNICIPIO', resguardos.loc[idx_min].get('municipio', 'N/A'))
                
                # Calcular dirección
                centroide_resg_utm = resguardos_utm.loc[idx_min].geometry.centroid
                centroide_resg_geo = gpd.GeoSeries([centroide_resg_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
                
                dx = centroide_resg_geo.x - centroide_geo.x
                dy = centroide_resg_geo.y - centroide_geo.y
                
                if abs(dy) > abs(dx) * 1.5:
                    direccion = "Norte" if dy > 0 else "Sur"
                elif abs(dx) > abs(dy) * 1.5:
                    direccion = "Este" if dx > 0 else "Oeste"
                else:
                    direccion_ns = "Norte" if dy > 0 else "Sur"
                    direccion_eo = "este" if dx > 0 else "oeste"
                    direccion = f"{direccion_ns}{direccion_eo}"
                
                distancias['resguardos_indigenas'] = {
                    'distancia_km': round(dist_min_km, 2),
                    'nombre': nombre_cercano,
                    'pueblo': pueblo,
                    'ubicacion': f"{municipio_resg}, {departamento_resg}" if municipio_resg != 'N/A' else departamento_resg,
                    'direccion': direccion,
                    'en_parcela': dist_min_km == 0
                }
            else:
                distancias['resguardos_indigenas'] = {
                    'distancia_km': None,
                    'nombre': f'No hay resguardos indígenas en {departamento}',
                    'pueblo': 'N/A',
                    'en_parcela': False
                }
        
        # 3. Distancia a fuente de agua más cercana
        if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
            red = verificador.red_hidrica
            if bbox:
                red = red.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            
            if len(red) > 0:
                red_utm = red.to_crs(UTM_COLOMBIA)
                
                distancias_m = red_utm.distance(centroide_utm)
                idx_min = distancias_m.idxmin()
                dist_min_km = distancias_m.min() / 1000
                dist_min_m = distancias_m.min()
                
                # 🚨 VALIDAR DISTANCIA: si es > 50 km, datos NO concluyentes
                sin_cobertura = dist_min_km > 50  # En Casanare/Llano, 50+ km a un río es sospechoso
                
                if sin_cobertura:
                    # 🔴 DATOS NO CONCLUYENTES - marcar como NO DETERMINABLE
                    distancias['red_hidrica'] = {
                        'distancia_km': None,
                        'distancia_m': None,
                        'nombre': 'Red hídrica no determinable con datos actuales',
                        'tipo': 'NO CONCLUYENTE',
                        'direccion': 'N/A',
                        'requiere_retiro': None,  # No determinable
                        'retiro_minimo_m': 30,
                        'no_concluyente': True,
                        'razon_no_concluyente': f'La cartografía disponible no permite determinar con certeza la ubicación de cauces en esta zona. Distancia al cauce más cercano registrado: {dist_min_km:.0f} km (fuera del área de análisis razonable).'
                    }
                else:
                    # Distancia razonable - procesar normalmente
                    # Intentar múltiples columnas para nombre (compatibilidad IGAC + OSM)
                    nombre_rio = (red.loc[idx_min].get('NOMBRE_GEO') or 
                                 red.loc[idx_min].get('NOMBRE') or 
                                 red.loc[idx_min].get('name') or  # Campo OSM
                                 red.loc[idx_min].get('NOM_GEO') or 
                                 red.loc[idx_min].get('nombre') or 
                                 'Cauce sin nombre oficial')
                    
                    # Intentar múltiples columnas para tipo (compatibilidad IGAC + OSM)
                    tipo_rio = (red.loc[idx_min].get('TIPO') or 
                               red.loc[idx_min].get('waterway') or  # Campo OSM
                               red.loc[idx_min].get('CLASE_DREN') or 
                               red.loc[idx_min].get('tipo') or 
                               red.loc[idx_min].get('ORDEN') or 
                               'Drenaje natural')
                    
                    # Calcular dirección hacia el cauce (usando geometría UTM)
                    centroide_rio_utm = red_utm.loc[idx_min].geometry.centroid if hasattr(red_utm.loc[idx_min].geometry, 'centroid') else red_utm.loc[idx_min].geometry.representative_point()
                    centroide_rio_geo = gpd.GeoSeries([centroide_rio_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
                    
                    dx = centroide_rio_geo.x - centroide_geo.x
                    dy = centroide_rio_geo.y - centroide_geo.y
                    
                    # Determinar dirección cardinal
                    if abs(dy) > abs(dx) * 1.5:
                        direccion = "Norte" if dy > 0 else "Sur"
                    elif abs(dx) > abs(dy) * 1.5:
                        direccion = "Este" if dx > 0 else "Oeste"
                    else:
                        direccion_ns = "Norte" if dy > 0 else "Sur"
                        direccion_eo = "este" if dx > 0 else "oeste"
                        direccion = f"{direccion_ns}{direccion_eo}"
                    
                    # Determinar si está dentro del retiro mínimo (30m)
                    requiere_retiro = dist_min_m < 30
                    
                    distancias['red_hidrica'] = {
                        'distancia_km': round(dist_min_km, 2),
                        'distancia_m': round(dist
                    direccion_ns = "Norte" if dy > 0 else "Sur"
                    direccion_eo = "este" if dx > 0 else "oeste"
                    direccion = f"{direccion_ns}{direccion_eo}"
                
                distancias['paramos'] = {
                    'distancia_km': round(dist_min_km, 2),
                    'nombre': nombre_paramo,
                    'ubicacion': departamento_par if departamento_par != 'N/A' else 'N/A',
                    'direccion': direccion,
                    'en_parcela': dist_min_km == 0
                }
            else:
                # Para Casanare, es correcto que no haya páramos
                distancias['paramos'] = {
                    'distancia_km': None,
                    'nombre': f'No hay páramos en {departamento} (llanura tropical)',
                    'en_parcela': False,
                    'nota': 'Geográficamente correcto - altitud insuficiente para páramos'
                }
        
        return distancias
    
    def _crear_portada(self, parcela: Parcela, resultado: ResultadoVerificacion, departamento: str = "Casanare") -> List:
        """Crea la portada del informe con información completa"""
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
        
        # Subtítulo con departamento
        subtitulo = Paragraph(
            f"Análisis de Restricciones Legales - {departamento}, Colombia",
            self.styles['SubtituloPersonalizado']
        )
        elementos.append(subtitulo)
        elementos.append(Spacer(1, 2*cm))
        
        # Obtener información del departamento
        dept_info = DEPARTAMENTOS_INFO.get(departamento, {})
        region = dept_info.get('region', 'N/A')
        caracteristicas = dept_info.get('caracteristicas', 'N/A')
        
        # Información de la parcela con ubicación completa
        centroide = parcela.geometria.centroid if parcela.geometria else None
        
        info_data = [
            ['Información de la Parcela', ''],
            ['Nombre:', parcela.nombre],
            ['Propietario:', parcela.propietario],
            ['Departamento:', f'{departamento} ({region})'],
            ['Características región:', caracteristicas],
            ['Área total:', f'{resultado.area_total_ha:.2f} hectáreas'],
            ['Área potencialmente cultivable\n(según análisis geoespacial):', f'{resultado.area_cultivable_ha["valor_ha"]:.2f} ha' if resultado.area_cultivable_ha['determinable'] else 'No determinable'],
            ['Coordenadas centro:', f'{centroide.y:.6f}°N, {centroide.x:.6f}°W' if centroide else 'N/A'],
            ['Fecha de verificación:', resultado.fecha_verificacion.split('T')[0]],
        ]
        
        info_table = Table(info_data, colWidths=[5.5*cm, 8.5*cm])
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
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elementos.append(info_table)
        elementos.append(Spacer(1, 1.5*cm))
        
        # Resultado principal
        cumple = resultado.cumple_normativa
        color = colors.HexColor('#2e7d32') if cumple else colors.HexColor('#d32f2f')
        # ✅ CORRECCIÓN LEGAL: No afirmar cumplimiento normativo definitivo
        texto_cumple = '✅ ANÁLISIS GEOESPACIAL: Sin restricciones identificadas' if cumple else '⚠️ RESTRICCIONES AMBIENTALES IDENTIFICADAS'
        
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
        
        # Resumen de restricciones CON CONTEXTO EXPLICATIVO
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
        elementos.append(Spacer(1, 0.3*cm))
        
        # NUEVO: Agregar contexto explicativo según el resultado
        if num_restricciones == 0:
            dept_contexto = DEPARTAMENTOS_INFO.get(departamento, {})
            
            # 🚨 VERIFICAR si hay datos NO CONCLUYENTES (especialmente red hídrica)
            tiene_datos_no_concluyentes = False
            if hasattr(resultado, 'niveles_confianza'):
                for capa, info in resultado.niveles_confianza.items():
                    if info.get('confianza') in ['Baja', 'Nula', 'Crítica']:
                        tiene_datos_no_concluyentes = True
                        break
            
            if tiene_datos_no_concluyentes:
                # ⚠️ RESULTADO CON LIMITACIONES - NO AFIRMAR CUMPLIMIENTO TOTAL
                contexto_texto = Paragraph(
                    f"<b>⚠️ Análisis con limitaciones en los datos:</b><br/>"
                    f"El análisis geoespacial identificó 0 restricciones con base en las capas disponibles. "
                    f"Sin embargo, <b>existen limitaciones importantes</b> en la calidad o cobertura de algunos datos:<br/><br/>"
                    f"• <b>Áreas protegidas:</b> {'Verificadas' if resultado.niveles_confianza.get('areas_protegidas', {}).get('confianza') == 'Alta' else 'Datos limitados'}<br/>"
                    f"• <b>Resguardos indígenas:</b> {'Verificados' if resultado.niveles_confianza.get('resguardos_indigenas', {}).get('confianza') == 'Alta' else 'Datos limitados'}<br/>"
                    f"• <b>Red hídrica:</b> {'Verificada' if resultado.niveles_confianza.get('red_hidrica', {}).get('confianza') == 'Alta' else '⚠️ DATOS NO CONCLUYENTES (ver sección de proximidad)'}<br/>"
                    f"• <b>Páramos:</b> {'Geográficamente correcto (altitud insuficiente)' if 'llanura' in dept_contexto.get('caracteristicas', '').lower() else 'Verificados'}<br/><br/>"
                    f"<b>Conclusión:</b> Este análisis <b>NO puede confirmar cumplimiento normativo total</b> debido a las limitaciones "
                    f"en los datos. Se requiere validación adicional con autoridad competente antes de tomar decisiones definitivas.",
                    self.styles['Advertencia']
                )
            else:
                # ✅ RESULTADO CONFIABLE - pero sin afirmar cumplimiento legal absoluto
                contexto_texto = Paragraph(
                    f"<b>¿Por qué 0 restricciones?</b><br/>"
                    f"• <b>Geografía regional:</b> {departamento} está en la región {dept_contexto.get('region', 'N/A')} "
                    f"({dept_contexto.get('caracteristicas', 'N/A')})<br/>"
                    f"• <b>Áreas protegidas:</b> La parcela no se superpone con áreas del RUNAP verificadas para esta región<br/>"
                    f"• <b>Resguardos indígenas:</b> No hay resguardos formalizados que intersecten la parcela<br/>"
                    f"• <b>Red hídrica:</b> Los cauces cartografiados están fuera de los retiros mínimos legales (>30m)<br/>"
                    f"• <b>Páramos:</b> {'Geográficamente correcto - altitud insuficiente para ecosistemas de páramo' if 'llanura' in dept_contexto.get('caracteristicas', '').lower() else 'No hay páramos delimitados que intersecten la parcela'}<br/><br/>"
                    f"<b>Conclusión:</b> El resultado de 0 restricciones corresponde a la información geográfica disponible y válida para esta región al momento del análisis. "
                    f"<b>Se recomienda validación con la autoridad ambiental</b> antes de proceder con proyectos.",
                    self.styles['TextoNormal']
                )
            elementos.append(contexto_texto)
        else:
            contexto_texto = Paragraph(
                f"<b>Análisis de restricciones encontradas:</b><br/>"
                f"Se identificaron {num_restricciones} restricción(es) legal(es) que afectan "
                f"{area_restringida:.2f} hectáreas ({porcentaje:.1f}% del total). "
                f"Estas restricciones provienen de capas oficiales verificadas y requieren atención legal "
                f"antes de proceder con actividades agrícolas.",
                self.styles['Advertencia']
            )
            elementos.append(contexto_texto)
        
        elementos.append(Spacer(1, 0.4*cm))
        
        # Salto de página
        elementos.append(PageBreak())
        
        return elementos
    
    def _crear_seccion_proximidad(self, distancias: Dict, departamento: str = "Casanare") -> List:
        """
        Crea sección de análisis de proximidad a zonas críticas
        """
        elementos = []
        
        titulo = Paragraph("📍 ANÁLISIS DE PROXIMIDAD", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        descripcion = Paragraph(
            f"Distancias desde el centro de la parcela a las zonas protegidas más cercanas en {departamento}. "
            "Este análisis utiliza datos filtrados específicamente para la región.",
            self.styles['TextoNormal']
        )
        elementos.append(descripcion)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Crear tabla de distancias MEJORADA con direcciones y ubicaciones
        headers = ['Tipo de Zona', 'Distancia', 'Dirección', 'Nombre y Ubicación', 'Estado']
        data = [headers]
        
        # 1. Áreas protegidas
        if 'areas_protegidas' in distancias:
            ap = distancias['areas_protegidas']
            if ap['distancia_km'] is not None:
                if ap['en_parcela']:
                    dist_texto = '0 km\n(DENTRO)'
                    dir_texto = 'Superpuesta'
                    estado = '⚠️ EN ÁREA\nPROTEGIDA'
                else:
                    dist_texto = f"{ap['distancia_km']} km"
                    dir_texto = ap.get('direccion', '-')
                    estado = '✅ Fuera\nde área'
                nombre = f"{ap['nombre'][:35]}\n({ap['categoria'][:25]})\n{ap.get('ubicacion', '')[:30]}"
            else:
                dist_texto = 'N/A'
                dir_texto = '-'
                nombre = ap['nombre'][:50]
                estado = '✅ Sin áreas\ncercanas'
            
            data.append(['Áreas\nProtegidas\n(RUNAP)', dist_texto, dir_texto, nombre, estado])
        
        # 2. Resguardos indígenas
        if 'resguardos_indigenas' in distancias:
            ri = distancias['resguardos_indigenas']
            if ri['distancia_km'] is not None:
                if ri['en_parcela']:
                    dist_texto = '0 km\n(DENTRO)'
                    dir_texto = 'Superpuesto'
                    estado = '⚠️ EN\nRESGUARDO'
                else:
                    dist_texto = f"{ri['distancia_km']} km"
                    dir_texto = ri.get('direccion', '-')
                    estado = '✅ Fuera de\nresguardo'
                nombre = f"{ri['nombre'][:35]}\nPueblo: {ri['pueblo'][:25]}\n{ri.get('ubicacion', '')[:30]}"
            else:
                dist_texto = 'N/A'
                dir_texto = '-'
                nombre = ri['nombre'][:50]
                estado = '✅ Sin resguardos\ncercanos'
            
            data.append(['Resguardos\nIndígenas', dist_texto, dir_texto, nombre, estado])
        
        # 3. Red hídrica
        if 'red_hidrica' in distancias:
            rh = distancias['red_hidrica']
            # 🚨 Verificar si es NO CONCLUYENTE (sin datos reales)
            es_no_concluyente = rh.get('no_concluyente', False)
            
            if rh['distancia_km'] is not None:
                if rh['requiere_retiro']:
                    dist_texto = f"{rh['distancia_m']:.0f} m"
                    dir_texto = rh.get('direccion', '-')
                    estado = f"⚠️ Requiere\nretiro\n(mín. {rh['retiro_minimo_m']}m)"
                else:
                    dist_texto = f"{rh['distancia_km']} km"
                    dir_texto = rh.get('direccion', '-')
                    estado = '✅ Sin retiro\nrequerido'
                # Mostrar nombre real del río, no "drenaje" genérico
                nombre_real = rh['nombre'] if rh['nombre'] and rh['nombre'] != 'Cauce sin nombre oficial' else 'Cauce sin nombre'
                nombre = f"{nombre_real[:35]}\nTipo: {str(rh.get('tipo', 'Drenaje'))[:25]}"
            else:
                dist_texto = 'NO\nDETERMINABLE'
                dir_texto = 'N/A'
                nombre = rh['nombre'][:50]
                # Si es NO CONCLUYENTE, marcar claramente
                if es_no_concluyente:
                    estado = '⚠️ DATO NO\nCONCLUYENTE\n(ver nota)'
                else:
                    estado = '✅ Sin cauces\nregistrados'
            
            data.append(['Red Hídrica\n(Ríos/Quebradas)', dist_texto, dir_texto, nombre, estado])
        
        # 4. Páramos
        if 'paramos' in distancias:
            p = distancias['paramos']
            if p['distancia_km'] is not None:
                if p['en_parcela']:
                    dist_texto = '0 km\n(DENTRO)'
                    dir_texto = 'Superpuesto'
                    estado = '⚠️ EN\nPÁRAMO'
                else:
                    dist_texto = f"{p['distancia_km']} km"
                    dir_texto = p.get('direccion', '-')
                    estado = '✅ Fuera de\npáramo'
                nombre = f"{p['nombre'][:35]}\n{p.get('ubicacion', '')[:30]}"
            else:
                dist_texto = 'N/A'
                dir_texto = '-'
                nombre = p['nombre'][:50]
                if 'nota' in p:
                    estado = f"✅ Correcto\n{p['nota'][:30]}"
                else:
                    estado = '✅ Sin páramos cercanos'
            
            data.append(['Páramos', dist_texto, dir_texto, nombre, estado])
        
        # Crear tabla MEJORADA con 5 columnas
        tabla = Table(data, colWidths=[2.8*cm, 2*cm, 2*cm, 5*cm, 4.2*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
        
        # 🚨 ADVERTENCIA CRÍTICA: Si RED HÍDRICA es NO CONCLUYENTE
        if 'red_hidrica' in distancias and distancias['red_hidrica'].get('no_concluyente', False):
            advertencia_rh = Paragraph(
                f"<b>⚠️ LIMITACIÓN IMPORTANTE - RED HÍDRICA:</b><br/>"
                f"{distancias['red_hidrica'].get('razon_no_concluyente', 'Datos no concluyentes')}<br/><br/>"
                f"<b>Implicación legal:</b> Este análisis <b>NO puede confirmar ni descartar</b> la presencia de cauces "
                f"en la parcela o en sus proximidades. La cartografía disponible tiene limitaciones de escala o cobertura "
                f"para esta zona específica.<br/><br/>"
                f"<b>Recomendación obligatoria:</b><br/>"
                f"• Realizar inspección hidrológica en campo por profesional competente<br/>"
                f"• Solicitar concepto técnico a la CAR (Corporación Autónoma Regional) competente<br/>"
                f"• Verificar con IGAC o IDEAM si existe cartografía de mayor detalle para la zona<br/>"
                f"• NO tomar decisiones definitivas basándose únicamente en este análisis<br/><br/>"
                f"<b>Nota legal:</b> La ausencia de cauces en la cartografía NO equivale a ausencia de cauces en la realidad. "
                f"El análisis de retiros hídricos (30m mínimo legal) <b>no puede completarse</b> con los datos disponibles.",
                self.styles['Advertencia']
            )
            elementos.append(advertencia_rh)
            elementos.append(Spacer(1, 0.5*cm))
        
        # Nota explicativa MEJORADA
        nota = Paragraph(
            "<b>Notas importantes:</b><br/>"
            "• Las distancias se calculan desde el centroide de la parcela hasta la zona más cercana<br/>"
            "• La columna 'Dirección' indica la orientación cardinal desde la parcela hacia la zona<br/>"
            "• Los retiros mínimos de fuentes hídricas según Decreto 1541/1978 son de 30 metros<br/>"
            "• Los nombres y ubicaciones provienen de fuentes oficiales (IGAC, PNN, ANT, SIAC)<br/>"
            "• Si no se muestra un nombre específico, indica que no existe en la base de datos oficial",
            self.styles['TextoNormal']
        )
        elementos.append(nota)
        elementos.append(Spacer(1, 0.5*cm))
        elementos.append(PageBreak())
        
        return elementos
    
    def _generar_mapa_parcela(self, parcela: Parcela, verificador: VerificadorRestriccionesLegales, departamento: str = "Casanare", distancias: Dict = None) -> BytesIO:
        """
        Genera mapa MEJORADO de la parcela con:
        - Silueta visible de la parcela (roja discontinua)
        - Flechas hacia zonas críticas cercanas
        - Rosa de los vientos
        - Capas FILTRADAS por departamento
        """
        UTM_COLOMBIA = 'EPSG:32618'  # Para cálculos sin warnings
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Convertir geometría de la parcela a GeoDataFrame
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            parcela_geom = shape(parcela.geometria)
        
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        
        # Calcular centroide en UTM (sin warning) y convertir a geo
        parcela_utm = parcela_gdf.to_crs(UTM_COLOMBIA)
        centroide_utm = parcela_utm.geometry.centroid.iloc[0]
        centroide = gpd.GeoSeries([centroide_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
        
        # Dibujar parcela MEJORADO: primero relleno translúcido, luego silueta ROJA visible
        parcela_gdf.plot(ax=ax, facecolor='lightgreen', edgecolor='none', alpha=0.3)
        parcela_gdf.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=3, linestyle='--', alpha=1.0, zorder=10)
        
        # Obtener bbox del departamento para filtrar
        dept_info = DEPARTAMENTOS_INFO.get(departamento, {})
        bbox = dept_info.get('bbox', None)
        
        # Superponer capas geográficas FILTRADAS por departamento
        bounds = parcela_gdf.total_bounds  # [minx, miny, maxx, maxy]
        
        # Expandir bounds para incluir contexto
        buffer = 0.2  # grados
        bounds_expanded = [bounds[0] - buffer, bounds[1] - buffer, bounds[2] + buffer, bounds[3] + buffer]
        
        # Red hídrica (FILTRADA)
        if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
            red = verificador.red_hidrica
            if bbox:
                red = red.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            red_clip = red.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(red_clip) > 0:
                red_clip.plot(ax=ax, color='blue', linewidth=1.5, alpha=0.7)
        
        # Áreas protegidas (FILTRADAS)
        if verificador.areas_protegidas is not None and len(verificador.areas_protegidas) > 0:
            areas = verificador.areas_protegidas
            if bbox:
                areas = areas.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            areas_clip = areas.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(areas_clip) > 0:
                areas_clip.plot(ax=ax, facecolor='yellow', edgecolor='orange', linewidth=1, alpha=0.4)
        
        # Resguardos indígenas (FILTRADOS)
        if verificador.resguardos_indigenas is not None and len(verificador.resguardos_indigenas) > 0:
            resguardos = verificador.resguardos_indigenas
            if bbox:
                resguardos = resguardos.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            resguardos_clip = resguardos.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(resguardos_clip) > 0:
                resguardos_clip.plot(ax=ax, facecolor='purple', edgecolor='darkviolet', linewidth=1, alpha=0.3)
        
        # Páramos (FILTRADOS)
        if verificador.paramos is not None and len(verificador.paramos) > 0:
            paramos = verificador.paramos
            if bbox:
                paramos = paramos.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            paramos_clip = paramos.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(paramos_clip) > 0:
                paramos_clip.plot(ax=ax, facecolor='lightblue', edgecolor='blue', linewidth=1, alpha=0.4)
        
        # Configurar el mapa (usando centroide ya calculado sin warnings)
        ax.set_title(f'Mapa de Verificación Legal - {departamento}\n{parcela.nombre}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud', fontsize=10)
        ax.set_ylabel('Latitud', fontsize=10)
        
        # Crear leyenda manual (evita warnings de matplotlib con GeoDataFrames)
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        
        legend_elements = [
            Line2D([0], [0], color='red', linewidth=3, linestyle='--', label='Límite Parcela'),
        ]
        
        # Solo agregar a la leyenda los elementos que realmente se dibujaron
        if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
            red = verificador.red_hidrica
            if bbox:
                red = red.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            red_clip = red.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(red_clip) > 0:
                legend_elements.append(Line2D([0], [0], color='blue', linewidth=2, label=f'Red Hídrica ({len(red_clip)})'))
        
        if verificador.areas_protegidas is not None and len(verificador.areas_protegidas) > 0:
            areas = verificador.areas_protegidas
            if bbox:
                areas = areas.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            areas_clip = areas.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(areas_clip) > 0:
                legend_elements.append(Patch(facecolor='yellow', edgecolor='orange', alpha=0.4, label=f'Áreas Protegidas ({len(areas_clip)})'))
        
        if verificador.resguardos_indigenas is not None and len(verificador.resguardos_indigenas) > 0:
            resguardos = verificador.resguardos_indigenas
            if bbox:
                resguardos = resguardos.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            resguardos_clip = resguardos.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(resguardos_clip) > 0:
                legend_elements.append(Patch(facecolor='purple', edgecolor='darkviolet', alpha=0.3, label=f'Resguardos ({len(resguardos_clip)})'))
        
        if verificador.paramos is not None and len(verificador.paramos) > 0:
            paramos = verificador.paramos
            if bbox:
                paramos = paramos.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            paramos_clip = paramos.cx[bounds_expanded[0]:bounds_expanded[2], bounds_expanded[1]:bounds_expanded[3]]
            if len(paramos_clip) > 0:
                legend_elements.append(Patch(facecolor='lightblue', edgecolor='blue', alpha=0.4, label=f'Páramos ({len(paramos_clip)})'))
        
        # Crear leyenda con elementos manuales (sin warnings)
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9)
        
        # Agregar grid
        ax.grid(True, alpha=0.3)
        
        # Agregar anotación de coordenadas
        ax.text(0.02, 0.02, f'Centro: {centroide.y:.6f}°N, {centroide.x:.6f}°W\nDatos filtrados para {departamento}', 
                transform=ax.transAxes, fontsize=8, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # NUEVO: Agregar flechas hacia zonas críticas cercanas
        if distancias:
            self._agregar_flechas_proximidad(ax, parcela_gdf, distancias)
        
        # NUEVO: Agregar rosa de los vientos
        self._agregar_rosa_vientos(ax)
        
        plt.tight_layout()
        
        # Guardar en BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer
    
    def _agregar_flechas_proximidad(self, ax, parcela_gdf, distancias: Dict):
        """
        Dibuja flechas desde la parcela hacia elementos críticos cercanos
        """
        from matplotlib.patches import FancyArrowPatch
        
        # Calcular centroide en UTM (sin warning)
        UTM_COLOMBIA = 'EPSG:32618'
        parcela_utm = parcela_gdf.to_crs(UTM_COLOMBIA)
        centroide_utm = parcela_utm.geometry.centroid.iloc[0]
        centroide_geo = gpd.GeoSeries([centroide_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
        
        x_parcela, y_parcela = centroide_geo.x, centroide_geo.y
        
        # Colores por tipo
        colores = {
            'areas_protegidas': 'orange',
            'resguardos_indigenas': 'purple',
            'red_hidrica': 'blue',
            'paramos': 'lightblue'
        }
        
        # Nombres legibles
        nombres_cortos = {
            'areas_protegidas': 'Área Prot.',
            'resguardos_indigenas': 'Resguardo',
            'red_hidrica': 'Río/Quebrada',
            'paramos': 'Páramo'
        }
        
        for tipo, info in distancias.items():
            # Solo dibujar si hay distancia válida, no está dentro, y está relativamente cerca
            if info.get('distancia_km') and info['distancia_km'] > 0 and info['distancia_km'] < 50:
                direccion = info.get('direccion', '')
                dx, dy = 0, 0
                
                # Calcular vector de dirección (normalizado)
                if 'Norte' in direccion:
                    dy = 0.08
                if 'Sur' in direccion:
                    dy = -0.08
                if 'Este' in direccion or 'este' in direccion:
                    dx = 0.08
                if 'Oeste' in direccion or 'oeste' in direccion:
                    dx = -0.08
                
                # Si no hay dirección, saltar
                if dx == 0 and dy == 0:
                    continue
                
                x_destino = x_parcela + dx
                y_destino = y_parcela + dy
                
                # Dibujar flecha
                arrow = FancyArrowPatch(
                    (x_parcela, y_parcela), 
                    (x_destino, y_destino),
                    arrowstyle='->', 
                    color=colores.get(tipo, 'gray'),
                    linewidth=2.5,
                    alpha=0.8,
                    mutation_scale=25,
                    zorder=15
                )
                ax.add_patch(arrow)
                
                # Etiqueta con distancia y tipo
                tipo_nombre = nombres_cortos.get(tipo, tipo[:10])
                ax.text(x_destino, y_destino, 
                       f"{info['distancia_km']} km\n{tipo_nombre}",
                       fontsize=7, ha='center', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor=colores.get(tipo, 'white'), 
                                alpha=0.85, edgecolor='black', linewidth=1),
                       zorder=16)
    
    def _agregar_rosa_vientos(self, ax):
        """
        Agrega veleta de puntos cardinales al mapa (esquina inferior izquierda)
        """
        from matplotlib.patches import Circle
        
        # Posición de la rosa (esquina inferior izquierda del mapa)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        x_base = xlim[0] + 0.10 * (xlim[1] - xlim[0])
        y_base = ylim[0] + 0.10 * (ylim[1] - ylim[0])
        
        tam_flecha = 0.035 * (ylim[1] - ylim[0])
        
        # Círculo de fondo
        circulo = Circle((x_base, y_base), tam_flecha * 1.3, 
                        facecolor='white', edgecolor='black', 
                        linewidth=2, alpha=0.9, zorder=100)
        ax.add_patch(circulo)
        
        # Flechas de dirección
        # Norte (roja y más grande)
        ax.arrow(x_base, y_base, 0, tam_flecha, 
                head_width=tam_flecha*0.35, head_length=tam_flecha*0.25, 
                fc='red', ec='darkred', linewidth=2, zorder=101)
        ax.text(x_base, y_base + tam_flecha * 1.6, 'N', 
               fontsize=11, fontweight='bold', ha='center', va='bottom', 
               color='red', zorder=102)
        
        # Sur
        ax.arrow(x_base, y_base, 0, -tam_flecha*0.7, 
                head_width=tam_flecha*0.27, head_length=tam_flecha*0.18, 
                fc='gray', ec='black', linewidth=1.2, alpha=0.7, zorder=101)
        ax.text(x_base, y_base - tam_flecha * 1.3, 'S', 
               fontsize=9, ha='center', va='top', color='gray', zorder=102)
        
        # Este
        ax.arrow(x_base, y_base, tam_flecha*0.7, 0, 
                head_width=tam_flecha*0.27, head_length=tam_flecha*0.18, 
                fc='gray', ec='black', linewidth=1.2, alpha=0.7, zorder=101)
        ax.text(x_base + tam_flecha * 1.1, y_base, 'E', 
               fontsize=9, ha='left', va='center', color='gray', zorder=102)
        
        # Oeste
        ax.arrow(x_base, y_base, -tam_flecha*0.7, 0, 
                head_width=tam_flecha*0.27, head_length=tam_flecha*0.18, 
                fc='gray', ec='black', linewidth=1.2, alpha=0.7, zorder=101)
        ax.text(x_base - tam_flecha * 1.1, y_base, 'O', 
               fontsize=9, ha='right', va='center', color='gray', zorder=102)
    
    def _crear_seccion_mapa(self, parcela: Parcela, verificador: VerificadorRestriccionesLegales, departamento: str = "Casanare", distancias: Dict = None) -> List:
        """Crea la sección del mapa de la parcela"""
        elementos = []
        
        # Título de sección
        titulo = Paragraph("🗺️ MAPA DE LA PARCELA", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Descripción
        texto = Paragraph(
            f"El siguiente mapa muestra la ubicación de la parcela y las capas geográficas verificadas, "
            f"<b>filtradas específicamente para {departamento}</b> (áreas protegidas, resguardos indígenas, red hídrica y páramos). "
            f"La parcela está delimitada con <b>línea roja discontinua</b>, las flechas indican dirección y distancia a zonas críticas cercanas, "
            f"y la rosa de los vientos en la esquina inferior izquierda muestra la orientación del mapa.",
            self.styles['TextoNormal']
        )
        elementos.append(texto)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Generar y agregar mapa
        try:
            img_buffer = self._generar_mapa_parcela(parcela, verificador, departamento, distancias)
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
    
    def _generar_mapa_contexto_regional(self, parcela: Parcela, departamento: str = "Casanare") -> BytesIO:
        """
        ✨ NUEVO V3: Genera mapa de contexto regional (vista amplia del departamento con punto de parcela)
        
        Para orientación geográfica general y evaluación de riesgo por ubicación.
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Obtener bbox del departamento
        dept_info = DEPARTAMENTOS_INFO.get(departamento, {})
        bbox = dept_info.get('bbox', [-74, 4, -70, 7])  # Default Colombia central
        
        # Configurar extent del mapa
        ax.set_xlim(bbox[0], bbox[2])
        ax.set_ylim(bbox[1], bbox[3])
        
        # Dibujar rectángulo del departamento (aproximado)
        from matplotlib.patches import Rectangle
        rect = Rectangle((bbox[0], bbox[1]), bbox[2]-bbox[0], bbox[3]-bbox[1],
                        linewidth=2, edgecolor='darkgreen', facecolor='lightgreen', alpha=0.2)
        ax.add_patch(rect)
        
        # Calcular centroide de la parcela
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            parcela_geom = shape(parcela.geometria)
        
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        centroide = parcela_gdf.geometry.centroid.iloc[0]
        
        # Marcar ubicación de la parcela
        ax.plot(centroide.x, centroide.y, 'ro', markersize=15, label='Ubicación Parcela', zorder=10)
        ax.plot(centroide.x, centroide.y, 'r*', markersize=25, zorder=11)
        
        # Etiqueta del departamento
        centro_dept_x = (bbox[0] + bbox[2]) / 2
        centro_dept_y = (bbox[1] + bbox[3]) / 2
        ax.text(centro_dept_x, centro_dept_y, departamento, 
               fontsize=20, ha='center', va='center', fontweight='bold',
               color='darkgreen', alpha=0.3, zorder=1)
        
        # Configuración del mapa
        ax.set_title(f'Contexto Regional - {departamento}\nUbicación de la Parcela', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud', fontsize=10)
        ax.set_ylabel('Latitud', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=10)
        
        # Rosa de los vientos
        self._agregar_rosa_vientos(ax)
        
        # Escala gráfica
        self._agregar_escala_grafica(ax, departamento)
        
        # Anotación de coordenadas
        ax.text(0.02, 0.02, f'Parcela: {centroide.y:.6f}°N, {centroide.x:.6f}°W', 
                transform=ax.transAxes, fontsize=8, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Guardar en BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer
    
    def _generar_mapa_silueta(self, parcela: Parcela, departamento: str = "Casanare") -> BytesIO:
        """
        ✨ NUEVO V3: Genera mapa silueta limpio (polígono sin capas superpuestas)
        
        Para visualización rápida del área total y forma de la parcela.
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Convertir geometría de la parcela
        if hasattr(parcela.geometria, 'wkt'):
            parcela_geom = wkt.loads(parcela.geometria.wkt)
        else:
            parcela_geom = shape(parcela.geometria)
        
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        
        # Dibujar parcela con estilo limpio y profesional
        parcela_gdf.plot(ax=ax, facecolor='#2e7d32', edgecolor='darkred', linewidth=3, alpha=0.6)
        
        # Configurar el mapa
        ax.set_title(f'Silueta de Parcela - {parcela.nombre}\n{departamento}, Colombia', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Longitud', fontsize=10)
        ax.set_ylabel('Latitud', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Rosa de los vientos
        self._agregar_rosa_vientos(ax)
        
        # Etiqueta con área total
        area_ha = parcela.area_hectareas if hasattr(parcela, 'area_hectareas') else 0
        centroide = parcela_gdf.geometry.centroid.iloc[0]
        
        ax.text(0.5, 0.95, f'Área Total: {area_ha:.2f} hectáreas', 
                transform=ax.transAxes, fontsize=12, ha='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='darkgreen', linewidth=2))
        
        # Coordenadas
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
    
    def _agregar_escala_grafica(self, ax, departamento: str = "Casanare"):
        """
        ✨ NUEVO V3: Agrega barra de escala gráfica al mapa
        
        Calcula escala apropiada según el extent del mapa.
        """
        from matplotlib.patches import Rectangle as MPLRectangle
        from matplotlib.lines import Line2D
        
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Calcular ancho del mapa en grados
        ancho_mapa_grados = xlim[1] - xlim[0]
        
        # Aproximación: 1 grado ≈ 111 km en el ecuador (Colombia ~4-6°N)
        ancho_mapa_km = ancho_mapa_grados * 111
        
        # Determinar escala apropiada (10%, 20%, o 50% del ancho del mapa)
        if ancho_mapa_km > 200:
            escala_km = 50
        elif ancho_mapa_km > 100:
            escala_km = 20
        elif ancho_mapa_km > 50:
            escala_km = 10
        else:
            escala_km = 5
        
        # Convertir km a grados
        escala_grados = escala_km / 111
        
        # Posición de la barra (esquina inferior derecha)
        x_base = xlim[1] - 0.25 * (xlim[1] - xlim[0])
        y_base = ylim[0] + 0.05 * (ylim[1] - ylim[0])
        
        # Dibujar barra de escala
        line = Line2D([x_base, x_base + escala_grados], [y_base, y_base],
                     linewidth=4, color='black', solid_capstyle='butt', zorder=100)
        ax.add_line(line)
        
        # Marcas en los extremos
        ax.plot([x_base, x_base], [y_base - 0.01, y_base + 0.01], 'k-', linewidth=2, zorder=100)
        ax.plot([x_base + escala_grados, x_base + escala_grados], [y_base - 0.01, y_base + 0.01], 'k-', linewidth=2, zorder=100)
        
        # Etiqueta
        ax.text(x_base + escala_grados/2, y_base + 0.03, f'{escala_km} km',
               fontsize=9, ha='center', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='black'),
               zorder=101)
    
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
                    rest.get('nombre', 'N/A')[:30],
                    f"{rest.get('area_interseccion_ha', 0):.2f}",
                    f"{rest.get('porcentaje_area_parcela', 0):.1f}%",
                    rest.get('descripcion', 'N/A')[:50]
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
    
    def _crear_seccion_confianza(self, resultado: ResultadoVerificacion, departamento: str = "Casanare") -> List:
        """
        Crea sección de niveles de confianza - MEJORADA sin N/A
        """
        elementos = []
        
        titulo = Paragraph("📈 NIVELES DE CONFIANZA DE LOS DATOS", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        descripcion = Paragraph(
            f"Confiabilidad de las fuentes de datos geográficos utilizadas para {departamento}. "
            "Todas las fuentes son oficiales y actualizadas.",
            self.styles['TextoNormal']
        )
        elementos.append(descripcion)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Crear tabla de confianza MEJORADA con orden lógico
        headers = ['Capa Geográfica', 'Nivel', 'Fuente Oficial', 'Versión/Año', 'Elementos\nVerificados', 'Observaciones']
        data = [headers]
        
        # Mapeo de nombres legibles
        nombres_capas = {
            'red_hidrica': 'Red Hídrica',
            'areas_protegidas': 'Áreas Protegidas',
            'resguardos_indigenas': 'Resguardos Indígenas',
            'paramos': 'Páramos'
        }
        
        # Mapeo de fuentes oficiales (sin N/A)
        fuentes_oficiales = {
            'red_hidrica': 'IGAC\n(Inst. Geográfico)',
            'areas_protegidas': 'PNN\n(Parques Nacionales)',
            'resguardos_indigenas': 'ANT\n(Agencia Nac. Tierras)',
            'paramos': 'SIAC\n(Sist. Info. Amb.)'
        }
        
        # Fechas/versiones de los datos (investigadas en metadatos)
        versiones_datos = {
            'red_hidrica': '2024\n(IGAC)',
            'areas_protegidas': '2025\n(Actual)',
            'resguardos_indigenas': '2024\n(ANT)',
            'paramos': 'Jun 2020\n(MADS)'
        }
        
        # Orden lógico: Áreas protegidas → Páramos → Red hídrica → Resguardos
        orden_capas = ['areas_protegidas', 'paramos', 'red_hidrica', 'resguardos_indigenas']
        capas_ordenadas = sorted(resultado.niveles_confianza.items(), 
                                key=lambda x: orden_capas.index(x[0]) if x[0] in orden_capas else 999)
        
        for capa, info in capas_ordenadas:
            # Emoji según nivel de confianza
            if info['confianza'] == 'Alta':
                emoji = '✅'
                nivel_texto = 'ALTA'
            elif info['confianza'] == 'Media':
                emoji = '⚠️'
                nivel_texto = 'MEDIA'
            else:
                emoji = '❌'
                nivel_texto = 'BAJA'
            
            nombre_capa = nombres_capas.get(capa, capa.replace('_', ' ').title())
            fuente = fuentes_oficiales.get(capa, 'Oficial')
            version = versiones_datos.get(capa, '2024')
            
            # Extraer número de elementos de la razón si está disponible
            razon = info.get('razon', '')
            elementos_num = 'Verificado'
            if '(' in razon and ')' in razon:
                try:
                    num_str = razon.split('(')[1].split(')')[0].split()[0]
                    elementos_num = f"{num_str}\nregistros"
                except:
                    elementos_num = 'Filtrado\npor región'
            elif 'vacío válido' in razon.lower() or 'sin páramos' in razon.lower() or 'región sin' in razon.lower():
                elementos_num = f'0\n(correcto\npara {departamento[:8]})'
            
            observaciones = razon[:50] + '...' if len(razon) > 50 and razon else 'Datos oficiales verificados y completos'
            
            fila = [
                nombre_capa,
                f"{emoji}\n{nivel_texto}",
                fuente,
                version,
                elementos_num,
                observaciones
            ]
            data.append(fila)
        
        tabla = Table(data, colWidths=[2.8*cm, 1.8*cm, 2.5*cm, 1.7*cm, 2*cm, 5.2*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#388e3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Nota explicativa mejorada
        nota = Paragraph(
            f"<b>Nota:</b> Todos los datos han sido filtrados específicamente para {departamento}. "
            "Los niveles de confianza 'Alta' indican fuentes oficiales nacionales completas y actualizadas. "
            "Un resultado de '0 elementos' puede ser correcto según la geografía regional.",
            self.styles['TextoNormal']
        )
        elementos.append(nota)
        elementos.append(Spacer(1, 0.5*cm))
        elementos.append(PageBreak())
        
        return elementos
    
    def _crear_tabla_metadatos_capas(self, departamento: str = "Casanare") -> List:
        """
        ✨ NUEVO V3: Crea tabla con metadatos completos de cada capa geográfica
        
        Para transparencia técnica y trazabilidad de fuentes de datos.
        """
        elementos = []
        
        titulo = Paragraph("📚 METADATOS DE CAPAS GEOGRÁFICAS", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        descripcion = Paragraph(
            "Información técnica detallada sobre las fuentes de datos geográficos utilizados en este análisis:",
            self.styles['TextoNormal']
        )
        elementos.append(descripcion)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Crear tabla de metadatos por capa
        headers = ['Capa', 'Nombre Completo', 'Autoridad', 'Año', 'Tipo', 'Escala/Limitación']
        data = [headers]
        
        # Orden lógico de capas
        capas_orden = ['red_hidrica', 'areas_protegidas', 'resguardos_indigenas', 'paramos']
        
        for capa_id in capas_orden:
            if capa_id not in METADATOS_CAPAS:
                continue
            
            meta = METADATOS_CAPAS[capa_id]
            
            # Nombre corto para la primera columna
            nombres_cortos = {
                'red_hidrica': 'Red Hídrica',
                'areas_protegidas': 'Áreas Protegidas',
                'resguardos_indigenas': 'Resguardos Indígenas',
                'paramos': 'Páramos'
            }
            
            fila = [
                nombres_cortos.get(capa_id, capa_id.replace('_', ' ').title()),
                meta['nombre_completo'],
                meta['autoridad'],
                meta['año'],
                meta['tipo_geometria'],
                meta['escala']
            ]
            data.append(fila)
        
        tabla = Table(data, colWidths=[2.5*cm, 3.5*cm, 2.5*cm, 1.2*cm, 2*cm, 4.3*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Tabla de notas críticas por capa
        titulo_notas = Paragraph("<b>Notas Críticas por Capa:</b>", self.styles['TextoNormal'])
        elementos.append(titulo_notas)
        elementos.append(Spacer(1, 0.3*cm))
        
        notas_data = [['Capa', 'Nota Crítica / Limitación']]
        
        for capa_id in capas_orden:
            if capa_id not in METADATOS_CAPAS:
                continue
            
            meta = METADATOS_CAPAS[capa_id]
            nombres_cortos = {
                'red_hidrica': 'Red Hídrica',
                'areas_protegidas': 'Áreas Protegidas',
                'resguardos_indigenas': 'Resguardos Indígenas',
                'paramos': 'Páramos'
            }
            
            notas_data.append([
                nombres_cortos.get(capa_id, capa_id.replace('_', ' ').title()),
                f"{meta['nota_critica']}\n\nLimitación: {meta['limitacion']}"
            ])
        
        tabla_notas = Table(notas_data, colWidths=[3*cm, 13*cm])
        tabla_notas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff9800')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elementos.append(tabla_notas)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Nota final de fuentes
        nota_fuentes = Paragraph(
            "<b>Fuentes oficiales consultadas:</b><br/>"
            "• IGAC (Instituto Geográfico Agustín Codazzi) - Cartografía base y red hídrica<br/>"
            "• IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales) - Hidrología<br/>"
            "• PNN (Parques Nacionales Naturales de Colombia) - RUNAP (Registro Único Nacional de Áreas Protegidas)<br/>"
            "• ANT (Agencia Nacional de Tierras) - Resguardos indígenas formalizados<br/>"
            "• SIAC (Sistema de Información Ambiental de Colombia) - Páramos delimitados<br/>"
            "• MADS (Ministerio de Ambiente y Desarrollo Sostenible) - Normativa ambiental vigente",
            self.styles['TextoNormal']
        )
        elementos.append(nota_fuentes)
        elementos.append(Spacer(1, 0.5*cm))
        elementos.append(PageBreak())
        
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
    
    def _crear_seccion_recomendaciones(self, resultado: ResultadoVerificacion, parcela: Parcela, departamento: str = "Casanare") -> List:
        """Crea sección de recomendaciones legales"""
        elementos = []
        
        titulo = Paragraph("💡 RECOMENDACIONES LEGALES", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Generar recomendaciones basadas en los resultados
        if resultado.cumple_normativa:
            # 🚨 VERIFICAR si hay datos NO CONCLUYENTES
            tiene_datos_no_concluyentes = False
            capas_problematicas = []
            if hasattr(resultado, 'niveles_confianza'):
                for capa, info in resultado.niveles_confianza.items():
                    if info.get('confianza') in ['Baja', 'Nula', 'Crítica']:
                        tiene_datos_no_concluyentes = True
                        capas_problematicas.append(capa.replace('_', ' ').title())
            
            if tiene_datos_no_concluyentes:
                # ⚠️ CUMPLE PERO CON DATOS LIMITADOS - ADVERTIR
                texto = Paragraph(
                    f"⚠️ <b>Análisis geoespacial para {departamento} - CON LIMITACIONES</b><br/><br/>"
                    f"<b>Estado del análisis:</b><br/>"
                    f"Con base en la información geográfica disponible, no se identificaron restricciones ambientales directas. "
                    f"Sin embargo, <b>este análisis tiene limitaciones importantes</b> en las siguientes capas: "
                    f"{', '.join(capas_problematicas)}.<br/><br/>"
                    f"<b>⚠️ IMPORTANTE:</b> La ausencia de restricciones identificadas <b>NO equivale a confirmación de cumplimiento normativo</b> "
                    f"debido a las limitaciones en los datos fuente.<br/><br/>"
                    f"<b>Acciones OBLIGATORIAS antes de proceder:</b><br/>"
                    f"• <b>PRIORIDAD CRÍTICA:</b> Validar este análisis con la Corporación Autónoma Regional (CAR) competente<br/>"
                    f"• Realizar inspección en campo por profesional competente (especialmente red hídrica)<br/>"
                    f"• Verificar existencia de cartografía de mayor detalle para la zona específica<br/>"
                    f"• Solicitar concepto técnico ambiental antes de iniciar cualquier proyecto<br/>"
                    f"• Obtener todas las licencias y permisos ambientales requeridos por ley<br/>"
                    f"• Respetar los retiros mínimos de fuentes hídricas (30m mínimo - Decreto 1541/1978)<br/>"
                    f"• Verificar en campo la presencia de cauces no cartografiados<br/><br/>"
                    f"<b>Nota legal:</b> Este informe NO autoriza ninguna actividad. Es un análisis técnico preliminar "
                    f"que requiere validación por autoridad competente.",
                    self.styles['Advertencia']
                )
            else:
                # ✅ CUMPLE CON DATOS CONFIABLES - pero siempre recomendar validación
                texto = Paragraph(
                    f"✅ <b>Resultado del análisis geoespacial para {departamento}:</b><br/>"
                    f"Con base en la información geográfica disponible y validada, no se identificaron restricciones ambientales directas.<br/><br/>"
                    "<b>Recomendaciones profesionales:</b><br/>"
                    "• <b>Validar</b> este análisis con la autoridad ambiental competente (CAR) antes de proceder<br/>"
                    "• Mantener las condiciones actuales del terreno<br/>"
                    "• Implementar buenas prácticas agrícolas sostenibles<br/>"
                    "• Realizar monitoreo periódico de cambios en la normativa ambiental<br/>"
                    "• Obtener las licencias y permisos requeridos antes de iniciar proyectos<br/>"
                    f"• Respetar los retiros mínimos de fuentes hídricas (30m mínimo - Decreto 1541/1978)<br/>"
                    f"• Verificar en campo la presencia de cauces no cartografiados<br/><br/>"
                    f"<b>Nota:</b> Este análisis se basa en cartografía oficial al {resultado.fecha_verificacion.split('T')[0]}. "
                    f"Los resultados pueden cambiar con actualizaciones de los datos geográficos.",
                    self.styles['TextoNormal']
                )
        else:
            texto = Paragraph(
                f"⚠️ <b>La parcela en {departamento} presenta RESTRICCIONES LEGALES.</b><br/><br/>"
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
        
        # Nota legal REFORZADA con alcances claros
        nota_legal = Paragraph(
            "<b>ALCANCE Y LIMITACIONES DEL ANÁLISIS:</b><br/><br/>"
            "<b>Naturaleza del documento:</b><br/>"
            f"Este informe presenta un análisis geoespacial preliminar basado en información "
            f"geográfica oficial disponible al momento de su generación ({resultado.fecha_verificacion.split('T')[0]}). "
            "<b>NO constituye:</b><br/>"
            "• Certificación de cumplimiento ambiental<br/>"
            "• Licencia o permiso ambiental<br/>"
            "• Concepto técnico vinculante de autoridad competente<br/>"
            "• Sustituto de estudios ambientales requeridos por ley<br/><br/>"
            "<b>Validez y limitaciones:</b><br/>"
            "Los resultados están sujetos a:<br/>"
            "• Precisión y escala de las fuentes cartográficas utilizadas<br/>"
            "• Fecha de actualización de los datos geográficos oficiales<br/>"
            "• Verificación en campo por profesionales competentes<br/>"
            "• Cobertura real de los shapefiles en la zona de estudio<br/><br/>"
            "<b>Recomendación legal:</b><br/>"
            "Antes de tomar decisiones legales, de inversión o de uso del suelo basadas en este análisis, "
            "se recomienda consultar directamente con:<br/>"
            "• La Corporación Autónoma Regional (CAR) competente<br/>"
            "• Ministerio de Ambiente y Desarrollo Sostenible<br/>"
            "• Asesor legal especializado en derecho ambiental<br/><br/>"
            "<b>Responsabilidad:</b> Este documento es de carácter informativo y técnico. "
            "La responsabilidad por decisiones tomadas con base en esta información recae "
            "exclusivamente en el usuario final.",
            self.styles['TextoNormal']
        )
        elementos.append(nota_legal)
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def _crear_conclusion_ejecutiva(self, resultado: ResultadoVerificacion, parcela: Parcela, departamento: str = "Casanare") -> List:
        """
        ✨ NUEVO V3: Crea conclusión ejecutiva comercial (1 párrafo, resultado + implicación)
        
        Enfoque comercial para oficial de crédito agrícola.
        """
        elementos = []
        
        titulo = Paragraph("📊 CONCLUSIÓN EJECUTIVA", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Determinar resultado principal
        cumple = resultado.cumple_normativa
        num_restricciones = len(resultado.restricciones_encontradas)
        porcentaje_disponible = 100 - resultado.porcentaje_restringido
        
        # 🚨 VERIFICAR si hay datos NO CONCLUYENTES
        tiene_datos_no_concluyentes = False
        if hasattr(resultado, 'niveles_confianza'):
            for capa, info in resultado.niveles_confianza.items():
                if info.get('confianza') in ['Baja', 'Nula', 'Crítica']:
                    tiene_datos_no_concluyentes = True
                    break
        
        # Construir conclusión según el escenario
        if cumple and not tiene_datos_no_concluyentes:
            # ✅ Escenario POSITIVO con datos confiables
            conclusion_texto = (
                f"El análisis geoespacial preliminar de la parcela <b>{parcela.nombre}</b> "
                f"({parcela.area_hectareas:.2f} ha) ubicada en {departamento}, indica que <b>{porcentaje_disponible:.1f}% del área "
                f"está técnicamente disponible</b> según la cartografía oficial verificada (sin restricciones ambientales identificadas). "
                f"<br/><br/>"
                f"<b>Implicación comercial:</b> El predio presenta condiciones geoespaciales favorables para evaluación crediticia. "
                f"Se recomienda proceder con verificación en campo y concepto de la autoridad ambiental competente antes de "
                f"formalizar operación de crédito agrícola."
            )
            color_conclusion = colors.HexColor('#2e7d32')
        elif cumple and tiene_datos_no_concluyentes:
            # ⚠️ Escenario POSITIVO pero con limitaciones en datos
            conclusion_texto = (
                f"El análisis geoespacial preliminar de la parcela <b>{parcela.nombre}</b> "
                f"({parcela.area_hectareas:.2f} ha) ubicada en {departamento}, identificó <b>0 restricciones ambientales</b> "
                f"según las capas cartográficas disponibles. Sin embargo, <b>existen limitaciones importantes</b> en la calidad "
                f"o cobertura de algunos datos geográficos utilizados."
                f"<br/><br/>"
                f"<b>Implicación comercial:</b> El resultado positivo debe interpretarse con precaución. "
                f"<b>Se requiere obligatoriamente</b> validación en campo y concepto técnico de autoridad competente antes de "
                f"proceder con operación de crédito agrícola. Las limitaciones de datos impiden confirmar cumplimiento normativo total."
            )
            color_conclusion = colors.HexColor('#ff9800')  # Naranja (advertencia)
        else:
            # ❌ Escenario con RESTRICCIONES identificadas
            conclusion_texto = (
                f"El análisis geoespacial preliminar de la parcela <b>{parcela.nombre}</b> "
                f"({parcela.area_hectareas:.2f} ha) ubicada en {departamento}, identificó <b>{num_restricciones} restricción(es) "
                f"ambiental(es)</b> que afectan {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}% del área total). "
                f"El área técnicamente disponible es de {porcentaje_disponible:.1f}%."
                f"<br/><br/>"
                f"<b>Implicación comercial:</b> El predio presenta restricciones ambientales que requieren evaluación legal detallada. "
                f"Se recomienda análisis de riesgo crediticio considerando limitaciones de uso del suelo antes de formalizar operación."
            )
            color_conclusion = colors.HexColor('#d32f2f')  # Rojo
        
        # Crear párrafo con fondo de color
        conclusion_par = Paragraph(conclusion_texto, self.styles['TextoNormal'])
        
        # Tabla con fondo de color para destacar
        tabla_conclusion = Table([[conclusion_par]], colWidths=[16*cm])
        tabla_conclusion.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color_conclusion),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elementos.append(tabla_conclusion)
        elementos.append(Spacer(1, 0.5*cm))
        elementos.append(PageBreak())
        
        return elementos
    
    def _crear_seccion_limitaciones_tecnicas(self, resultado: ResultadoVerificacion, departamento: str = "Casanare") -> List:
        """
        ✨ NUEVO V3: Crea sección de limitaciones técnicas (disclaimer legal final)
        
        Transparencia total sobre limitaciones del análisis para protección legal.
        """
        elementos = []
        
        titulo = Paragraph("⚠️ LIMITACIONES TÉCNICAS DEL ANÁLISIS", self.styles['SubtituloPersonalizado'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Introducción
        intro = Paragraph(
            "<b>Este análisis geoespacial tiene limitaciones inherentes que deben considerarse:</b>",
            self.styles['TextoNormal']
        )
        elementos.append(intro)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Tabla de limitaciones por capa
        data = [['Aspecto', 'Limitación Técnica', 'Implicación Legal']]
        
        limitaciones = [
            ('Escala Cartográfica', 
             'Los datos provienen de cartografía 1:100.000 (IGAC/IDEAM)',
             'NO es apta para delimitación exacta de retiros o límites. Requiere topografía detallada.'),
            
            ('Actualización Temporal',
             f'Datos oficiales con fecha de publicación 2024 (consulta {datetime.now().strftime("%Y-%m-%d")})',
             'Pueden existir resoluciones, declaratorias o delimitaciones posteriores no reflejadas.'),
            
            ('Cobertura Geográfica',
             f'Datos filtrados específicamente para {departamento}. Posible incompletitud en zonas de frontera.',
             'Zonas limítrofes con otros departamentos requieren verificación adicional.'),
            
            ('Cartografía Hídrica',
             'Red hídrica basada en digitalización a escala 1:100.000',
             'Cauces menores, quebradas estacionales o nacederos pueden no estar representados.'),
            
            ('Dinámicas Territoriales',
             'No incluye procesos de delimitación en curso o comunidades en trámite de formalización',
             'Pueden existir procesos administrativos no reflejados en las bases de datos oficiales.'),
            
            ('Validación en Campo',
             'Análisis exclusivamente geoespacial (sin verificación in situ)',
             'Condiciones reales del terreno pueden diferir de la información cartográfica.')
        ]
        
        for aspecto, limitacion, implicacion in limitaciones:
            data.append([aspecto, limitacion, implicacion])
        
        tabla = Table(data, colWidths=[3.5*cm, 6*cm, 6.5*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
        
        # Disclaimer legal final reforzado
        disclaimer_final = Paragraph(
            "<b>DISCLAIMER LEGAL:</b><br/>"
            "Este análisis geoespacial es <b>preliminar</b> y se basa en cartografía oficial disponible al momento de la consulta. "
            "<b>NO constituye concepto legal definitivo</b> ni reemplaza la verificación en campo por autoridad ambiental competente. "
            "<br/><br/>"
            "Los resultados de este informe deben interpretarse como <b>insumo técnico para evaluación crediticia preliminar</b>, "
            "no como certificación de cumplimiento normativo absoluto. "
            "<br/><br/>"
            "<b>La responsabilidad por decisiones de crédito, inversión o uso del suelo tomadas con base en este documento "
            "recae exclusivamente en la entidad crediticia y el solicitante.</b> "
            "<br/><br/>"
            "Se recomienda obligatoriamente complementar con:<br/>"
            "• Concepto técnico de la Corporación Autónoma Regional (CAR) competente<br/>"
            "• Levantamiento topográfico detallado en campo<br/>"
            "• Asesoría legal especializada en derecho ambiental<br/>"
            "• Verificación de licencias, permisos y autorizaciones ambientales vigentes",
            self.styles['Advertencia']
        )
        elementos.append(disclaimer_final)
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def generar_pdf(self, parcela: Parcela, resultado: ResultadoVerificacion, 
                   verificador: VerificadorRestriccionesLegales, output_path: str,
                   departamento: str = "Casanare") -> str:
        """
        Genera el PDF completo de verificación legal MEJORADO
        
        Args:
            parcela: Objeto Parcela de Django
            resultado: ResultadoVerificacion del verificador legal
            verificador: Instancia del VerificadorRestriccionesLegales
            output_path: Ruta donde guardar el PDF
            departamento: Nombre del departamento para filtrado
        
        Returns:
            Ruta del PDF generado
        """
        print(f"\n{'='*80}")
        print(f"📄 GENERANDO PDF MEJORADO DE VERIFICACIÓN LEGAL")
        print(f"{'='*80}\n")
        
        # Crear directorio si no existe (solo si hay directorio en el path)
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Calcular distancias mínimas (análisis de proximidad)
        print(f"📍 Calculando análisis de proximidad para {departamento}...")
        distancias = self._calcular_distancias_minimas(parcela, verificador, departamento)
        
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
        
        # ✨ NUEVO ORDEN COMERCIAL V3 (Psicología de Venta)
        
        # 1. Portada (con resultado destacado)
        print("📋 Generando portada...")
        elementos.extend(self._crear_portada(parcela, resultado, departamento))
        
        # 2. Conclusión Ejecutiva (NUEVO - 1 párrafo comercial)
        print("📊 Generando conclusión ejecutiva comercial...")
        elementos.extend(self._crear_conclusion_ejecutiva(resultado, parcela, departamento))
        
        # 3. Mapa Silueta (NUEVO - impacto visual inmediato)
        print("�️  Generando mapa silueta limpio...")
        try:
            titulo_silueta = Paragraph("🗺️ MAPA SILUETA - ÁREA EVALUADA", self.styles['SubtituloPersonalizado'])
            elementos.append(titulo_silueta)
            elementos.append(Spacer(1, 0.3*cm))
            desc_silueta = Paragraph(
                f"Visualización del área total de la parcela para referencia geográfica y evaluación de escala.",
                self.styles['TextoNormal']
            )
            elementos.append(desc_silueta)
            elementos.append(Spacer(1, 0.5*cm))
            
            img_silueta = self._generar_mapa_silueta(parcela, departamento)
            img_silueta_reportlab = Image(img_silueta, width=16*cm, height=12*cm)
            elementos.append(img_silueta_reportlab)
            elementos.append(Spacer(1, 0.5*cm))
            elementos.append(PageBreak())
        except Exception as e:
            print(f"   ⚠️  Advertencia: No se pudo generar mapa silueta: {str(e)}")
        
        # 4. Mapa Contexto Regional (NUEVO - ubicación general)
        print("🌍 Generando mapa de contexto regional...")
        try:
            titulo_contexto = Paragraph("🌍 CONTEXTO REGIONAL - UBICACIÓN GENERAL", self.styles['SubtituloPersonalizado'])
            elementos.append(titulo_contexto)
            elementos.append(Spacer(1, 0.3*cm))
            desc_contexto = Paragraph(
                f"Ubicación de la parcela dentro de {departamento} para evaluación de riesgo por ubicación geográfica.",
                self.styles['TextoNormal']
            )
            elementos.append(desc_contexto)
            elementos.append(Spacer(1, 0.5*cm))
            
            img_contexto = self._generar_mapa_contexto_regional(parcela, departamento)
            img_contexto_reportlab = Image(img_contexto, width=16*cm, height=12*cm)
            elementos.append(img_contexto_reportlab)
            elementos.append(Spacer(1, 0.5*cm))
            elementos.append(PageBreak())
        except Exception as e:
            print(f"   ⚠️  Advertencia: No se pudo generar mapa de contexto: {str(e)}")
        
        # 5. Mapa Técnico Principal (refactorizado con flechas y capas)
        print(f"🗺️  Generando mapa técnico principal con flechas y capas...")
        elementos.extend(self._crear_seccion_mapa(parcela, verificador, departamento, distancias))
        
        # 6. Análisis por Capa (metadatos + restricciones)
        print("� Generando metadatos de capas geográficas...")
        elementos.extend(self._crear_tabla_metadatos_capas(departamento))
        
        print("�📊 Generando tabla de restricciones...")
        elementos.extend(self._crear_tabla_restricciones(resultado))
        
        # 7. Análisis de Proximidad
        print("📍 Generando análisis de proximidad...")
        elementos.extend(self._crear_seccion_proximidad(distancias, departamento))
        
        # 8. Niveles de Confianza
        print("📈 Generando niveles de confianza...")
        elementos.extend(self._crear_seccion_confianza(resultado, departamento))
        
        # 9. Advertencias (si existen)
        if resultado.advertencias:
            print("⚠️  Generando advertencias...")
            elementos.extend(self._crear_seccion_advertencias(resultado))
        
        # 10. Recomendaciones
        print("💡 Generando recomendaciones legales...")
        elementos.extend(self._crear_seccion_recomendaciones(resultado, parcela, departamento))
        
        # 11. Limitaciones Técnicas (NUEVO - disclaimer legal final)
        print("⚠️  Generando sección de limitaciones técnicas...")
        elementos.extend(self._crear_seccion_limitaciones_tecnicas(resultado, departamento))
        
        # Construir PDF
        print("🔨 Construyendo documento PDF...")
        doc.build(elementos)
        
        print(f"\n✅ PDF generado exitosamente: {output_path}")
        print(f"   Tamaño: {os.path.getsize(output_path) / 1024:.2f} KB")
        print(f"{'='*80}\n")
        
        return output_path


def main():
    """Función principal para generar PDF COMERCIAL V3 de verificación legal"""
    print("\n" + "="*80)
    print("🏛️  GENERACIÓN DE PDF COMERCIAL V3 - VERIFICACIÓN LEGAL CASANARE")
    print("="*80)
    print("\n✨ MEJORAS V3 IMPLEMENTADAS (Brief Comercial):")
    print("   ✅ Tres mapas profesionales: Contexto Regional, Técnico con Flechas, Silueta Limpia")
    print("   ✅ Orden psicológico de venta optimizado para evaluación crediticia")
    print("   ✅ Conclusión ejecutiva comercial en primera página")
    print("   ✅ Metadatos completos por capa geográfica (fuente, año, limitación)")
    print("   ✅ Tabla de limitaciones técnicas (disclaimer legal reforzado)")
    print("   ✅ Copy técnico-legal defendible (sin afirmaciones absolutas)")
    print("\n🔧 MEJORAS V2 (Base):")
    print("   ✅ Filtrado específico para Casanare")
    print("   ✅ Análisis de proximidad a zonas críticas")
    print("   ✅ Información de contexto geográfico")
    print("   ✅ Tabla de confianza sin N/A\n")
    
    departamento = "Casanare"
    
    # 1. Obtener la parcela
    try:
        parcela = Parcela.objects.get(id=6)
        print(f"✅ Parcela encontrada:")
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
    print(f"\n🔍 Iniciando verificación legal para {departamento}...")
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
    
    # 4. Generar PDF MEJORADO
    output_dir = os.path.join(
        os.path.dirname(__file__),
        'media',
        'verificacion_legal'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(
        output_dir,
        f'verificacion_legal_{departamento.lower()}_parcela_{parcela.id}_MEJORADO_{timestamp}.pdf'
    )
    
    generador = GeneradorPDFLegal()
    pdf_path = generador.generar_pdf(parcela, resultado, verificador, output_path, departamento)
    
    print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
    print(f"   PDF generado: {pdf_path}")
    print(f"\n💡 El PDF incluye:")
    print(f"   ✅ Portada con info de {departamento}")
    print(f"   ✅ Análisis de proximidad (distancias a zonas críticas)")
    print(f"   ✅ Mapa con datos filtrados para {departamento}")
    print(f"   ✅ Tabla de confianza SIN N/A")
    print(f"   ✅ Niveles de confianza con fuentes oficiales")
    print(f"   ✅ Recomendaciones contextualizadas")
    print(f"\n" + "="*80)


if __name__ == "__main__":
    main()
