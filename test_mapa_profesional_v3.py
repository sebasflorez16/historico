#!/usr/bin/env python
"""
🧪 TEST: Generación de Mapa Municipal Profesional con Mejoras V3

Este script prueba la nueva versión refinada del Mapa 1 (Ubicación Municipal)
con todas las mejoras visuales y técnicas implementadas:

✅ Jerarquía visual mejorada (límite municipal dominante)
✅ Red hídrica jerarquizada (principales vs secundarios)
✅ Etiquetado inteligente (dentro del marco, con halo)
✅ Encuadre optimizado
✅ Leyenda profesional
✅ Bloque de fuentes legales

Parcela de prueba: Parcela 6 (id=6) en Yopal, Casanare
"""

import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from detector_geografico import DetectorGeografico
from mapas_profesionales import *
from shapely import wkt
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

def generar_mapa_profesional_v3(parcela_id=6):
    """
    Genera el mapa municipal profesional con todas las mejoras V3
    
    Args:
        parcela_id: ID de la parcela a mapear
    """
    print("━" * 80)
    print("🗺️  GENERACIÓN DE MAPA MUNICIPAL PROFESIONAL V3")
    print("━" * 80)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ CARGAR PARCELA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        print(f"\n✅ Parcela cargada: {parcela.nombre}")
        print(f"   Propietario: {parcela.propietario}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
    except Parcela.DoesNotExist:
        print(f"❌ No existe la parcela con ID {parcela_id}")
        return None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ DETECCIÓN GEOGRÁFICA AUTOMÁTICA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🌍 PASO 1: Detección geográfica automática...")
    detector = DetectorGeografico()
    ubicacion = detector.proceso_completo(parcela.geometria)
    
    if ubicacion['departamento'] is None or ubicacion['municipio'] is None:
        print("❌ No se pudo detectar la ubicación de la parcela")
        return None
    
    departamento_nombre = ubicacion['departamento']
    municipio_nombre = ubicacion['municipio']
    municipio_gdf = ubicacion['municipio_gdf']
    red_hidrica_municipal = ubicacion.get('red_hidrica', None)
    centroide = ubicacion['centroide']
    
    print(f"✅ Ubicación detectada: {municipio_nombre}, {departamento_nombre}")
    print(f"   Coordenadas: {centroide.y:.6f}°N, {abs(centroide.x):.6f}°W")
    
    # Convertir parcela a GeoDataFrame
    if hasattr(parcela.geometria, 'wkt'):
        parcela_geom = wkt.loads(parcela.geometria.wkt)
    else:
        parcela_geom = parcela.geometria
    parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3️⃣ CREAR FIGURA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🎨 PASO 2: Creando figura del mapa...")
    fig, ax = plt.subplots(figsize=FIGSIZE_MAPA)
    ax.set_facecolor(COLOR_FONDO)
    fig.patch.set_facecolor(COLOR_FONDO)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4️⃣ DIBUJAR LÍMITE MUNICIPAL (con jerarquía visual mejorada)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🏛️  PASO 3: Dibujando límite municipal profesional...")
    dibujar_limite_municipal_profesional(ax, municipio_gdf)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5️⃣ DIBUJAR RED HÍDRICA JERARQUIZADA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🌊 PASO 4: Dibujando red hídrica jerarquizada...")
    num_principales, num_secundarios = dibujar_red_hidrica_jerarquizada(ax, red_hidrica_municipal)
    num_rios_total = num_principales + num_secundarios
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6️⃣ DIBUJAR PARCELA (destacada)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📍 PASO 5: Dibujando parcela destacada...")
    
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
    
    print("✅ Parcela dibujada con alta visibilidad")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7️⃣ AJUSTAR ZOOM Y ENCUADRE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🔍 PASO 6: Ajustando zoom y encuadre...")
    municipio_bounds = municipio_gdf.total_bounds
    dx = (municipio_bounds[2] - municipio_bounds[0]) * MARGEN_MUNICIPIO_PCT
    dy = (municipio_bounds[3] - municipio_bounds[1]) * MARGEN_MUNICIPIO_PCT
    
    xlim = (municipio_bounds[0] - dx, municipio_bounds[2] + dx)
    ylim = (municipio_bounds[1] - dy, municipio_bounds[3] + dy)
    
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    print(f"✅ Encuadre: {xlim[1]-xlim[0]:.4f}° x {ylim[1]-ylim[0]:.4f}°")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 8️⃣ ETIQUETAR RÍOS INTELIGENTEMENTE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🏷️  PASO 7: Etiquetando ríos principales...")
    num_etiquetados = etiquetar_rios_inteligente(ax, red_hidrica_municipal, xlim, ylim)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 9️⃣ ELEMENTOS CARTOGRÁFICOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🧭 PASO 8: Agregando elementos cartográficos...")
    
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
    
    # B) Escala gráfica (simplificada)
    escala_km = 2 if (xlim[1] - xlim[0]) < 0.5 else 5
    x_escala = xlim[0] + (xlim[1] - xlim[0]) * 0.15
    y_escala = ylim[0] + (ylim[1] - ylim[0]) * 0.08
    long_barra = escala_km / 111  # Aproximado para Colombia
    
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
    
    print("✅ Norte y escala agregados")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔟 TÍTULO Y ETIQUETAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📝 PASO 9: Agregando título y etiquetas...")
    
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
    
    print("✅ Título y etiquetas agregadas")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣1️⃣ LEYENDA PROFESIONAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📊 PASO 10: Agregando leyenda profesional...")
    agregar_leyenda_profesional(ax, municipio_gdf, parcela_gdf, num_rios_total)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣2️⃣ GUARDAR MAPA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n💾 PASO 11: Guardando mapa...")
    
    plt.tight_layout()
    
    # Crear directorio de salida
    output_dir = 'test_outputs_mapas'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'mapa_profesional_v3_parcela{parcela_id}_{timestamp}.png')
    
    plt.savefig(output_path, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor=COLOR_FONDO)
    print(f"✅ Mapa guardado: {output_path}")
    
    # También guardar en buffer para PDF
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=DPI_MAPA, bbox_inches='tight', facecolor=COLOR_FONDO)
    img_buffer.seek(0)
    
    plt.close(fig)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣3️⃣ RESUMEN FINAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "━" * 80)
    print("📊 RESUMEN DE GENERACIÓN")
    print("━" * 80)
    print(f"Parcela:              {parcela.nombre}")
    print(f"Ubicación:            {municipio_nombre}, {departamento_nombre}")
    print(f"Coordenadas:          {centroide.y:.6f}°N, {abs(centroide.x):.6f}°W")
    print(f"Ríos dibujados:       {num_rios_total} ({num_principales} principales, {num_secundarios} secundarios)")
    print(f"Ríos etiquetados:     {num_etiquetados}")
    print(f"Resolución:           {DPI_MAPA} DPI")
    print(f"Tamaño:               {FIGSIZE_MAPA[0]}x{FIGSIZE_MAPA[1]} pulgadas")
    print(f"Archivo generado:     {output_path}")
    print("━" * 80)
    print("\n✅ MAPA PROFESIONAL V3 GENERADO EXITOSAMENTE")
    
    return img_buffer, output_path


if __name__ == '__main__':
    print("\n🧪 TEST: Mapa Municipal Profesional V3")
    print("=" * 80)
    
    # Generar mapa
    resultado = generar_mapa_profesional_v3(parcela_id=6)
    
    if resultado:
        img_buffer, output_path = resultado
        
        # Generar también el bloque de fuentes legales
        print("\n📚 Generando bloque de fuentes legales...")
        tabla_fuentes = agregar_bloque_fuentes_legales()
        print("✅ Bloque de fuentes legales creado")
        print("\nPara añadirlo al PDF, usar:")
        print("   elementos.append(tabla_fuentes)")
        print("   elementos.append(Spacer(1, 0.3*cm))")
        
        print("\n" + "=" * 80)
        print(f"🎉 TEST COMPLETADO - Ver resultado en: {output_path}")
        print("=" * 80)
    else:
        print("\n❌ Error al generar el mapa")
