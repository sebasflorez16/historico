"""
Generador de Máscaras de Cultivo desde Geometrías de Parcela
============================================================

Módulo para convertir geometrías PostGIS (polígonos) en máscaras booleanas
de arrays NumPy, permitiendo recortar análisis al área real de cultivo.

Autor: AgroTech Engineering Team
Fecha: Enero 2026
"""

import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def generar_mascara_desde_geometria(
    geometria,  # django.contrib.gis.geos.Polygon
    geo_transform: Tuple[float, float, float, float, float, float],
    shape: Tuple[int, int],
    buffer_pixels: int = 0
) -> np.ndarray:
    """
    Genera máscara booleana de cultivo desde geometría de parcela
    
    Args:
        geometria: Objeto GEOSGeometry (Polygon/MultiPolygon) de Django/PostGIS
        geo_transform: Transformación GDAL (origin_x, pixel_width, rotation_x,
                                            origin_y, rotation_y, pixel_height)
        shape: Dimensiones del raster (height, width)
        buffer_pixels: Número de píxeles de buffer interior (negativo = erosión)
    
    Returns:
        Array booleano (True = dentro del cultivo, False = fuera)
    
    Ejemplo:
    --------
    ```python
    from informes.models import Parcela
    from informes.motor_analisis.mascara_cultivo import generar_mascara_desde_geometria
    
    parcela = Parcela.objects.get(id=2)
    
    # Transformación geográfica del raster
    bbox = parcela.geometria.extent  # (min_x, min_y, max_x, max_y)
    width, height = 256, 256
    geo_transform = (
        bbox[0],  # origin_x
        (bbox[2] - bbox[0]) / width,  # pixel_width
        0,  # rotation_x
        bbox[3],  # origin_y
        0,  # rotation_y
        -(bbox[3] - bbox[1]) / height  # pixel_height (negativo)
    )
    
    mascara = generar_mascara_desde_geometria(
        geometria=parcela.geometria,
        geo_transform=geo_transform,
        shape=(height, width)
    )
    
    # Usar en diagnóstico
    diagnostico = ejecutar_diagnostico_unificado(..., mascara_cultivo=mascara)
    ```
    """
    try:
        from shapely.geometry import shape as shapely_shape
        from shapely.geometry.polygon import Polygon as ShapelyPolygon
        from shapely.ops import transform
        import shapely.affinity
        
        logger.info(f"🗺️  Generando máscara de cultivo desde geometría...")
        logger.info(f"   Dimensiones: {shape[0]}x{shape[1]} píxeles")
        
        # Convertir GEOSGeometry a Shapely
        if hasattr(geometria, '__geo_interface__'):
            geojson = geometria.__geo_interface__
            shapely_geom = shapely_shape(geojson)
        else:
            logger.error("❌ Geometría no tiene interfaz GeoJSON")
            return np.ones(shape, dtype=bool)  # Fallback: máscara completa
        
        # Extraer parámetros de transformación
        origin_x = geo_transform[0]
        pixel_width = geo_transform[1]
        origin_y = geo_transform[3]
        pixel_height = geo_transform[5]  # Usualmente negativo
        
        # Crear máscara vacía
        mascara = np.zeros(shape, dtype=bool)
        
        # Recorrer cada píxel y verificar si está dentro del polígono
        height, width = shape
        
        logger.info(f"   Rasterizando polígono...")
        
        for row in range(height):
            for col in range(width):
                # Convertir coordenadas de píxel a geográficas (centro del píxel)
                geo_x = origin_x + (col + 0.5) * pixel_width
                geo_y = origin_y + (row + 0.5) * pixel_height
                
                # Verificar si el punto está dentro del polígono
                try:
                    from shapely.geometry import Point
                    punto = Point(geo_x, geo_y)
                    mascara[row, col] = shapely_geom.contains(punto) or shapely_geom.touches(punto)
                except Exception as e:
                    # En caso de error, asumir que está fuera
                    mascara[row, col] = False
        
        # Aplicar buffer si se requiere
        if buffer_pixels != 0:
            logger.info(f"   Aplicando buffer de {buffer_pixels} píxeles...")
            mascara = aplicar_buffer_morfologico(mascara, buffer_pixels)
        
        # Estadísticas
        pixeles_dentro = np.sum(mascara)
        porcentaje_cultivo = (pixeles_dentro / (height * width)) * 100
        
        logger.info(f"✅ Máscara generada:")
        logger.info(f"   Píxeles dentro del cultivo: {pixeles_dentro} ({porcentaje_cultivo:.1f}%)")
        logger.info(f"   Píxeles fuera del cultivo: {height * width - pixeles_dentro}")
        
        return mascara
        
    except ImportError as e:
        logger.error(f"❌ Shapely no instalado: {str(e)}")
        logger.warning(f"   Retornando máscara completa (sin recorte)")
        return np.ones(shape, dtype=bool)
        
    except Exception as e:
        logger.error(f"❌ Error generando máscara: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.warning(f"   Retornando máscara completa (sin recorte)")
        return np.ones(shape, dtype=bool)


def generar_mascara_desde_bbox_simple(
    bbox: Tuple[float, float, float, float],
    geo_transform: Tuple[float, float, float, float, float, float],
    shape: Tuple[int, int]
) -> np.ndarray:
    """
    Genera máscara rectangular simple desde bounding box
    
    Útil cuando no se tiene geometría compleja o como fallback.
    
    Args:
        bbox: (min_x, min_y, max_x, max_y) en coordenadas geográficas
        geo_transform: Transformación GDAL
        shape: Dimensiones del raster (height, width)
    
    Returns:
        Array booleano con True en área del bbox
    """
    logger.info(f"🗺️  Generando máscara simple desde bbox...")
    
    origin_x = geo_transform[0]
    pixel_width = geo_transform[1]
    origin_y = geo_transform[3]
    pixel_height = geo_transform[5]
    
    height, width = shape
    mascara = np.zeros(shape, dtype=bool)
    
    # Convertir bbox a coordenadas de píxel
    col_min = int((bbox[0] - origin_x) / pixel_width)
    col_max = int((bbox[2] - origin_x) / pixel_width)
    row_min = int((bbox[3] - origin_y) / pixel_height)  # max_y (norte)
    row_max = int((bbox[1] - origin_y) / pixel_height)  # min_y (sur)
    
    # Clip a límites del raster
    col_min = max(0, min(col_min, width - 1))
    col_max = max(0, min(col_max, width - 1))
    row_min = max(0, min(row_min, height - 1))
    row_max = max(0, min(row_max, height - 1))
    
    # Rellenar máscara
    mascara[row_min:row_max+1, col_min:col_max+1] = True
    
    pixeles_dentro = np.sum(mascara)
    logger.info(f"✅ Máscara simple generada: {pixeles_dentro} píxeles ({pixeles_dentro / (height * width) * 100:.1f}%)")
    
    return mascara


def aplicar_buffer_morfologico(
    mascara: np.ndarray,
    buffer_pixels: int
) -> np.ndarray:
    """
    Aplica erosión/dilatación morfológica a la máscara
    
    Args:
        mascara: Máscara booleana original
        buffer_pixels: > 0 = dilatación (expandir), < 0 = erosión (contraer)
    
    Returns:
        Máscara modificada
    """
    try:
        import cv2
        
        # Convertir a uint8
        mascara_uint8 = (mascara * 255).astype(np.uint8)
        
        # Crear kernel
        kernel_size = abs(buffer_pixels)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # Aplicar operación morfológica
        if buffer_pixels > 0:
            # Dilatación (expandir)
            mascara_procesada = cv2.dilate(mascara_uint8, kernel, iterations=1)
        else:
            # Erosión (contraer)
            mascara_procesada = cv2.erode(mascara_uint8, kernel, iterations=1)
        
        return mascara_procesada > 0
        
    except ImportError:
        logger.warning("⚠️  OpenCV no disponible, buffer morfológico ignorado")
        return mascara
    except Exception as e:
        logger.error(f"❌ Error aplicando buffer: {str(e)}")
        return mascara


def calcular_area_mascara(
    mascara: np.ndarray,
    resolucion_pixel_m: float = 10.0
) -> float:
    """
    Calcula área real de la máscara en hectáreas
    
    Args:
        mascara: Máscara booleana
        resolucion_pixel_m: Tamaño de pixel en metros
    
    Returns:
        Área en hectáreas
    """
    pixeles = np.sum(mascara)
    area_m2 = pixeles * (resolucion_pixel_m ** 2)
    area_ha = area_m2 / 10000.0
    
    return area_ha


def validar_coherencia_mascara(
    mascara: np.ndarray,
    area_esperada_ha: float,
    resolucion_pixel_m: float = 10.0,
    tolerancia_pct: float = 10.0
) -> bool:
    """
    Valida que el área de la máscara sea coherente con el área esperada
    
    Args:
        mascara: Máscara generada
        area_esperada_ha: Área esperada en hectáreas (de parcela.area_hectareas)
        resolucion_pixel_m: Resolución del píxel
        tolerancia_pct: Tolerancia permitida en porcentaje
    
    Returns:
        True si la máscara es coherente, False si hay discrepancias
    """
    area_calculada = calcular_area_mascara(mascara, resolucion_pixel_m)
    diferencia_pct = abs((area_calculada - area_esperada_ha) / area_esperada_ha) * 100
    
    logger.info(f"🔍 Validación de máscara:")
    logger.info(f"   Área calculada: {area_calculada:.2f} ha")
    logger.info(f"   Área esperada: {area_esperada_ha:.2f} ha")
    logger.info(f"   Diferencia: {diferencia_pct:.1f}%")
    
    if diferencia_pct > tolerancia_pct:
        logger.warning(f"⚠️  Diferencia de área ({diferencia_pct:.1f}%) supera tolerancia ({tolerancia_pct}%)")
        return False
    else:
        logger.info(f"✅ Máscara coherente (diferencia {diferencia_pct:.1f}% < {tolerancia_pct}%)")
        return True


# ============================================================================
# INTEGRACIÓN CON GENERADOR PDF
# ============================================================================

def obtener_mascara_cultivo_para_diagnostico(
    parcela,  # informes.models.Parcela
    geo_transform: Tuple,
    shape: Tuple[int, int],
    usar_simple_si_falla: bool = True
) -> Optional[np.ndarray]:
    """
    Función de alto nivel para obtener máscara de cultivo en generador_pdf.py
    
    Args:
        parcela: Objeto Parcela de Django
        geo_transform: Transformación geográfica
        shape: Dimensiones del raster
        usar_simple_si_falla: Si falla generación compleja, usar bbox simple
    
    Returns:
        Máscara booleana o None si no se pudo generar
    
    Uso en generador_pdf.py:
    ------------------------
    ```python
    from informes.motor_analisis.mascara_cultivo import obtener_mascara_cultivo_para_diagnostico
    
    mascara = obtener_mascara_cultivo_para_diagnostico(
        parcela=parcela,
        geo_transform=geo_transform,
        shape=(256, 256)
    )
    
    diagnostico = ejecutar_diagnostico_unificado(
        ...,
        mascara_cultivo=mascara
    )
    ```
    """
    try:
        # Intentar generar desde geometría completa
        if hasattr(parcela, 'geometria') and parcela.geometria:
            logger.info(f"📍 Generando máscara desde geometría de parcela #{parcela.id}...")
            mascara = generar_mascara_desde_geometria(
                geometria=parcela.geometria,
                geo_transform=geo_transform,
                shape=shape
            )
            
            # Validar coherencia
            if parcela.area_hectareas:
                es_coherente = validar_coherencia_mascara(
                    mascara=mascara,
                    area_esperada_ha=parcela.area_hectareas,
                    tolerancia_pct=15.0  # 15% de tolerancia
                )
                
                if not es_coherente and usar_simple_si_falla:
                    logger.warning("⚠️  Máscara no coherente, usando bbox simple...")
                    bbox = parcela.geometria.extent
                    mascara = generar_mascara_desde_bbox_simple(bbox, geo_transform, shape)
            
            return mascara
        
        # Fallback: Usar bbox si existe
        elif hasattr(parcela, 'geometria') and parcela.geometria:
            logger.warning("⚠️  Usando bbox simple como fallback...")
            bbox = parcela.geometria.extent
            return generar_mascara_desde_bbox_simple(bbox, geo_transform, shape)
        
        else:
            logger.warning("⚠️  Parcela sin geometría, no se puede generar máscara")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo máscara de cultivo: {str(e)}")
        
        if usar_simple_si_falla:
            try:
                logger.warning("   Intentando bbox simple...")
                bbox = parcela.geometria.extent
                return generar_mascara_desde_bbox_simple(bbox, geo_transform, shape)
            except:
                return None
        
        return None
