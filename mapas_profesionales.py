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
import pandas as pd
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 CONFIGURACIÓN VISUAL PROFESIONAL (PLANTILLA BASE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Colores institucionales - MAPA MUNICIPAL
COLOR_LIMITE_MUNICIPAL = '#6B8E23'     # Verde oliva intenso (diferenciación clara de red hídrica)
COLOR_RIO_PRINCIPAL = '#0D47A1'        # Azul intenso (destacado)
COLOR_RIO_SECUNDARIO = '#64B5F6'       # Azul claro (contexto)
COLOR_PARCELA = '#C62828'              # Rojo intenso (elemento de interés)
COLOR_PARCELA_RELLENO = '#FFCDD2'      # Rojo claro translúcido
COLOR_FONDO = 'white'                  # Blanco limpio
COLOR_GRID = '#E0E0E0'                 # Gris muy claro

# Colores institucionales - MAPA DEPARTAMENTAL
COLOR_LIMITE_DEPARTAMENTAL = '#424242'  # Gris oscuro técnico (límite dominante)
COLOR_RESGUARDO_INDIGENA = '#FFF9C4'    # Amarillo suave (restricción legal)
COLOR_RESGUARDO_BORDE = '#F57F17'       # Amarillo oscuro (borde sutil)
COLOR_RESGUARDO_FILL = '#FFF9C4'        # Amarillo suave (fill para leyenda)
COLOR_AREA_PROTEGIDA = '#FFCDD2'        # Rojo suave (restricción ambiental)
COLOR_AREA_PROTEGIDA_BORDE = '#C62828'  # Rojo oscuro (borde visible)
COLOR_PARCELA_PUNTO = '#B71C1C'         # Rojo muy oscuro (punto destacado)

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
MAX_LONGITUD_NOMBRE = 35  # Aumentado para nombres completos como "DRMI de los Páramos de Guantiva"
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


def agregar_leyenda_profesional(ax, municipio_gdf, parcela_gdf, num_rios, areas_dibujadas=0, resguardos_dibujados=0):
    """
    📊 Agrega leyenda profesional al mapa
    
    Args:
        ax: Eje de matplotlib
        municipio_gdf: GeoDataFrame del municipio (o None)
        parcela_gdf: GeoDataFrame de la parcela
        num_rios: Número de ríos dibujados
        areas_dibujadas: Número de áreas protegidas dibujadas
        resguardos_dibujados: Número de resguardos indígenas dibujados
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
    
    # Resguardos indígenas
    if resguardos_dibujados > 0:
        legend_elements.append(
            Patch(
                facecolor=COLOR_RESGUARDO_FILL,
                edgecolor=COLOR_RESGUARDO_BORDE,
                alpha=0.4,
                label='Resguardos Indígenas'
            )
        )
    
    # Dibujar leyenda con z-order alto para que no sea cubierta por elementos del mapa
    if legend_elements:
        legend = ax.legend(
            handles=legend_elements,
            loc='upper left',
            fontsize=9,
            framealpha=1.0,
            edgecolor='black',
            fancybox=True,
            shadow=True,
            title='Leyenda',
            title_fontsize=10
        )
        legend.set_zorder(1000)  # Z-order muy alto para garantizar visibilidad completa


def agregar_bloque_fuentes_legales():
    """
    📚 Crea el bloque de fuentes de datos legales para añadir al PDF
    
    Returns:
        Table: Tabla ReportLab con las fuentes de datos
    """
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    
    fuentes_texto = """<b>📚 FUENTES DE DATOS</b>

<b>Fuentes oficiales:</b> IGAC (límites), IDEAM (hidrología), PNN/RUNAP (áreas protegidas), ANT (resguardos). Proyección: WGS84. 
<i>Datos con carácter informativo. Para trámites oficiales, consulte directamente las autoridades competentes.</i>"""
    
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

def generar_mapa_ubicacion_municipal_profesional(parcela, verificador=None, save_to_file=False, output_path=None):
    """
    🗺️ Genera mapa profesional de ubicación municipal con jerarquía visual
    
    Esta función encapsula todo el flujo de generación del mapa profesional,
    diseñado para ser usado directamente por generador_pdf_legal.py
    
    Args:
        parcela: Objeto Parcela de Django con geometría y datos
        verificador: VerificadorRestriccionesLegales (opcional, para cargar resguardos)
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
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INTEGRACIÓN DE RESGUARDOS INDÍGENAS EN MAPA MUNICIPAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    num_resguardos = 0
    resguardos_municipales = None
    
    # Cargar resguardos indígenas
    resguardos_gdf = None
    if verificador and verificador.resguardos_indigenas is not None:
        resguardos_gdf = verificador.resguardos_indigenas
        print(f"\n🟡 Procesando resguardos indígenas para contexto municipal...")
    else:
        # Intentar cargar directamente
        try:
            resguardos_path = 'datos_geograficos/resguardos_indigenas/Resguardo_Indígena_Formalizado.shp'
            if os.path.exists(resguardos_path):
                resguardos_gdf = gpd.read_file(resguardos_path)
                if resguardos_gdf.crs != 'EPSG:4326':
                    resguardos_gdf = resguardos_gdf.to_crs('EPSG:4326')
                print(f"\n🟡 Procesando resguardos indígenas para contexto municipal...")
        except Exception as e:
            print(f"   ⚠️  No se pudieron cargar resguardos: {str(e)}")
    
    if resguardos_gdf is not None and len(resguardos_gdf) > 0:
        # Crear buffer contextual alrededor de la parcela (8 km para escala municipal)
        BUFFER_CONTEXTO_MUNICIPAL_KM = 8
        parcela_utm_buffered = parcela_utm.geometry.buffer(BUFFER_CONTEXTO_MUNICIPAL_KM * 1000).iloc[0]
        parcela_buffered_gdf = gpd.GeoDataFrame([{'geometry': parcela_utm_buffered}], crs=UTM_COLOMBIA)
        parcela_buffered_4326 = parcela_buffered_gdf.to_crs('EPSG:4326')
        buffer_geom = parcela_buffered_4326.geometry.iloc[0]
        
        # Filtrar resguardos que intersectan el buffer o están dentro del municipio
        municipio_bounds = municipio_gdf.total_bounds
        resguardos_candidatos = resguardos_gdf.cx[municipio_bounds[0]:municipio_bounds[2], municipio_bounds[1]:municipio_bounds[3]]
        
        # Priorizar resguardos dentro del buffer contextual
        resguardos_en_buffer = resguardos_candidatos[resguardos_candidatos.intersects(buffer_geom)]
        
        if len(resguardos_en_buffer) > 0:
            resguardos_municipales = resguardos_en_buffer
        elif len(resguardos_candidatos) > 0:
            # Si no hay en el buffer, tomar los más cercanos del municipio
            resguardos_candidatos_copia = resguardos_candidatos.copy()
            resguardos_candidatos_copia['dist_parcela'] = resguardos_candidatos_copia.geometry.distance(centroide)
            resguardos_municipales = resguardos_candidatos_copia.nsmallest(3, 'dist_parcela')
        
        if resguardos_municipales is not None and len(resguardos_municipales) > 0:
            print(f"   📊 {len(resguardos_municipales)} resguardos relevantes identificados en contexto municipal")
            
            # Dibujar resguardos con estilo claro
            resguardos_municipales.plot(
                ax=ax,
                facecolor=COLOR_RESGUARDO_INDIGENA,
                edgecolor=COLOR_RESGUARDO_BORDE,
                linewidth=1.5,
                alpha=0.65,
                zorder=ZORDER_ZONAS_CRITICAS
            )
            num_resguardos = len(resguardos_municipales)
            print(f"   ✅ {num_resguardos} resguardos dibujados en mapa municipal")
        else:
            print("   ℹ️  No hay resguardos relevantes en el contexto municipal")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
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
    
    # Etiquetar resguardos indígenas (si hay)
    if resguardos_municipales is not None and len(resguardos_municipales) > 0:
        print(f"\n🏷️  Etiquetando resguardos en mapa municipal...")
        
        # Intentar encontrar campo de nombre
        campo_nombre = None
        for campo in ['NOMBRE', 'nombre', 'name', 'RESGUARDO', 'Nombre']:
            if campo in resguardos_municipales.columns:
                campo_nombre = campo
                break
        
        if campo_nombre:
            resguardos_con_nombre = resguardos_municipales[resguardos_municipales[campo_nombre].notna()].copy()
            
            # Ordenar por área (más grandes primero)
            resguardos_con_nombre['area_calc'] = resguardos_con_nombre.geometry.area
            resguardos_con_nombre = resguardos_con_nombre.sort_values('area_calc', ascending=False)
            
            # Etiquetar los 2 más relevantes que estén dentro del marco
            etiquetas_resguardos = 0
            for idx, row in resguardos_con_nombre.head(2).iterrows():
                centroid = row.geometry.centroid
                
                # Verificar que esté dentro del marco
                if xlim[0] <= centroid.x <= xlim[1] and ylim[0] <= centroid.y <= ylim[1]:
                    nombre_corto = str(row[campo_nombre])[:MAX_LONGITUD_NOMBRE]
                    # Etiqueta legal clara
                    etiqueta = f"{nombre_corto}\nResguardo indígena\n(figura constitucional)"
                    
                    ax.text(
                        centroid.x, centroid.y,
                        etiqueta,
                        fontsize=7,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        color='#3E2723',
                        bbox=dict(
                            boxstyle='round,pad=0.4',
                            facecolor='white',
                            edgecolor=COLOR_RESGUARDO_BORDE,
                            linewidth=1.3,
                            alpha=0.95
                        ),
                        zorder=ZORDER_ETIQUETAS
                    )
                    etiquetas_resguardos += 1
            
            if etiquetas_resguardos > 0:
                print(f"   ✅ {etiquetas_resguardos} resguardos etiquetados")
    
    
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
    
    # Leyenda profesional con resguardos
    agregar_leyenda_profesional(ax, municipio_gdf, parcela_gdf, num_rios_total, 0, num_resguardos)
    
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗺️ MAPA 2: UBICACIÓN DEPARTAMENTAL CON RESTRICCIONES LEGALES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generar_mapa_departamental_profesional(parcela, verificador=None, save_to_file=False, output_path=None):
    """
    🗺️ Genera mapa profesional a nivel departamental con restricciones legales
    
    Este mapa muestra el contexto legal y territorial del departamento completo,
    incluyendo resguardos indígenas y áreas protegidas como restricciones de orden superior.
    
    Características:
    - Límite departamental dominante (gris oscuro técnico)
    - Parcela como punto destacado (rojo intenso)
    - Resguardos indígenas (amarillo suave con etiquetas)
    - Áreas protegidas (rojo suave con etiquetas)
    - Etiquetado inteligente (solo dentro del marco)
    - Elementos cartográficos profesionales
    - Bloque de fuentes legales
    
    Args:
        parcela: Objeto Parcela de Django con geometría y datos
        verificador: VerificadorRestriccionesLegales (opcional, para cargar capas)
        save_to_file: Si True, guarda imagen en disco
        output_path: Ruta personalizada para guardar
    
    Returns:
        BytesIO: Buffer con imagen PNG del mapa (para PDF)
    """
    from io import BytesIO
    from datetime import datetime
    import os
    from detector_geografico import DetectorGeografico
    from shapely.geometry import shape
    from shapely import wkt
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ PREPARACIÓN DE DATOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Validar parcela
    if not parcela or not parcela.geometria:
        raise ValueError("La parcela debe tener geometría válida")
    
    # Convertir geometría de la parcela
    if hasattr(parcela.geometria, 'wkt'):
        parcela_geom = wkt.loads(parcela.geometria.wkt)
    else:
        parcela_geom = shape(parcela.geometria)
    
    parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
    
    # Calcular centroide (para mostrar como punto)
    UTM_COLOMBIA = 'EPSG:32618'
    parcela_utm = parcela_gdf.to_crs(UTM_COLOMBIA)
    centroide_utm = parcela_utm.geometry.centroid.iloc[0]
    centroide = gpd.GeoSeries([centroide_utm], crs=UTM_COLOMBIA).to_crs('EPSG:4326').iloc[0]
    
    # Detectar ubicación automáticamente
    print("\n🌍 Detectando ubicación departamental...")
    detector = DetectorGeografico()
    resultado = detector.proceso_completo(parcela.geometria)
    
    if not resultado['departamento']:
        raise Exception("No se pudo detectar el departamento de la parcela")
    
    departamento_nombre = resultado['departamento']
    municipio_nombre = resultado.get('municipio', 'N/A')  # Agregar nombre del municipio
    departamento_gdf = resultado['departamento_gdf']
    
    print(f"✅ Departamento detectado: {departamento_nombre}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ CARGAR CAPAS OFICIALES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📥 Cargando capas oficiales del departamento...")
    
    # Cargar resguardos indígenas
    resguardos_gdf = None
    if verificador and verificador.resguardos_indigenas is not None:
        resguardos_gdf = verificador.resguardos_indigenas
        print(f"✅ Resguardos indígenas: {len(resguardos_gdf)} elementos (desde verificador)")
    else:
        # Intentar cargar directamente
        try:
            resguardos_path = 'datos_geograficos/resguardos_indigenas/Resguardo_Indígena_Formalizado.shp'
            if os.path.exists(resguardos_path):
                resguardos_gdf = gpd.read_file(resguardos_path)
                if resguardos_gdf.crs != 'EPSG:4326':
                    resguardos_gdf = resguardos_gdf.to_crs('EPSG:4326')
                print(f"✅ Resguardos indígenas cargados: {len(resguardos_gdf)} elementos")
        except Exception as e:
            print(f"⚠️  No se pudieron cargar resguardos: {str(e)}")
    
    # Cargar áreas protegidas
    areas_protegidas_gdf = None
    if verificador and verificador.areas_protegidas is not None:
        areas_protegidas_gdf = verificador.areas_protegidas
        print(f"✅ Áreas protegidas: {len(areas_protegidas_gdf)} elementos (desde verificador)")
    else:
        # Intentar cargar directamente
        try:
            runap_path = 'datos_geograficos/runap/runap.shp'
            if os.path.exists(runap_path):
                areas_protegidas_gdf = gpd.read_file(runap_path)
                if areas_protegidas_gdf.crs != 'EPSG:4326':
                    areas_protegidas_gdf = areas_protegidas_gdf.to_crs('EPSG:4326')
                print(f"✅ Áreas protegidas cargadas: {len(areas_protegidas_gdf)} elementos")
        except Exception as e:
            print(f"⚠️  No se pudieron cargar áreas protegidas: {str(e)}")
    
    # Cargar red hídrica del departamento
    red_hidrica_gdf = resultado.get('red_hidrica', None)
    if red_hidrica_gdf is not None and len(red_hidrica_gdf) > 0:
        print(f"✅ Red hídrica departamental: {len(red_hidrica_gdf)} elementos")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3️⃣ CREAR FIGURA DEL MAPA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🎨 Creando figura del mapa departamental...")
    fig, ax = plt.subplots(figsize=FIGSIZE_MAPA, facecolor=COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4️⃣ DIBUJAR LÍMITE DEPARTAMENTAL (BASE)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🏛️  Dibujando límite departamental...")
    
    # A) Fondo del departamento (muy sutil)
    departamento_gdf.plot(
        ax=ax,
        facecolor='#FAFAFA',
        edgecolor='none',
        alpha=0.3,
        zorder=ZORDER_FONDO
    )
    
    # B) Halo blanco (para separar visualmente del borde)
    departamento_gdf.plot(
        ax=ax,
        facecolor='none',
        edgecolor='white',
        linewidth=6,
        alpha=1.0,
        zorder=ZORDER_HALO_MUNICIPIO
    )
    
    # C) Límite departamental dominante (gris oscuro técnico)
    departamento_gdf.plot(
        ax=ax,
        facecolor='none',
        edgecolor=COLOR_LIMITE_DEPARTAMENTAL,
        linewidth=4,
        alpha=1.0,
        zorder=ZORDER_LIMITE_MUNICIPAL
    )
    
    print("✅ Límite departamental dibujado con jerarquía visual")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5️⃣ DIBUJAR RESGUARDOS INDÍGENAS (CON BUFFER CONTEXTUAL)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    num_resguardos = 0
    resguardos_dept = None
    
    if resguardos_gdf is not None and len(resguardos_gdf) > 0:
        print("\n🟡 Procesando resguardos indígenas para contexto departamental...")
        
        # Crear buffer contextual alrededor de la parcela (10 km)
        BUFFER_CONTEXTO_KM = 10
        parcela_utm_buffered = parcela_utm.geometry.buffer(BUFFER_CONTEXTO_KM * 1000).iloc[0]
        parcela_buffered_gdf = gpd.GeoDataFrame([{'geometry': parcela_utm_buffered}], crs=UTM_COLOMBIA)
        parcela_buffered_4326 = parcela_buffered_gdf.to_crs('EPSG:4326')
        buffer_geom = parcela_buffered_4326.geometry.iloc[0]
        
        # Filtrar resguardos que intersectan el buffer o están dentro del departamento
        dept_bounds = departamento_gdf.total_bounds
        resguardos_candidatos = resguardos_gdf.cx[dept_bounds[0]:dept_bounds[2], dept_bounds[1]:dept_bounds[3]]
        
        # Priorizar resguardos dentro del buffer contextual
        resguardos_en_buffer = resguardos_candidatos[resguardos_candidatos.intersects(buffer_geom)]
        
        # Si hay pocos en el buffer, incluir también los más cercanos del departamento
        if len(resguardos_en_buffer) < 3 and len(resguardos_candidatos) > 0:
            # Calcular distancias al centroide de la parcela
            resguardos_candidatos_copia = resguardos_candidatos.copy()
            resguardos_candidatos_copia['dist_parcela'] = resguardos_candidatos_copia.geometry.distance(centroide)
            resguardos_cercanos = resguardos_candidatos_copia.nsmallest(5, 'dist_parcela')
            # Combinar con los del buffer
            resguardos_dept = gpd.GeoDataFrame(
                pd.concat([resguardos_en_buffer, resguardos_cercanos]).drop_duplicates(),
                crs='EPSG:4326'
            )
        else:
            resguardos_dept = resguardos_en_buffer
        
        if resguardos_dept is not None and len(resguardos_dept) > 0:
            print(f"   📊 {len(resguardos_dept)} resguardos relevantes identificados (de {len(resguardos_candidatos)} totales en departamento)")
            
            # Dibujar resguardos con estilo legal claro
            resguardos_dept.plot(
                ax=ax,
                facecolor=COLOR_RESGUARDO_INDIGENA,
                edgecolor=COLOR_RESGUARDO_BORDE,
                linewidth=1.5,
                alpha=0.65,
                zorder=ZORDER_ZONAS_CRITICAS
            )
            num_resguardos = len(resguardos_dept)
            print(f"✅ {num_resguardos} resguardos indígenas dibujados en mapa departamental")
        else:
            print("   ℹ️  No hay resguardos relevantes en el contexto departamental")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6️⃣ DIBUJAR ÁREAS PROTEGIDAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    num_areas = 0
    areas_dept = None
    if areas_protegidas_gdf is not None and len(areas_protegidas_gdf) > 0:
        print("\n🔴 Dibujando áreas protegidas...")
        
        # Filtrar por departamento
        dept_bounds = departamento_gdf.total_bounds
        areas_dept = areas_protegidas_gdf.cx[dept_bounds[0]:dept_bounds[2], dept_bounds[1]:dept_bounds[3]]
        
        if len(areas_dept) > 0:
            # Dibujar áreas protegidas
            areas_dept.plot(
                ax=ax,
                facecolor=COLOR_AREA_PROTEGIDA,
                edgecolor=COLOR_AREA_PROTEGIDA_BORDE,
                linewidth=1.2,
                alpha=0.5,
                zorder=ZORDER_ZONAS_CRITICAS + 1
            )
            num_areas = len(areas_dept)
            print(f"✅ {num_areas} áreas protegidas dibujadas")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6️⃣B DIBUJAR RED HÍDRICA DEPARTAMENTAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    num_rios = 0
    if red_hidrica_gdf is not None and len(red_hidrica_gdf) > 0:
        print("\n🌊 Dibujando red hídrica departamental...")
        
        # Clasificar ríos en principales y secundarios
        principales_gdf, secundarios_gdf = clasificar_rios(red_hidrica_gdf)
        
        # Filtrar por departamento
        dept_bounds = departamento_gdf.total_bounds
        
        # Dibujar ríos secundarios primero (abajo)
        if secundarios_gdf is not None and len(secundarios_gdf) > 0:
            rios_sec_dept = secundarios_gdf.cx[dept_bounds[0]:dept_bounds[2], dept_bounds[1]:dept_bounds[3]]
            if len(rios_sec_dept) > 0:
                rios_sec_dept.plot(
                    ax=ax,
                    color=COLOR_RIO_SECUNDARIO,
                    linewidth=0.8,
                    alpha=0.6,
                    zorder=ZORDER_RIOS_SECUNDARIOS - 3
                )
        
        # Dibujar ríos principales encima
        if principales_gdf is not None and len(principales_gdf) > 0:
            rios_prin_dept = principales_gdf.cx[dept_bounds[0]:dept_bounds[2], dept_bounds[1]:dept_bounds[3]]
            if len(rios_prin_dept) > 0:
                rios_prin_dept.plot(
                    ax=ax,
                    color=COLOR_RIO_PRINCIPAL,
                    linewidth=1.5,
                    alpha=0.8,
                    zorder=ZORDER_RIOS_PRINCIPALES - 3
                )
                num_rios = len(rios_prin_dept) + (len(rios_sec_dept) if secundarios_gdf is not None else 0)
        
        print(f"✅ Red hídrica dibujada: {num_rios} cauces")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7️⃣ DIBUJAR PARCELA COMO PUNTO DESTACADO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📍 Dibujando parcela como punto destacado...")
    
    # Punto grande con halo blanco
    ax.plot(
        centroide.x, centroide.y,
        marker='o',
        markersize=20,
        color=COLOR_PARCELA_PUNTO,
        markeredgecolor='white',
        markeredgewidth=3,
        zorder=ZORDER_MARCADOR_PARCELA
    )
    
    print("✅ Parcela dibujada como punto rojo intenso")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 8️⃣ AJUSTAR ZOOM Y ENCUADRE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🔍 Ajustando zoom y encuadre...")
    dept_bounds = departamento_gdf.total_bounds
    dx = (dept_bounds[2] - dept_bounds[0]) * MARGEN_MUNICIPIO_PCT
    dy = (dept_bounds[3] - dept_bounds[1]) * MARGEN_MUNICIPIO_PCT
    
    xlim = (dept_bounds[0] - dx, dept_bounds[2] + dx)
    ylim = (dept_bounds[1] - dy, dept_bounds[3] + dy)
    
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    print(f"✅ Encuadre: {xlim[1]-xlim[0]:.4f}° x {ylim[1]-ylim[0]:.4f}°")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 9️⃣ ETIQUETAR ZONAS CRÍTICAS INTELIGENTEMENTE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🏷️  Etiquetando zonas críticas (solo dentro del marco)...")
    
    num_etiquetas = 0
    
    # Etiquetar resguardos más relevantes
    if resguardos_dept is not None and len(resguardos_dept) > 0:
        resguardos_con_nombre = resguardos_dept[resguardos_dept.geometry.notna()].copy()
        
        # Intentar encontrar campo de nombre
        campo_nombre = None
        for campo in ['NOMBRE', 'nombre', 'name', 'RESGUARDO', 'Nombre']:
            if campo in resguardos_con_nombre.columns:
                campo_nombre = campo
                break
        
        if campo_nombre:
            resguardos_con_nombre = resguardos_con_nombre[resguardos_con_nombre[campo_nombre].notna()]
            
            # Ordenar por área (más grandes primero)
            resguardos_con_nombre['area_calc'] = resguardos_con_nombre.geometry.area
            resguardos_con_nombre = resguardos_con_nombre.sort_values('area_calc', ascending=False)
            
            # Etiquetar los 3 más relevantes que estén dentro del marco
            for idx, row in resguardos_con_nombre.head(3).iterrows():
                centroid = row.geometry.centroid
                
                # Verificar que esté dentro del marco
                if xlim[0] <= centroid.x <= xlim[1] and ylim[0] <= centroid.y <= ylim[1]:
                    nombre_corto = str(row[campo_nombre])[:MAX_LONGITUD_NOMBRE]
                    # Etiqueta legal clara
                    etiqueta = f"{nombre_corto}\nResguardo indígena\n(figura constitucional)"
                    
                    ax.text(
                        centroid.x, centroid.y,
                        etiqueta,
                        fontsize=7.5,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        color='#3E2723',  # Marrón oscuro (legible sobre amarillo)
                        bbox=dict(
                            boxstyle='round,pad=0.5',
                            facecolor='white',
                            edgecolor=COLOR_RESGUARDO_BORDE,
                            linewidth=1.5,
                            alpha=0.95
                        ),
                        zorder=ZORDER_ETIQUETAS
                    )
                    num_etiquetas += 1
            
            print(f"   ✅ {num_etiquetas} resguardos etiquetados")
    
    # Etiquetar áreas protegidas más relevantes
    if areas_protegidas_gdf is not None and areas_dept is not None and len(areas_dept) > 0:
        areas_con_nombre = areas_dept[areas_dept.geometry.notna()].copy()
        
        # Debug: mostrar columnas disponibles
        # print(f"   Columnas disponibles en áreas protegidas: {list(areas_con_nombre.columns)[:10]}")
        
        # Intentar encontrar campo de nombre
        campo_nombre = None
        for campo in ['ap_nombre', 'NOMBRE', 'nombre', 'name', 'NOMBRE_AP', 'NOM_AP', 'nombre_are', 'cat_name']:
            if campo in areas_con_nombre.columns:
                campo_nombre = campo
                break
        
        if campo_nombre:
            areas_con_nombre = areas_con_nombre[areas_con_nombre[campo_nombre].notna()]
            
            # Ordenar por área
            areas_con_nombre['area_calc'] = areas_con_nombre.geometry.area
            areas_con_nombre = areas_con_nombre.sort_values('area_calc', ascending=False)
            
            # Etiquetar solo las 2 más grandes BIEN dentro del marco (evitar etiquetas en bordes)
            margen_seguridad = 0.15  # 15% de margen desde los bordes
            x_min_seguro = xlim[0] + (xlim[1] - xlim[0]) * margen_seguridad
            x_max_seguro = xlim[1] - (xlim[1] - xlim[0]) * margen_seguridad
            y_min_seguro = ylim[0] + (ylim[1] - ylim[0]) * margen_seguridad
            y_max_seguro = ylim[1] - (ylim[1] - ylim[0]) * margen_seguridad
            
            etiquetas_agregadas = 0
            for idx, row in areas_con_nombre.head(5).iterrows():
                if etiquetas_agregadas >= 2:  # Máximo 2 etiquetas para evitar saturación
                    break
                    
                centroid = row.geometry.centroid
                
                # Verificar que esté BIEN dentro del marco (no en los bordes)
                if (x_min_seguro <= centroid.x <= x_max_seguro and 
                    y_min_seguro <= centroid.y <= y_max_seguro):
                    nombre = str(row[campo_nombre])[:MAX_LONGITUD_NOMBRE]
                    
                    ax.text(
                        centroid.x, centroid.y,
                        nombre,
                        fontsize=7.5,  # Reducido de 8 a 7.5 para evitar superposición
                        fontweight='bold',
                        ha='center',
                        va='center',
                        color='#424242',
                        bbox=dict(
                            boxstyle='round,pad=0.5',
                            facecolor='white',
                            edgecolor=COLOR_AREA_PROTEGIDA_BORDE,
                            linewidth=1.2,
                            alpha=0.9
                        ),
                        zorder=ZORDER_ETIQUETAS
                    )
                    num_etiquetas += 1
                    etiquetas_agregadas += 1
    
    print(f"✅ {num_etiquetas} zonas críticas etiquetadas")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔟 ELEMENTOS CARTOGRÁFICOS (Norte y Escala)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🧭 Agregando elementos cartográficos...")
    
    # A) Flecha de Norte
    x_norte = xlim[1] - (xlim[1] - xlim[0]) * 0.08
    y_norte = ylim[1] - (ylim[1] - ylim[0]) * 0.08
    tam_flecha = (ylim[1] - ylim[0]) * 0.05
    
    ax.arrow(
        x_norte, y_norte, 0, tam_flecha,
        head_width=tam_flecha*0.3,
        head_length=tam_flecha*0.25,
        fc='black',
        ec='black',
        linewidth=2,
        zorder=100
    )
    
    ax.text(
        x_norte, y_norte + tam_flecha * 1.2, 'N',
        fontsize=12,
        fontweight='bold',
        ha='center',
        va='center',
        bbox=dict(
            boxstyle='circle,pad=0.3',
            facecolor='white',
            edgecolor='black',
            linewidth=1.2
        ),
        zorder=101
    )
    
    # B) Escala gráfica
    escala_km = 0.5 if (xlim[1] - xlim[0]) < 0.1 else 1
    x_escala = xlim[0] + (xlim[1] - xlim[0]) * 0.15
    y_escala = ylim[0] + (ylim[1] - ylim[0]) * 0.06
    long_barra = escala_km / 111
    
    ax.plot(
        [x_escala, x_escala + long_barra],
        [y_escala, y_escala],
        color='black',
        linewidth=3,
        zorder=100
    )
    
    ax.text(
        x_escala + long_barra/2, y_escala - (ylim[1] - ylim[0]) * 0.015,
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
        zorder=101
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣1️⃣ LEYENDA PROFESIONAL DEL MAPA DEPARTAMENTAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📊 Agregando leyenda profesional...")
    agregar_leyenda_profesional(ax, None, parcela_gdf, num_rios, num_areas, num_resguardos)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣2️⃣ TÍTULO Y FINALIZACIÓN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ax.set_title(
        f'Contexto Departamental - {departamento_nombre}\nAnálisis de Restricciones Legales Regionales',
        fontsize=14,
        fontweight='bold',
        pad=15,
        color='#1B5E20'
    )
    
    ax.set_xlabel('Longitud (°)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Latitud (°)', fontsize=10, fontweight='bold')
    
    # Grid sutil
    ax.grid(True, alpha=0.25, linestyle=':', color=COLOR_GRID, linewidth=0.7)
    
    plt.tight_layout()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣3️⃣ GUARDAR MAPA DEPARTAMENTAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n💾 Guardando mapa departamental...")
    
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
            output_path = os.path.join(output_dir, f'mapa_departamental_parcela{parcela.id}_{timestamp}.png')
        
        plt.savefig(output_path, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor=COLOR_FONDO)
        print(f"✅ Mapa departamental guardado: {output_path}")
    
    plt.close(fig)
    
    print("\n" + "=" * 80)
    print("✅ MAPA DEPARTAMENTAL GENERADO EXITOSAMENTE")
    print("=" * 80)
    
    return img_buffer


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗺️ MAPA 3: INFLUENCIA LEGAL DIRECTA (IMPLEMENTADO)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generar_mapa_influencia_legal_directa(parcela, verificador, save_to_file=False, output_path=None):
    """
    🗺️ MAPA 3: Mapa de Influencia Legal Directa de la Parcela
    
    Genera un mapa minimalista mostrando SOLO:
    - Silueta de la parcela (elemento central, 60-70% del área)
    - Flechas rojas a cuerpos de agua cercanos
    - Distancias precisas desde el lindero (NO centroide)
    - Direcciones cardinales
    - Barra de escala profesional
    - Flecha de norte
    
    NO incluye:
    - Resguardos indígenas
    - Áreas protegidas  
    - Límites municipales
    - Etiquetas de ríos (solo distancias)
    
    Estilo: Técnico, minimalista, apto para banca.
    
    Args:
        parcela: Objeto Parcela de Django
        verificador: Instancia de VerificadorRestriccionesLegales
        save_to_file: Si True, guarda el mapa en archivo PNG
        output_path: Ruta opcional para guardar el archivo
    
    Returns:
        BytesIO: Buffer con imagen PNG del mapa
    """
    from io import BytesIO
    from datetime import datetime
    from matplotlib.patches import FancyArrowPatch, Rectangle
    from matplotlib.patheffects import withStroke
    import os
    
    print("\n" + "=" * 80)
    print("🗺️  GENERANDO MAPA 3: INFLUENCIA LEGAL DIRECTA")
    print("=" * 80)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ PREPARAR GEOMETRÍA DE LA PARCELA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📐 Preparando geometría de la parcela...")
    
    # Convertir geometría de Django a Shapely
    if hasattr(parcela.geometria, 'wkt'):
        from shapely import wkt as wkt_module
        parcela_geom = wkt_module.loads(parcela.geometria.wkt)
    else:
        parcela_geom = shape(parcela.geometria)
    
    # Crear GeoDataFrame correctamente
    parcela_gdf = gpd.GeoDataFrame(
        [{'geometry': parcela_geom}], 
        crs='EPSG:4326'
    )
    centroide_parcela = parcela_geom.centroid
    
    print(f"✅ Parcela: {parcela.nombre}")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
    print(f"   Centroide: ({centroide_parcela.y:.6f}, {centroide_parcela.x:.6f})")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ BUSCAR CUERPOS DE AGUA CERCANOS (500m buffer)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🌊 Buscando cuerpos de agua cercanos...")
    
    # Buffer de 500m alrededor de la parcela
    buffer_500m = parcela_geom.buffer(0.0045)  # ~500m en grados
    
    rios_cercanos = None
    if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
        red_hidrica_area = verificador.red_hidrica[
            verificador.red_hidrica.geometry.intersects(buffer_500m)
        ].copy()
        
        if len(red_hidrica_area) > 0:
            rios_cercanos = red_hidrica_area
            print(f"✅ Cuerpos de agua encontrados: {len(rios_cercanos)}")
        else:
            print("⚠️  No hay cuerpos de agua en el área de consulta (500m)")
    else:
        print("⚠️  No hay datos de red hídrica disponibles")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3️⃣ CALCULAR DISTANCIAS DESDE LINDERO (NO CENTROIDE)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📏 Calculando distancias desde lindero...")
    
    relaciones = []
    
    if rios_cercanos is not None and len(rios_cercanos) > 0:
        for idx, rio in rios_cercanos.iterrows():
            # Distancia desde LINDERO, no centroide
            distancia_m = parcela_geom.distance(rio.geometry) * 111000  # Convertir grados a metros
            
            # Solo incluir elementos a menos de 500m
            if distancia_m <= 500:
                # Calcular punto más cercano en el lindero
                punto_cercano_lindero = parcela_geom.boundary.interpolate(
                    parcela_geom.boundary.project(Point(rio.geometry.centroid))
                )
                
                # Calcular punto más cercano en el río
                punto_cercano_rio = rio.geometry.interpolate(
                    rio.geometry.project(punto_cercano_lindero)
                )
                
                # Dirección cardinal
                dx = punto_cercano_rio.x - punto_cercano_lindero.x
                dy = punto_cercano_rio.y - punto_cercano_lindero.y
                
                if abs(dy) > abs(dx):
                    direccion = 'N' if dy > 0 else 'S'
                else:
                    direccion = 'E' if dx > 0 else 'O'
                
                # Obtener nombre del río (si existe)
                nombre_rio = None
                for campo in ['NOMBRE', 'nombre', 'name', 'NOMBRE_GEO', 'Nombre']:
                    if campo in rio and pd.notna(rio[campo]) and str(rio[campo]).strip() != '':
                        nombre_rio = str(rio[campo]).strip()
                        break
                
                relaciones.append({
                    'tipo': 'red_hidrica',
                    'nombre': nombre_rio or 'Cuerpo de agua',
                    'distancia_m': distancia_m,
                    'direccion': direccion,
                    'punto_lindero': punto_cercano_lindero,
                    'punto_destino': punto_cercano_rio,
                    'geometria_destino': rio.geometry
                })
        
        # Ordenar por distancia y tomar los 3 más cercanos
        relaciones = sorted(relaciones, key=lambda x: x['distancia_m'])[:3]
        
        print(f"✅ Relaciones espaciales identificadas: {len(relaciones)}")
        for rel in relaciones:
            print(f"   • {rel['nombre']}: {rel['distancia_m']:.0f}m al {rel['direccion']}")
    else:
        print("ℹ️  No hay elementos cercanos para mostrar distancias")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4️⃣ DEFINIR ÁREA DE VISUALIZACIÓN
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🎯 Definiendo área de visualización...")
    
    # La parcela debe ocupar 60-70% del área del mapa
    bounds_parcela = parcela_geom.bounds  # (minx, miny, maxx, maxy)
    width = bounds_parcela[2] - bounds_parcela[0]
    height = bounds_parcela[3] - bounds_parcela[1]
    
    # Expandir para que la parcela ocupe 65% del área
    factor_zoom = 1.5  # La parcela ocupará 1/1.5 = 66.7% del área
    
    center_x = (bounds_parcela[0] + bounds_parcela[2]) / 2
    center_y = (bounds_parcela[1] + bounds_parcela[3]) / 2
    
    new_width = width * factor_zoom
    new_height = height * factor_zoom
    
    # Si hay relaciones, asegurar que todas sean visibles
    if relaciones:
        for rel in relaciones:
            pt = rel['punto_destino']
            new_width = max(new_width, abs(pt.x - center_x) * 2.2)
            new_height = max(new_height, abs(pt.y - center_y) * 2.2)
    
    xlim = (center_x - new_width/2, center_x + new_width/2)
    ylim = (center_y - new_height/2, center_y + new_height/2)
    
    print(f"✅ Área de visualización definida")
    print(f"   X: {xlim[0]:.6f} - {xlim[1]:.6f}")
    print(f"   Y: {ylim[0]:.6f} - {ylim[1]:.6f}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5️⃣ CREAR FIGURA Y DIBUJAR MAPA BASE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🎨 Creando figura...")
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 12), dpi=DPI_MAPA)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect('equal')
    ax.set_facecolor('#FAFAFA')  # Fondo gris muy claro
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6️⃣ DIBUJAR CUERPOS DE AGUA (SOLO CONTEXTO MÍNIMO)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🌊 Dibujando red hídrica...")
    
    if rios_cercanos is not None and len(rios_cercanos) > 0:
        rios_cercanos.plot(
            ax=ax,
            color=COLOR_RIO_PRINCIPAL,
            linewidth=2.0,
            alpha=0.6,
            zorder=3
        )
        print(f"✅ {len(rios_cercanos)} cuerpos de agua dibujados")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7️⃣ DIBUJAR PARCELA (ELEMENTO CENTRAL)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📍 Dibujando parcela...")
    
    # Relleno translúcido
    parcela_gdf.plot(
        ax=ax,
        facecolor=COLOR_PARCELA_RELLENO,
        edgecolor='none',
        alpha=0.4,
        zorder=8
    )
    
    # Borde negro grueso (destacado)
    parcela_gdf.plot(
        ax=ax,
        facecolor='none',
        edgecolor='#212121',
        linewidth=3.0,
        alpha=1.0,
        zorder=11
    )
    
    print("✅ Parcela dibujada")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 8️⃣ DIBUJAR FLECHAS DE INFLUENCIA Y DISTANCIAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🎯 Dibujando flechas de influencia...")
    
    for rel in relaciones:
        # Flecha roja desde lindero al elemento
        arrow = FancyArrowPatch(
            (rel['punto_lindero'].x, rel['punto_lindero'].y),
            (rel['punto_destino'].x, rel['punto_destino'].y),
            arrowstyle='->,head_width=0.4,head_length=0.6',
            color=COLOR_PARCELA,  # Rojo intenso
            lw=2.5,
            zorder=100,
            alpha=0.9
        )
        ax.add_patch(arrow)
        
        # Etiqueta de distancia (en el punto medio de la flecha)
        mid_x = (rel['punto_lindero'].x + rel['punto_destino'].x) / 2
        mid_y = (rel['punto_lindero'].y + rel['punto_destino'].y) / 2
        
        # Texto con fondo blanco
        texto_distancia = f"{rel['distancia_m']:.0f} m"
        
        ax.text(
            mid_x, mid_y,
            texto_distancia,
            fontsize=10,
            fontweight='bold',
            color='#212121',
            ha='center',
            va='center',
            zorder=101,
            bbox=dict(
                boxstyle='round,pad=0.4',
                facecolor='white',
                edgecolor=COLOR_PARCELA,
                linewidth=1.5,
                alpha=0.95
            )
        )
    
    print(f"✅ {len(relaciones)} flechas de influencia dibujadas")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 9️⃣ ELEMENTOS CARTOGRÁFICOS: NORTE Y ESCALA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n🧭 Agregando elementos cartográficos...")
    
    # Flecha de Norte (esquina superior derecha)
    from matplotlib.patches import FancyArrow
    
    norte_x = xlim[1] - (xlim[1] - xlim[0]) * 0.08
    norte_y = ylim[1] - (ylim[1] - ylim[0]) * 0.08
    norte_altura = (ylim[1] - ylim[0]) * 0.05
    
    ax.add_patch(FancyArrow(
        norte_x, norte_y,
        0, norte_altura,
        width=norte_altura * 0.3,
        head_width=norte_altura * 0.6,
        head_length=norte_altura * 0.4,
        fc='#212121',
        ec='white',
        linewidth=1.5,
        zorder=200
    ))
    
    ax.text(
        norte_x, norte_y + norte_altura + (ylim[1] - ylim[0]) * 0.015,
        'N',
        fontsize=14,
        fontweight='bold',
        ha='center',
        va='bottom',
        color='#212121',
        zorder=200
    )
    
    # Barra de escala (esquina inferior izquierda)
    escala_x = xlim[0] + (xlim[1] - xlim[0]) * 0.05
    escala_y = ylim[0] + (ylim[1] - ylim[0]) * 0.08
    
    # Calcular distancia representativa (100m en grados)
    dist_100m_grados = 100 / 111000
    
    # Dibujar barra de escala
    ax.plot(
        [escala_x, escala_x + dist_100m_grados],
        [escala_y, escala_y],
        color='#212121',
        linewidth=3.5,
        solid_capstyle='butt',
        zorder=200
    )
    
    # Marcadores verticales
    for offset in [0, dist_100m_grados]:
        ax.plot(
            [escala_x + offset, escala_x + offset],
            [escala_y - (ylim[1] - ylim[0]) * 0.008, escala_y + (ylim[1] - ylim[0]) * 0.008],
            color='#212121',
            linewidth=2.5,
            zorder=200
        )
    
    # Etiquetas
    ax.text(
        escala_x, escala_y - (ylim[1] - ylim[0]) * 0.02,
        '0',
        fontsize=9,
        ha='center',
        va='top',
        color='#212121',
        fontweight='bold',
        zorder=200
    )
    
    ax.text(
        escala_x + dist_100m_grados, escala_y - (ylim[1] - ylim[0]) * 0.02,
        '100 m',
        fontsize=9,
        ha='center',
        va='top',
        color='#212121',
        fontweight='bold',
        zorder=200
    )
    
    print("✅ Elementos cartográficos agregados (norte + escala)")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔟 LEYENDA MINIMALISTA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📊 Agregando leyenda...")
    
    legend_elements = []
    
    # 1. Línea negra - Parcela
    legend_elements.append(
        Line2D([0], [0], color='#212121', linewidth=2.5, label='Límite de la parcela')
    )
    
    # 2. Línea azul - Red hídrica
    if rios_cercanos is not None and len(rios_cercanos) > 0:
        legend_elements.append(
            Line2D([0], [0], color=COLOR_RIO_PRINCIPAL, linewidth=2.0, label='Red hídrica')
        )
    
    # 3. Flecha roja - Distancia
    if len(relaciones) > 0:
        legend_elements.append(
            FancyArrowPatch((0, 0), (0.3, 0), 
                           arrowstyle='->', 
                           color=COLOR_PARCELA,
                           lw=2.0,
                           label='Distancia desde lindero')
        )
    
    # Crear leyenda compacta
    legend = ax.legend(
        handles=legend_elements,
        loc='upper left',
        fontsize=9,
        framealpha=0.98,
        edgecolor='#212121',
        title='LEYENDA',
        title_fontsize=10,
        borderpad=0.6,
        labelspacing=0.5,
        handlelength=2.0,
        handletextpad=0.6,
        frameon=True,
        fancybox=False
    )
    legend.get_frame().set_linewidth(1.5)
    legend.get_frame().set_facecolor('white')
    plt.setp(legend.get_title(), fontweight='bold')
    
    print("✅ Leyenda agregada")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣1️⃣ TÍTULO Y CONFIGURACIÓN FINAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ax.set_title(
        f'Mapa de Influencia Legal Directa\nParcela: {parcela.nombre}',
        fontsize=14,
        fontweight='bold',
        pad=20,
        color='#212121'
    )
    
    ax.axis('off')
    
    # Nota técnica
    nota_tecnica = (
        "Fuente: Cartografía oficial IGAC / IDEAM. Análisis espacial automatizado.\n"
        "Nota: Distancias calculadas desde el lindero de la parcela. Área de consulta: 500 m."
    )
    
    fig.text(
        0.5, 0.02,
        nota_tecnica,
        ha='center',
        va='bottom',
        fontsize=7,
        style='italic',
        color='#616161',
        wrap=True
    )
    
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣2️⃣ GUARDAR MAPA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n💾 Guardando mapa...")
    
    # Buffer (siempre)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    
    # Archivo (opcional)
    if save_to_file:
        if not output_path:
            output_dir = 'test_outputs_mapas'
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_dir, f'mapa_influencia_legal_parcela{parcela.id}_{timestamp}.png')
        
        plt.savefig(output_path, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor='white')
        print(f"✅ Mapa guardado: {output_path}")
    
    plt.close(fig)
    
    print("\n" + "=" * 80)
    print("✅ MAPA DE INFLUENCIA LEGAL DIRECTA GENERADO EXITOSAMENTE")
    print("=" * 80)
    
    return img_buffer

