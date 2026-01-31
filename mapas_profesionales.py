#!/usr/bin/env python
"""
🗺️ MÓDULO DE MAPAS PROFESIONALES - PLANTILLA BASE
===================================================

Funciones modulares para generar mapas técnicos con jerarquía visual profesional.
Diseñado para ser importado por generador_pdf_legal.py

Características:
- Jerarquía visual clara (límite municipal dominante)
- Red hídrica jerarquizada (principales vs secundarios)
- Etiquetado inteligente y bien posicionado
- Fuentes de datos documentadas
- Reutilizable como plantilla base
"""

import geopandas as gpd
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 CONFIGURACIÓN VISUAL PROFESIONAL (PLANTILLA BASE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Colores institucionales
COLOR_LIMITE_MUNICIPAL = '#6B8E23'     # Verde oliva intenso (diferenciación clara de red hídrica)
COLOR_RIO_PRINCIPAL = '#0D47A1'        # Azul intenso (destacado)
COLOR_RIO_SECUNDARIO = '#64B5F6'       # Azul claro (contexto)
COLOR_PARCELA = '#C62828'              # Rojo intenso (elemento de interés)
COLOR_PARCELA_RELLENO = '#FFCDD2'      # Rojo claro translúcido
COLOR_FONDO = 'white'                  # Blanco limpio
COLOR_GRID = '#E0E0E0'                 # Gris muy claro

# Jerarquía Z-order
ZORDER_FONDO = 1
ZORDER_ZONAS_CRITICAS = 2
ZORDER_RIOS_SECUNDARIOS = 5
ZORDER_RIOS_PRINCIPALES = 6
ZORDER_PARCELA_RELLENO = 8
ZORDER_HALO_MUNICIPIO = 9
ZORDER_LIMITE_MUNICIPAL = 10
ZORDER_PARCELA_BORDE = 11
ZORDER_MARCADOR_PARCELA = 12
ZORDER_ETIQUETAS = 15
ZORDER_ELEMENTOS_CARTOGRAFICOS = 100

# Configuración general
DPI_MAPA = 300
FIGSIZE_MAPA = (12, 10)
MARGEN_MUNICIPIO_PCT = 0.08
BUFFER_PARCELA_FACTOR = 1.0
BUFFER_MINIMO_KM = 0.02
MAX_ETIQUETAS_RIOS = 5
MAX_LONGITUD_NOMBRE = 25
PERCENTIL_CLASIFICACION = 75


def clasificar_rios(red_hidrica_gdf):
    """
    🌊 Clasifica la red hídrica en principales y secundarios
    
    Criterios (en orden de prioridad):
    1. Orden de Strahler (campo 'orden', 'orden_strah', 'strahler') >= 4
    2. Longitud > percentil 75
    3. Tiene nombre conocido
    
    Args:
        red_hidrica_gdf: GeoDataFrame con red hídrica
    
    Returns:
        tuple: (principales_gdf, secundarios_gdf)
    """
    if red_hidrica_gdf is None or len(red_hidrica_gdf) == 0:
        return None, None
    
    red = red_hidrica_gdf.copy()
    
    # Calcular longitud
    red['longitud_calc'] = red.geometry.length
    
    # Percentil 75 de longitud
    percentil_75 = red['longitud_calc'].quantile(PERCENTIL_CLASIFICACION / 100)
    
    # Verificar si tiene campo de orden
    campo_orden = None
    for campo in ['orden', 'orden_strah', 'strahler', 'ORDEN', 'Strahler']:
        if campo in red.columns:
            campo_orden = campo
            break
    
    # Clasificar
    es_principal = red['longitud_calc'] > percentil_75
    
    if campo_orden:
        # Si tiene orden de Strahler, usarlo como criterio dominante
        es_principal = es_principal | (red[campo_orden] >= 4)
    
    # Verificar si tiene nombre
    for campo_nombre in ['NOMBRE', 'nombre', 'name', 'NOMBRE_GEO', 'Nombre']:
        if campo_nombre in red.columns:
            tiene_nombre = red[campo_nombre].notna() & (red[campo_nombre] != '') & (red[campo_nombre] != 'None')
            es_principal = es_principal | tiene_nombre
            break
    
    principales = red[es_principal].copy()
    secundarios = red[~es_principal].copy()
    
    print(f"📊 Clasificación de ríos: {len(principales)} principales, {len(secundarios)} secundarios")
    
    return principales, secundarios


def dibujar_limite_municipal_profesional(ax, municipio_gdf):
    """
    🏛️ Dibuja el límite municipal con jerarquía visual dominante
    
    Técnica:
    1. Halo blanco grueso (resalta el límite)
    2. Línea azul corporativa (dominante)
    
    Args:
        ax: Eje de matplotlib
        municipio_gdf: GeoDataFrame del municipio
    """
    if municipio_gdf is None or len(municipio_gdf) == 0:
        return
    
    # Paso 1: Halo blanco (crea separación visual)
    municipio_gdf.plot(
        ax=ax,
        facecolor='none',
        edgecolor='white',
        linewidth=7,
        alpha=1.0,
        zorder=ZORDER_HALO_MUNICIPIO
    )
    
    # Paso 2: Relleno muy claro
    municipio_gdf.plot(
        ax=ax,
        facecolor='#F5F5F5',  # Gris casi blanco
        edgecolor='none',
        alpha=0.3,
        zorder=ZORDER_FONDO
    )
    
    # Paso 3: Línea dominante azul corporativa
    municipio_gdf.plot(
        ax=ax,
        facecolor='none',
        edgecolor=COLOR_LIMITE_MUNICIPAL,
        linewidth=4.5,
        alpha=1.0,
        zorder=ZORDER_LIMITE_MUNICIPAL,
        linestyle='-'
    )
    
    print("✅ Límite municipal dibujado con jerarquía visual dominante")


def dibujar_red_hidrica_jerarquizada(ax, red_hidrica_gdf):
    """
    🌊 Dibuja la red hídrica con jerarquía visual (principales vs secundarios)
    
    Args:
        ax: Eje de matplotlib
        red_hidrica_gdf: GeoDataFrame con red hídrica
    
    Returns:
        tuple: (num_principales, num_secundarios)
    """
    if red_hidrica_gdf is None or len(red_hidrica_gdf) == 0:
        return 0, 0
    
    principales, secundarios = clasificar_rios(red_hidrica_gdf)
    
    # Dibujar secundarios primero (abajo)
    num_secundarios = 0
    if secundarios is not None and len(secundarios) > 0:
        secundarios.plot(
            ax=ax,
            color=COLOR_RIO_SECUNDARIO,
            linewidth=1.2,
            alpha=0.7,
            zorder=ZORDER_RIOS_SECUNDARIOS
        )
        num_secundarios = len(secundarios)
    
    # Dibujar principales encima
    num_principales = 0
    if principales is not None and len(principales) > 0:
        principales.plot(
            ax=ax,
            color=COLOR_RIO_PRINCIPAL,
            linewidth=2.5,
            alpha=0.95,
            zorder=ZORDER_RIOS_PRINCIPALES
        )
        num_principales = len(principales)
    
    print(f"✅ Red hídrica jerarquizada: {num_principales} principales (gruesos), {num_secundarios} secundarios (delgados)")
    
    return num_principales, num_secundarios


def etiquetar_rios_inteligente(ax, red_hidrica_gdf, xlim, ylim, max_etiquetas=MAX_ETIQUETAS_RIOS):
    """
    🏷️ Etiqueta los ríos más importantes de forma inteligente
    
    Algoritmo:
    1. Clasificar por importancia (longitud + orden + nombre)
    2. Calcular punto medio del tramo
    3. Verificar que esté dentro del marco visible
    4. Aplicar halo blanco sutil
    5. Limitar a max_etiquetas para evitar saturación
    
    Args:
        ax: Eje de matplotlib
        red_hidrica_gdf: GeoDataFrame con red hídrica
        xlim: Límites del eje X (tupla min, max)
        ylim: Límites del eje Y (tupla min, max)
        max_etiquetas: Máximo número de etiquetas
    
    Returns:
        int: Número de ríos etiquetados
    """
    if red_hidrica_gdf is None or len(red_hidrica_gdf) == 0:
        return 0
    
    # Obtener solo los principales (ya clasificados)
    principales, _ = clasificar_rios(red_hidrica_gdf)
    
    if principales is None or len(principales) == 0:
        return 0
    
    # Ordenar por longitud (más largos primero)
    principales_ordenados = principales.sort_values('longitud_calc', ascending=False)
    
    etiquetas_dibujadas = 0
    
    for idx, rio in principales_ordenados.iterrows():
        if etiquetas_dibujadas >= max_etiquetas:
            break
        
        # Buscar nombre
        nombre_rio = None
        for campo in ['NOMBRE', 'nombre', 'name', 'NOMBRE_GEO', 'Nombre']:
            if campo in rio.index:
                n = rio.get(campo)
                if n and str(n).strip() and str(n).lower() not in ['none', 'nan', '', 'sin nombre']:
                    nombre_rio = str(n)[:MAX_LONGITUD_NOMBRE]
                    break
        
        if not nombre_rio:
            continue
        
        try:
            # Calcular punto medio del tramo
            if rio.geometry.geom_type == 'LineString':
                punto = rio.geometry.interpolate(0.5, normalized=True)
            elif rio.geometry.geom_type == 'MultiLineString':
                # Para MultiLineString, usar el tramo más largo
                linea_mas_larga = max(list(rio.geometry.geoms), key=lambda l: l.length)
                punto = linea_mas_larga.interpolate(0.5, normalized=True)
            else:
                continue
            
            # Verificar que el punto esté dentro del marco visible
            if not (xlim[0] <= punto.x <= xlim[1] and ylim[0] <= punto.y <= ylim[1]):
                print(f"⚠️  Etiqueta '{nombre_rio}' fuera del marco, omitida")
                continue
            
            # Dibujar etiqueta con halo blanco sutil
            ax.text(
                punto.x, punto.y,
                nombre_rio,
                fontsize=9,
                fontweight='bold',
                color=COLOR_RIO_PRINCIPAL,
                ha='center',
                va='center',
                bbox=dict(
                    boxstyle='round,pad=0.4',
                    facecolor='white',
                    edgecolor=COLOR_RIO_PRINCIPAL,
                    linewidth=1.5,
                    alpha=0.85
                ),
                zorder=ZORDER_ETIQUETAS
            )
            
            etiquetas_dibujadas += 1
            
        except Exception as e:
            print(f"⚠️  Error al etiquetar '{nombre_rio}': {str(e)}")
            continue
    
    print(f"✅ Etiquetados {etiquetas_dibujadas} ríos principales (dentro del marco)")
    
    return etiquetas_dibujadas


def agregar_leyenda_profesional(ax, municipio_gdf, parcela_gdf, num_rios, areas_dibujadas=0):
    """
    📊 Agrega leyenda profesional al mapa
    
    Args:
        ax: Eje de matplotlib
        municipio_gdf: GeoDataFrame del municipio (o None)
        parcela_gdf: GeoDataFrame de la parcela
        num_rios: Número de ríos dibujados
        areas_dibujadas: Número de áreas protegidas dibujadas
    """
    legend_elements = []
    
    # Límite municipal
    if municipio_gdf is not None and len(municipio_gdf) > 0:
        legend_elements.append(
            Line2D(
                [0], [0],
                color=COLOR_LIMITE_MUNICIPAL,
                linewidth=4,
                label='Límite Municipal'
            )
        )
    
    # Parcela
    legend_elements.append(
        Line2D(
            [0], [0],
            color=COLOR_PARCELA,
            linewidth=3,
            label='Parcela Analizada'
        )
    )
    
    # Red hídrica
    if num_rios > 0:
        legend_elements.append(
            Line2D(
                [0], [0],
                color=COLOR_RIO_PRINCIPAL,
                linewidth=2.5,
                label=f'Ríos Principales'
            )
        )
        legend_elements.append(
            Line2D(
                [0], [0],
                color=COLOR_RIO_SECUNDARIO,
                linewidth=1.2,
                alpha=0.7,
                label=f'Ríos Secundarios'
            )
        )
    
    # Áreas protegidas
    if areas_dibujadas > 0:
        legend_elements.append(
            Patch(
                facecolor='#FFF9C4',
                edgecolor='#F57C00',
                alpha=0.35,
                label='Zonas Protegidas'
            )
        )
    
    # Dibujar leyenda
    if legend_elements:
        ax.legend(
            handles=legend_elements,
            loc='upper left',
            fontsize=9,
            framealpha=0.95,
            edgecolor='black',
            fancybox=True,
            shadow=True,
            title='Leyenda',
            title_fontsize=10
        )


def agregar_bloque_fuentes_legales():
    """
    📚 Crea el bloque de fuentes de datos legales para añadir al PDF
    
    Returns:
        Table: Tabla ReportLab con las fuentes de datos
    """
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    
    fuentes_texto = """<b>📚 FUENTES DE DATOS GEOGRÁFICOS</b>

• <b>Límites Administrativos:</b> Instituto Geográfico Agustín Codazzi (IGAC) - Marco Geoestadístico Nacional 2023
• <b>Red Hídrica:</b> Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM) - Sistema de Información del Recurso Hídrico (SIRH)
• <b>Áreas Protegidas:</b> Parques Nacionales Naturales de Colombia - Registro Único Nacional de Áreas Protegidas (RUNAP)
• <b>Datum/Proyección:</b> WGS84 (EPSG:4326) para visualización, UTM Zona 18N (EPSG:32618) para cálculos

<i>Nota: Estos datos tienen carácter informativo. Para trámites legales o decisiones definitivas, consulte directamente con las autoridades ambientales competentes (CAR, Corporación Autónoma Regional correspondiente).</i>"""
    
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph
    
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para fuentes
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.styles import ParagraphStyle
    
    estilo_fuentes = ParagraphStyle(
        'FuentesLegales',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#424242'),
        alignment=TA_JUSTIFY,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=5
    )
    
    parrafo_fuentes = Paragraph(fuentes_texto, estilo_fuentes)
    
    # Crear tabla con borde sutil
    tabla_fuentes = Table([[parrafo_fuentes]], colWidths=[16*cm])
    tabla_fuentes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDBDBD')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    return tabla_fuentes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗺️ FUNCIÓN PRINCIPAL DE GENERACIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generar_mapa_ubicacion_municipal_profesional(parcela, save_to_file=False, output_path=None):
    """
    🗺️ Genera mapa profesional de ubicación municipal con jerarquía visual
    
    Esta función encapsula todo el flujo de generación del mapa profesional,
    diseñado para ser usado directamente por generador_pdf_legal.py
    
    Args:
        parcela: Objeto Parcela de Django con geometría y datos
        save_to_file: Si True, guarda imagen en disco (además del buffer)
        output_path: Ruta personalizada para guardar (opcional)
    
    Returns:
        BytesIO: Buffer con imagen PNG del mapa (para PDF)
        
    Excepciones:
        ValueError: Si la parcela no tiene geometría válida
        Exception: Si falla la detección geográfica o generación
    """
    from io import BytesIO
    from datetime import datetime
    import os
    from detector_geografico import DetectorGeografico
    from shapely.geometry import shape
    from shapely import wkt
    
    # Validar parcela
    if not parcela or not parcela.geometria:
        raise ValueError("La parcela debe tener geometría válida")
    
    # Convertir geometría
    if hasattr(parcela.geometria, 'wkt'):
        parcela_geom = wkt.loads(parcela.geometria.wkt)
    else:
        parcela_geom = shape(parcela.geometria)
    
    parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
    
    # Calcular centroide
    UTM_COLOMBIA = 'EPSG:32618'
    parcela_utm = parcela_gdf.to_crs(UTM_COLOMBIA)
    centroide_utm = parcela_utm.geometry.centroid.iloc[0]
    centroide = gpd.GeoSeries([centroide_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
    
    # Detectar ubicación automáticamente usando DetectorGeografico
    detector = DetectorGeografico()
    resultado = detector.proceso_completo(parcela.geometria)
    
    if not resultado['municipio']:
        raise Exception(f"No se pudo detectar el municipio de la parcela")
    
    departamento_nombre = resultado['departamento']
    municipio_nombre = resultado['municipio']
    municipio_gdf = resultado['municipio_gdf']
    red_hidrica_municipal = resultado.get('red_hidrica', None)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=FIGSIZE_MAPA, facecolor=COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)
    
    # Dibujar límite municipal profesional
    dibujar_limite_municipal_profesional(ax, municipio_gdf)
    
    # Dibujar red hídrica jerarquizada
    num_principales, num_secundarios = dibujar_red_hidrica_jerarquizada(ax, red_hidrica_municipal)
    num_rios_total = num_principales + num_secundarios
    
    # Dibujar parcela destacada
    # A) Relleno translúcido
    parcela_gdf.plot(
        ax=ax,
        facecolor=COLOR_PARCELA_RELLENO,
        edgecolor='none',
        alpha=0.4,
        zorder=ZORDER_PARCELA_RELLENO
    )
    
    # B) Borde fuerte
    parcela_gdf.plot(
        ax=ax,
        facecolor='none',
        edgecolor=COLOR_PARCELA,
        linewidth=3,
        alpha=1.0,
        zorder=ZORDER_PARCELA_BORDE
    )
    
    # C) Marcador circular
    ax.plot(
        centroide.x, centroide.y,
        marker='o',
        markersize=15,
        color=COLOR_PARCELA,
        markeredgecolor='white',
        markeredgewidth=2.5,
        zorder=ZORDER_MARCADOR_PARCELA
    )
    
    # Ajustar zoom y encuadre
    municipio_bounds = municipio_gdf.total_bounds
    dx = (municipio_bounds[2] - municipio_bounds[0]) * MARGEN_MUNICIPIO_PCT
    dy = (municipio_bounds[3] - municipio_bounds[1]) * MARGEN_MUNICIPIO_PCT
    
    xlim = (municipio_bounds[0] - dx, municipio_bounds[2] + dx)
    ylim = (municipio_bounds[1] - dy, municipio_bounds[3] + dy)
    
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    # Etiquetar ríos inteligentemente
    etiquetar_rios_inteligente(ax, red_hidrica_municipal, xlim, ylim)
    
    # Elementos cartográficos (Norte y Escala)
    # A) Flecha de Norte
    x_norte = xlim[1] - (xlim[1] - xlim[0]) * 0.10
    y_norte = ylim[1] - (ylim[1] - ylim[0]) * 0.10
    tam_flecha = (ylim[1] - ylim[0]) * 0.06
    
    ax.arrow(
        x_norte, y_norte, 0, tam_flecha,
        head_width=tam_flecha*0.35,
        head_length=tam_flecha*0.25,
        fc='black',
        ec='black',
        linewidth=2,
        zorder=ZORDER_ELEMENTOS_CARTOGRAFICOS
    )
    
    ax.text(
        x_norte, y_norte + tam_flecha * 1.3, 'N',
        fontsize=14,
        fontweight='bold',
        ha='center',
        va='center',
        bbox=dict(
            boxstyle='circle,pad=0.3',
            facecolor='white',
            edgecolor='black',
            linewidth=1.5
        ),
        zorder=ZORDER_ELEMENTOS_CARTOGRAFICOS + 1
    )
    
    # B) Escala gráfica
    escala_km = 2 if (xlim[1] - xlim[0]) < 0.5 else 5
    x_escala = xlim[0] + (xlim[1] - xlim[0]) * 0.15
    y_escala = ylim[0] + (ylim[1] - ylim[0]) * 0.08
    long_barra = escala_km / 111
    
    ax.plot(
        [x_escala, x_escala + long_barra],
        [y_escala, y_escala],
        color='black',
        linewidth=3,
        zorder=ZORDER_ELEMENTOS_CARTOGRAFICOS
    )
    
    ax.text(
        x_escala + long_barra/2, y_escala - (ylim[1] - ylim[0]) * 0.02,
        f'{escala_km} km',
        fontsize=9,
        fontweight='bold',
        ha='center',
        va='top',
        bbox=dict(
            boxstyle='round,pad=0.3',
            facecolor='white',
            edgecolor='black',
            linewidth=1
        ),
        zorder=ZORDER_ELEMENTOS_CARTOGRAFICOS + 1
    )
    
    # Título y etiquetas
    ax.set_title(
        f'Ubicación de la Parcela a Nivel Municipal\nMunicipio: {municipio_nombre} ({departamento_nombre})',
        fontsize=14,
        fontweight='bold',
        pad=15,
        color='#1B5E20'
    )
    
    ax.set_xlabel('Longitud (°)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Latitud (°)', fontsize=10, fontweight='bold')
    
    # Grid sutil
    ax.grid(True, alpha=0.25, linestyle=':', color=COLOR_GRID, linewidth=0.7)
    
    # Etiqueta de parcela
    offset_y = (ylim[1] - ylim[0]) * 0.02
    ax.text(
        centroide.x, centroide.y + offset_y,
        f"📍 {parcela.nombre}\n{parcela.area_hectareas:.2f} ha",
        fontsize=10,
        fontweight='bold',
        ha='center',
        va='bottom',
        color='#B71C1C',
        bbox=dict(
            boxstyle='round,pad=0.5',
            facecolor='white',
            edgecolor=COLOR_PARCELA,
            linewidth=2,
            alpha=0.95
        ),
        zorder=ZORDER_ETIQUETAS + 5
    )
    
    # Leyenda profesional
    agregar_leyenda_profesional(ax, municipio_gdf, parcela_gdf, num_rios_total)
    
    # Finalizar
    plt.tight_layout()
    
    # Guardar en buffer (siempre)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor=COLOR_FONDO)
    img_buffer.seek(0)
    
    # Guardar en archivo (opcional)
    if save_to_file:
        if not output_path:
            output_dir = 'test_outputs_mapas'
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_dir, f'mapa_profesional_parcela{parcela.id}_{timestamp}.png')
        
        plt.savefig(output_path, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor=COLOR_FONDO)
        print(f"✅ Mapa guardado: {output_path}")
    
    plt.close(fig)
    
    return img_buffer


if __name__ == '__main__':
    print("🗺️  Módulo de Mapas Profesionales")
    print("=" * 60)
    print("\nEste módulo contiene funciones para generar mapas técnicos")
    print("con jerarquía visual profesional.")
    print("\nFunciones disponibles:")
    print("  • clasificar_rios()")
    print("  • dibujar_limite_municipal_profesional()")
    print("  • dibujar_red_hidrica_jerarquizada()")
    print("  • etiquetar_rios_inteligente()")
    print("  • agregar_leyenda_profesional()")
    print("  • agregar_bloque_fuentes_legales()")
    print("\nImportar con: from mapas_profesionales import *")
