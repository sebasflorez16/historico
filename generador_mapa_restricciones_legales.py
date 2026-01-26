"""
Generador de Mapa de Restricciones Legales
Visualización geográfica de restricciones ambientales/legales sobre parcelas
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MPLPolygon, Circle
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon, Point
import numpy as np


def generar_mapa_restricciones_legales(
    geometria_parcela,  # Django GEOS Polygon
    restricciones: List[Dict],  # Lista de restricciones encontradas
    verificacion_completa: Dict,  # Resultado completo de verificación
    output_dir: Path,
    parcela_nombre: str = "Parcela",
    fuentes_hidricas_gdf: Optional[gpd.GeoDataFrame] = None,  # NUEVO: Red hídrica cercana
    metadata_fuente: Optional[Dict] = None  # NUEVO: Metadata de la fuente de datos
) -> Optional[Path]:
    """
    Genera mapa visual de restricciones legales sobre la parcela
    
    Muestra:
    - Polígono de la parcela
    - FUENTES HÍDRICAS REALES (ríos/quebradas en azul) - NUEVO
    - Buffers de retiro hídrico (30m, 100m)
    - Áreas protegidas superpuestas
    - Resguardos indígenas si aplica
    - Páramos si aplica
    - Coordenadas GPS en las esquinas
    - Metadata de fuente de datos - NUEVO
    
    Args:
        geometria_parcela: Geometría Django GEOS de la parcela
        restricciones: Lista de restricciones encontradas con geometrías de fuentes
        verificacion_completa: Dict con resultado completo
        output_dir: Directorio de salida
        parcela_nombre: Nombre de la parcela para el título
        fuentes_hidricas_gdf: GeoDataFrame con red hídrica cercana (NUEVO)
        metadata_fuente: Dict con metadata de la fuente de datos (NUEVO)
        
    Returns:
        Path al archivo PNG generado o None si falla
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ===== CONVERTIR GEOMETRÍA A SHAPELY =====
        from shapely import wkt
        
        if hasattr(geometria_parcela, 'wkt'):
            geom_parcela = wkt.loads(geometria_parcela.wkt)
        else:
            print("⚠️ No se pudo convertir geometría de parcela")
            return None
            
        # ===== CONFIGURACIÓN DE FIGURA =====
        fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
        ax.set_facecolor('#FAFAFA')  # Fondo gris muy claro
        
        # ===== CALCULAR BOUNDS DE LA PARCELA =====
        minx, miny, maxx, maxy = geom_parcela.bounds
        
        # Buffer para visualización (agregar 10% de margen)
        width = maxx - minx
        height = maxy - miny
        buffer_x = width * 0.15
        buffer_y = height * 0.15
        
        # ===== DIBUJAR POLÍGONO DE LA PARCELA (BASE) =====
        if isinstance(geom_parcela, Polygon):
            polygons = [geom_parcela]
        elif isinstance(geom_parcela, MultiPolygon):
            polygons = list(geom_parcela.geoms)
        else:
            polygons = []
            
        for poly in polygons:
            coords = list(poly.exterior.coords)
            xs, ys = zip(*coords)
            
            # Dibujar parcela en verde claro con borde sólido
            polygon_patch = MPLPolygon(
                coords,
                closed=True,
                edgecolor='#27AE60',  # Verde oscuro
                facecolor='#D5F4E6',  # Verde muy claro
                linewidth=3,
                zorder=5,
                alpha=0.5
            )
            ax.add_patch(polygon_patch)
        
        # ===== DIBUJAR FUENTES HÍDRICAS REALES (NUEVO) =====
        if fuentes_hidricas_gdf is not None and len(fuentes_hidricas_gdf) > 0:
            for idx, fuente in fuentes_hidricas_gdf.iterrows():
                geom = fuente.geometry
                
                if geom.geom_type in ['LineString', 'MultiLineString']:
                    # Dibujar ríos/quebradas como líneas azules
                    if geom.geom_type == 'LineString':
                        coords = list(geom.coords)
                        xs, ys = zip(*coords)
                        ax.plot(
                            xs, ys,
                            color='#3498DB',  # Azul agua
                            linewidth=2.5,
                            linestyle='-',
                            zorder=15,
                            label='_nolegend_' if idx > 0 else 'Red hídrica'
                        )
                    else:  # MultiLineString
                        for line in geom.geoms:
                            coords = list(line.coords)
                            xs, ys = zip(*coords)
                            ax.plot(
                                xs, ys,
                                color='#3498DB',
                                linewidth=2.5,
                                linestyle='-',
                                zorder=15,
                                label='_nolegend_'
                            )
                    
                    # Agregar etiqueta con nombre de la fuente
                    centroid = geom.centroid
                    nombre_fuente = fuente.get('NOMBRE', fuente.get('nombre', ''))
                    if nombre_fuente and str(nombre_fuente) != 'None':
                        ax.text(
                            centroid.x, centroid.y,
                            nombre_fuente[:25],
                            fontsize=8,
                            color='#2C3E50',
                            bbox=dict(
                                boxstyle='round,pad=0.3',
                                facecolor='white',
                                edgecolor='#3498DB',
                                alpha=0.8
                            ),
                            zorder=20
                        )
                elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                    # ⚠️ Si es polígono, marcarlo en amarillo (datos incorrectos)
                    if geom.geom_type == 'Polygon':
                        polys = [geom]
                    else:
                        polys = list(geom.geoms)
                    
                    for poly in polys:
                        coords = list(poly.exterior.coords)
                        warning_patch = MPLPolygon(
                            coords,
                            closed=True,
                            edgecolor='#F39C12',
                            facecolor='#FEF5E7',
                            linewidth=2,
                            linestyle='--',
                            zorder=8,
                            alpha=0.3
                        )
                        ax.add_patch(warning_patch)
                    
                    # Advertencia visual
                    ax.text(
                        (minx + maxx) / 2,
                        miny + buffer_y * 0.05,
                        '⚠️ ADVERTENCIA: Datos de zonificación (polígonos), NO red de drenaje',
                        fontsize=10,
                        fontweight='bold',
                        ha='center',
                        color='#D68910',
                        bbox=dict(
                            boxstyle='round,pad=0.5',
                            facecolor='#FEF5E7',
                            edgecolor='#F39C12',
                            linewidth=2
                        ),
                        zorder=100
                    )
        
        # ===== DIBUJAR RESTRICCIONES (BUFFERS) =====
        restricciones_dibujadas = []
        
        for restriccion in restricciones:
            tipo = restriccion.get('tipo', '')
            nombre = restriccion.get('nombre', 'Sin nombre')
            area_ha = restriccion.get('area_afectada_ha', 0)
            severidad = restriccion.get('severidad', 'MEDIA')
            
            # ===== RETIROS HÍDRICOS =====
            if tipo == 'retiro_hidrico':
                subtipo = restriccion.get('subtipo', 'quebrada')
                retiro_m = restriccion.get('retiro_minimo_m', 30)
                distancia_m = restriccion.get('distancia_real_m', None)  # NUEVO
                
                # Color según severidad
                if severidad == 'ALTA' or retiro_m >= 100:
                    color = '#E74C3C'  # Rojo intenso
                    alpha = 0.4
                elif retiro_m >= 50:
                    color = '#F39C12'  # Naranja
                    alpha = 0.35
                else:
                    color = '#F4D03F'  # Amarillo
                    alpha = 0.3
                
                # Crear buffer aproximado sobre la parcela
                # (La lógica real está en verificador_legal.py, aquí solo visualizamos)
                buffer_geom = geom_parcela.buffer(0.0003)  # ~30m aprox
                
                if isinstance(buffer_geom, (Polygon, MultiPolygon)):
                    if isinstance(buffer_geom, Polygon):
                        buffer_polys = [buffer_geom]
                    else:
                        buffer_polys = list(buffer_geom.geoms)
                    
                    for buf_poly in buffer_polys:
                        coords = list(buf_poly.exterior.coords)
                        buffer_patch = MPLPolygon(
                            coords,
                            closed=True,
                            edgecolor=color,
                            facecolor=color,
                            linewidth=2,
                            linestyle='--',
                            zorder=10,
                            alpha=alpha
                        )
                        ax.add_patch(buffer_patch)
                
                restricciones_dibujadas.append({
                    'tipo': f'Retiro hídrico ({retiro_m}m)',
                    'color': color,
                    'area_ha': area_ha
                })
            
            # ===== ÁREAS PROTEGIDAS =====
            elif tipo == 'area_protegida':
                color = '#8E44AD'  # Púrpura
                alpha = 0.35
                
                # Dibujar zona superpuesta
                buffer_geom = geom_parcela.buffer(0.0001)
                if isinstance(buffer_geom, (Polygon, MultiPolygon)):
                    if isinstance(buffer_geom, Polygon):
                        buffer_polys = [buffer_geom]
                    else:
                        buffer_polys = list(buffer_geom.geoms)
                    
                    for buf_poly in buffer_polys:
                        coords = list(buf_poly.exterior.coords)
                        ap_patch = MPLPolygon(
                            coords,
                            closed=True,
                            edgecolor=color,
                            facecolor=color,
                            linewidth=2,
                            linestyle='-.',
                            zorder=12,
                            alpha=alpha
                        )
                        ax.add_patch(ap_patch)
                
                restricciones_dibujadas.append({
                    'tipo': f'Área Protegida: {nombre[:30]}',
                    'color': color,
                    'area_ha': area_ha
                })
            
            # ===== RESGUARDOS INDÍGENAS =====
            elif tipo == 'resguardo_indigena':
                color = '#D68910'  # Naranja tierra
                alpha = 0.3
                
                buffer_geom = geom_parcela.buffer(0.0002)
                if isinstance(buffer_geom, (Polygon, MultiPolygon)):
                    if isinstance(buffer_geom, Polygon):
                        buffer_polys = [buffer_geom]
                    else:
                        buffer_polys = list(buffer_geom.geoms)
                    
                    for buf_poly in buffer_polys:
                        coords = list(buf_poly.exterior.coords)
                        ri_patch = MPLPolygon(
                            coords,
                            closed=True,
                            edgecolor=color,
                            facecolor=color,
                            linewidth=2,
                            linestyle=':',
                            zorder=11,
                            alpha=alpha
                        )
                        ax.add_patch(ri_patch)
                
                restricciones_dibujadas.append({
                    'tipo': f'Resguardo: {nombre[:30]}',
                    'color': color,
                    'area_ha': area_ha
                })
            
            # ===== PÁRAMOS =====
            elif tipo == 'paramo':
                color = '#5DADE2'  # Azul claro
                alpha = 0.35
                
                buffer_geom = geom_parcela.buffer(0.00015)
                if isinstance(buffer_geom, (Polygon, MultiPolygon)):
                    if isinstance(buffer_geom, Polygon):
                        buffer_polys = [buffer_geom]
                    else:
                        buffer_polys = list(buffer_geom.geoms)
                    
                    for buf_poly in buffer_polys:
                        coords = list(buf_poly.exterior.coords)
                        p_patch = MPLPolygon(
                            coords,
                            closed=True,
                            edgecolor=color,
                            facecolor=color,
                            linewidth=2,
                            linestyle='-',
                            zorder=13,
                            alpha=alpha
                        )
                        ax.add_patch(p_patch)
                
                restricciones_dibujadas.append({
                    'tipo': f'Páramo: {nombre[:30]}',
                    'color': color,
                    'area_ha': area_ha
                })
        
        # ===== COORDENADAS GPS EN LAS ESQUINAS =====
        # Esquina superior izquierda
        ax.text(
            minx + buffer_x * 0.3,
            maxy - buffer_y * 0.3,
            f'{maxy:.6f}°N\n{minx:.6f}°W',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#34495E', alpha=0.9),
            ha='left',
            va='top',
            zorder=50
        )
        
        # Esquina superior derecha
        ax.text(
            maxx - buffer_x * 0.3,
            maxy - buffer_y * 0.3,
            f'{maxy:.6f}°N\n{maxx:.6f}°W',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#34495E', alpha=0.9),
            ha='right',
            va='top',
            zorder=50
        )
        
        # Esquina inferior izquierda
        ax.text(
            minx + buffer_x * 0.3,
            miny + buffer_y * 0.3,
            f'{miny:.6f}°N\n{minx:.6f}°W',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#34495E', alpha=0.9),
            ha='left',
            va='bottom',
            zorder=50
        )
        
        # Esquina inferior derecha
        ax.text(
            maxx - buffer_x * 0.3,
            miny + buffer_y * 0.3,
            f'{miny:.6f}°N\n{maxx:.6f}°W',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#34495E', alpha=0.9),
            ha='right',
            va='bottom',
            zorder=50
        )
        
        # ===== LEYENDA =====
        leyenda_patches = []
        
        # Parcela
        leyenda_patches.append(
            mpatches.Patch(
                facecolor='#D5F4E6',
                edgecolor='#27AE60',
                linewidth=2,
                label=f'Parcela ({verificacion_completa.get("area_total_ha", 0):.2f} ha)'
            )
        )
        
        # Restricciones encontradas
        for rest in restricciones_dibujadas[:6]:  # Máximo 6 para no saturar
            leyenda_patches.append(
                mpatches.Patch(
                    facecolor=rest['color'],
                    edgecolor=rest['color'],
                    alpha=0.5,
                    label=f'{rest["tipo"]} ({rest["area_ha"]:.2f} ha)'
                )
            )
        
        if leyenda_patches:
            ax.legend(
                handles=leyenda_patches,
                loc='upper right',
                fontsize=10,
                framealpha=0.95,
                edgecolor='#2C3E50',
                title='Restricciones Detectadas',
                title_fontsize=11,
                bbox_to_anchor=(0.98, 0.98)
            )
        
        # ===== TÍTULO =====
        cumple = verificacion_completa.get('cumple_normativa', False)
        area_cultivable = verificacion_completa.get('area_cultivable_ha', 0)
        area_restringida = verificacion_completa.get('area_restringida_ha', 0)
        
        if cumple:
            titulo_color = '#27AE60'
            estado = '✅ SIN RESTRICCIONES'
        else:
            titulo_color = '#E74C3C'
            estado = f'⚠️ {len(restricciones)} RESTRICCIONES DETECTADAS'
        
        ax.text(
            (minx + maxx) / 2,
            maxy + buffer_y * 0.7,
            f'MAPA DE RESTRICCIONES LEGALES - {parcela_nombre}',
            fontsize=16,
            fontweight='bold',
            ha='center',
            va='top',
            color='#2C3E50',
            zorder=100
        )
        
        ax.text(
            (minx + maxx) / 2,
            maxy + buffer_y * 0.4,
            estado,
            fontsize=13,
            fontweight='bold',
            ha='center',
            va='top',
            color=titulo_color,
            zorder=100
        )
        
        # NUEVO: Manejar area_cultivable como estructura o valor
        if isinstance(area_cultivable, dict):
            if area_cultivable['determinable']:
                texto_area_cultivable = f"{area_cultivable['valor_ha']:.2f} ha (preliminar)"
            else:
                texto_area_cultivable = "NO DETERMINABLE"
        else:
            texto_area_cultivable = f"{area_cultivable:.2f} ha"
        
        ax.text(
            (minx + maxx) / 2,
            maxy + buffer_y * 0.15,
            f'Área cultivable: {texto_area_cultivable} | Área restringida: {area_restringida:.2f} ha',
            fontsize=11,
            ha='center',
            va='top',
            color='#34495E',
            zorder=100
        )
        
        # ===== CUADRO DE METADATA (NUEVO) =====
        if metadata_fuente:
            fecha_dato = metadata_fuente.get('fecha', 'N/A')
            fuente_nombre = metadata_fuente.get('fuente', 'Datos oficiales gobierno Colombia')
            precision = metadata_fuente.get('precision', '±10m')
            autoridad = metadata_fuente.get('autoridad', 'IGAC/IDEAM')
            tipo_dato = metadata_fuente.get('tipo_dato', 'Red hídrica')
            num_elementos = metadata_fuente.get('num_elementos_cercanos', 0)
            
            metadata_text = f"""METADATA DEL MAPA
Fuente: {fuente_nombre}
Tipo: {tipo_dato}
Fecha descarga: {fecha_dato}
Autoridad: {autoridad}
Elementos cercanos: {num_elementos}
CRS: EPSG:4326 (WGS84)
Precisión: {precision}"""
            
            ax.text(
                minx + buffer_x * 0.02,
                miny - buffer_y * 0.7,
                metadata_text,
                fontsize=7,
                ha='left',
                va='bottom',
                color='#34495E',
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    facecolor='white',
                    edgecolor='#34495E',
                    linewidth=1,
                    alpha=0.95
                ),
                zorder=100,
                family='monospace'
            )
        
        # ===== CONFIGURACIÓN FINAL =====
        ax.set_xlim(minx - buffer_x, maxx + buffer_x)
        ax.set_ylim(miny - buffer_y, maxy + buffer_y)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, color='#BDC3C7')
        ax.set_xlabel('Longitud (grados)', fontsize=10, color='#34495E')
        ax.set_ylabel('Latitud (grados)', fontsize=10, color='#34495E')
        
        # ===== GUARDAR =====
        output_path = output_dir / f'mapa_restricciones_legales_{parcela_nombre.replace(" ", "_")}.png'
        plt.tight_layout()
        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        plt.close(fig)
        
        print(f"✅ Mapa de restricciones guardado: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error generando mapa de restricciones: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    """Test rápido con parcela real"""
    import os
    import sys
    import django
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
    django.setup()
    
    from informes.models import Parcela
    from pathlib import Path
    
    # Usar parcela de prueba
    parcela = Parcela.objects.get(id=1)
    
    # Crear restricciones de ejemplo (normalmente vendrían del verificador)
    restricciones_ejemplo = [
        {
            'tipo': 'retiro_hidrico',
            'subtipo': 'quebrada',
            'retiro_minimo_m': 30,
            'area_afectada_ha': 69.82,
            'nombre': 'Quebrada Sin Nombre',
            'severidad': 'ALTA'
        }
    ]
    
    verificacion_ejemplo = {
        'area_total_ha': 69.82,
        'area_cultivable_ha': 0.00,
        'area_restringida_ha': 69.82,
        'cumple_normativa': False,
        'restricciones_encontradas': restricciones_ejemplo
    }
    
    # Generar mapa
    output_dir = Path('/Users/sebastianflorez/Documents/Historico Agrotech/historico/media/temp')
    mapa_path = generar_mapa_restricciones_legales(
        geometria_parcela=parcela.geometria,
        restricciones=restricciones_ejemplo,
        verificacion_completa=verificacion_ejemplo,
        output_dir=output_dir,
        parcela_nombre=parcela.nombre
    )
    
    if mapa_path:
        print(f"\n✅ Mapa generado exitosamente: {mapa_path}")
        print(f"📏 Tamaño: {os.path.getsize(mapa_path) / 1024:.1f} KB")
    else:
        print("\n❌ No se pudo generar el mapa")