"""
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CÓDIGO BORRADOR COMENTADO - NO USAR
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # 1️⃣2️⃣ LEYENDA CARTOGRÁFICA (OBLIGATORIA)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📊 Agregando leyenda cartográfica...")
    
    from matplotlib.patches import FancyArrowPatch
    
    legend_elements = []
    
    # 1. Línea negra - Parcela analizada
    legend_elements.append(
        Line2D([0], [0], color='#212121', linewidth=2.5, 
               label='Límite de la parcela')
    )
    
    # 2. Línea azul - Red hídrica (si hay ríos cercanos)
    if rios_cercanos is not None and len(rios_cercanos) > 0:
        legend_elements.append(
            Line2D([0], [0], color=COLOR_RIO_PRINCIPAL, linewidth=1.5,
                   label='Red hídrica superficial')
        )
    
    # 3. Flecha roja - Elemento ambiental (si hay relaciones)
    if len(relaciones) > 0:
        # Verificar si hay áreas protegidas u otros elementos ambientales
        tiene_elementos = any(r['tipo'] in ['area_protegida', 'paramo', 'resguardo'] for r in relaciones)
        if tiene_elementos:
            legend_elements.append(
                FancyArrowPatch((0, 0), (0.3, 0), 
                               arrowstyle='->', 
                               color=COLOR_AREA_PROTEGIDA_BORDE,
                               lw=2.0,
                               label='Elemento ambiental')
            )
        
        # 4. Flecha azul - Distancia desde lindero
        legend_elements.append(
            FancyArrowPatch((0, 0), (0.3, 0), 
                           arrowstyle='->', 
                           color=COLOR_RIO_PRINCIPAL,
                           lw=2.0,
                           label='Distancia desde lindero')
        )
    
    # Crear leyenda compacta en la parte inferior
    legend = ax.legend(
        handles=legend_elements,
        loc='lower center',
        fontsize=7.5,
        framealpha=0.98,
        edgecolor='#212121',
        title='LEYENDA',
        title_fontsize=8.5,
        borderpad=0.5,
        labelspacing=0.4,
        handlelength=1.8,
        handletextpad=0.5,
        columnspacing=1.0,
        ncol=len(legend_elements),  # Todos en una fila
        frameon=True,
        fancybox=False,
        bbox_to_anchor=(0.5, -0.02)
    )
    legend.get_frame().set_linewidth(1.2)
    legend.get_frame().set_facecolor('white')
    # Poner título en negrita
    plt.setp(legend.get_title(), fontweight='bold')
    
    print("✅ Leyenda cartográfica agregada")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣3️⃣ TÍTULO Y CONFIGURACIÓN FINAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ax.set_title(
        f'Ubicación de la Parcela a Nivel Municipal\nMunicipio: {municipio_nombre} ({departamento_nombre})',
        fontsize=14,
        fontweight='bold',
        pad=20,
        color='#212121'
    )
    
    # Sin ejes (mapa técnico minimalista)
    ax.axis('off')
    
    # Agregar nota técnica en la parte inferior (bajo la leyenda)
    nota_tecnica = (
        "Fuente: Cartografía oficial IGAC / IDEAM. Análisis espacial automatizado. Fecha de consulta: 2026\n"
        "Nota: Distancias calculadas desde el lindero de la parcela hacia elementos externos identificados. "
        "Área de consulta hídrica: 500 m alrededor de la parcela."
    )
    
    fig.text(
        0.5, 0.01,
        nota_tecnica,
        ha='center',
        va='bottom',
        fontsize=6.5,
        style='italic',
        color='#616161',
        wrap=True
    )
    
    plt.tight_layout(rect=[0, 0.06, 1, 1])  # Dejar espacio para leyenda y nota
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣3️⃣ GUARDAR MAPA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n💾 Guardando mapa de influencia legal...")
    
    # Guardar en buffer (siempre)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    
    # Guardar en archivo (opcional)
    if save_to_file:
        if not output_path:
            output_dir = 'test_outputs_mapas'
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_dir, f'mapa_influencia_legal_parcela{parcela.id}_{timestamp}.png')
        
        plt.savefig(output_path, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor='white')
        print(f"✅ Mapa guardado: {output_path}")
    
    plt.close(fig)
    
    print("\n" + "=" * 80)
    print("✅ MAPA DE INFLUENCIA LEGAL DIRECTA GENERADO EXITOSAMENTE")
    print("=" * 80)
    
    return img_buffer
"""


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
    print("  • generar_mapa_ubicacion_municipal_profesional()")
    print("  • generar_mapa_departamental_profesional()")
    print("\nImportar con: from mapas_profesionales import *")
