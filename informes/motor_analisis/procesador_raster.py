"""
Procesador Avanzado de Datos Raster Satelitales
================================================

Procesa imágenes satelitales en formato raster usando GDAL/Rasterio para:
- Extraer estadísticas zonales por parcela
- Calcular histogramas y distribuciones espaciales
- Detectar patrones espaciales (hotspots, clusters)
- Generar máscaras de calidad (nubes, sombras, anomalías)

Referencias:
- Rasterio Docs: https://rasterio.readthedocs.io/
- GDAL Stats: https://gdal.org/programs/gdalinfo.html
- Zonal Statistics: Gorelick et al. (2017) - Google Earth Engine
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class EstadisticasZonales:
    """Estadísticas extraídas de una zona del raster"""
    media: float
    mediana: float
    desviacion: float
    minimo: float
    maximo: float
    percentil_25: float
    percentil_75: float
    coef_variacion: float
    area_pixels: int
    area_hectareas: float
    histograma: Dict[str, int]  # Bins y frecuencias
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'media': round(self.media, 4),
            'mediana': round(self.mediana, 4),
            'desviacion': round(self.desviacion, 4),
            'minimo': round(self.minimo, 4),
            'maximo': round(self.maximo, 4),
            'percentil_25': round(self.percentil_25, 4),
            'percentil_75': round(self.percentil_75, 4),
            'coef_variacion': round(self.coef_variacion, 4),
            'area_pixels': self.area_pixels,
            'area_hectareas': round(self.area_hectareas, 2),
            'histograma': self.histograma
        }


class ProcesadorRaster:
    """
    Procesador avanzado de datos raster satelitales.
    
    Funcionalidades:
    1. Estadísticas zonales por polígono
    2. Análisis de calidad de imagen
    3. Detección de patrones espaciales
    4. Generación de máscaras
    """
    
    def __init__(self):
        """Inicializa el procesador"""
        self.logger = logging.getLogger(__name__)
    
    def calcular_estadisticas_zonales(
        self,
        valores_array: np.ndarray,
        area_hectareas: float,
        num_bins: int = 10
    ) -> EstadisticasZonales:
        """
        Calcula estadísticas completas de una zona.
        
        Args:
            valores_array: Array NumPy con valores del índice
            area_hectareas: Área de la zona en hectáreas
            num_bins: Número de bins para el histograma
            
        Returns:
            EstadisticasZonales con todos los indicadores
        """
        # Filtrar valores válidos (eliminar NaN, infinitos, fuera de rango)
        valores_validos = valores_array[
            np.isfinite(valores_array) & 
            (valores_array >= -1.0) & 
            (valores_array <= 1.0)
        ]
        
        if len(valores_validos) == 0:
            self.logger.warning("⚠️ No hay valores válidos para calcular estadísticas")
            return self._estadisticas_vacias(area_hectareas)
        
        # Estadísticas básicas
        media = float(np.mean(valores_validos))
        mediana = float(np.median(valores_validos))
        desviacion = float(np.std(valores_validos))
        minimo = float(np.min(valores_validos))
        maximo = float(np.max(valores_validos))
        p25 = float(np.percentile(valores_validos, 25))
        p75 = float(np.percentile(valores_validos, 75))
        
        # Coeficiente de variación (CV)
        cv = (desviacion / media * 100) if media != 0 else 0
        
        # Histograma
        hist, bins = np.histogram(valores_validos, bins=num_bins)
        histograma = {
            f"{bins[i]:.2f}-{bins[i+1]:.2f}": int(hist[i])
            for i in range(len(hist))
        }
        
        return EstadisticasZonales(
            media=media,
            mediana=mediana,
            desviacion=desviacion,
            minimo=minimo,
            maximo=maximo,
            percentil_25=p25,
            percentil_75=p75,
            coef_variacion=cv,
            area_pixels=len(valores_array),
            area_hectareas=area_hectareas,
            histograma=histograma
        )
    
    def _estadisticas_vacias(self, area_hectareas: float) -> EstadisticasZonales:
        """Retorna estadísticas vacías cuando no hay datos válidos"""
        return EstadisticasZonales(
            media=0.0,
            mediana=0.0,
            desviacion=0.0,
            minimo=0.0,
            maximo=0.0,
            percentil_25=0.0,
            percentil_75=0.0,
            coef_variacion=0.0,
            area_pixels=0,
            area_hectareas=area_hectareas,
            histograma={}
        )
    
    def detectar_hotspots(
        self,
        valores_array: np.ndarray,
        umbral_percentil: int = 90
    ) -> Dict[str, Any]:
        """
        Detecta zonas de valores extremos (hotspots y coldspots).
        
        Útil para identificar:
        - Zonas de estrés severo (hotspots negativos)
        - Zonas de vigor excepcional (hotspots positivos)
        
        Args:
            valores_array: Array con valores del índice
            umbral_percentil: Percentil para considerar hotspot
            
        Returns:
            Dict con análisis de hotspots
        """
        valores_validos = valores_array[np.isfinite(valores_array)]
        
        if len(valores_validos) == 0:
            return {'error': 'No hay datos válidos'}
        
        # Calcular umbrales
        umbral_alto = np.percentile(valores_validos, umbral_percentil)
        umbral_bajo = np.percentile(valores_validos, 100 - umbral_percentil)
        
        # Identificar hotspots
        hotspots_positivos = np.sum(valores_validos >= umbral_alto)
        hotspots_negativos = np.sum(valores_validos <= umbral_bajo)
        
        porcentaje_positivo = (hotspots_positivos / len(valores_validos)) * 100
        porcentaje_negativo = (hotspots_negativos / len(valores_validos)) * 100
        
        return {
            'umbral_alto': round(float(umbral_alto), 4),
            'umbral_bajo': round(float(umbral_bajo), 4),
            'num_hotspots_positivos': int(hotspots_positivos),
            'num_hotspots_negativos': int(hotspots_negativos),
            'porcentaje_positivo': round(porcentaje_positivo, 2),
            'porcentaje_negativo': round(porcentaje_negativo, 2),
            'interpretacion': self._interpretar_hotspots(
                porcentaje_positivo,
                porcentaje_negativo
            )
        }
    
    def _interpretar_hotspots(
        self,
        pct_positivo: float,
        pct_negativo: float
    ) -> str:
        """Genera interpretación de hotspots"""
        if pct_negativo > 15:
            return "⚠️ Múltiples zonas de estrés severo detectadas"
        elif pct_positivo > 15:
            return "✅ Múltiples zonas de alto vigor vegetativo"
        else:
            return "ℹ️ Distribución uniforme, sin zonas extremas"
    
    def analizar_calidad_imagen(
        self,
        valores_array: np.ndarray,
        nubosidad: float
    ) -> Dict[str, Any]:
        """
        Analiza la calidad de la imagen satelital.
        
        Args:
            valores_array: Array con valores del índice
            nubosidad: Porcentaje de nubosidad reportado
            
        Returns:
            Dict con métricas de calidad
        """
        total_pixels = valores_array.size
        pixels_validos = np.sum(np.isfinite(valores_array))
        pixels_invalidos = total_pixels - pixels_validos
        
        porcentaje_validos = (pixels_validos / total_pixels) * 100
        
        # Clasificación de calidad
        if porcentaje_validos >= 95 and nubosidad < 10:
            calidad = "excelente"
            confianza = "alta"
        elif porcentaje_validos >= 85 and nubosidad < 20:
            calidad = "buena"
            confianza = "alta"
        elif porcentaje_validos >= 70 and nubosidad < 40:
            calidad = "aceptable"
            confianza = "media"
        else:
            calidad = "baja"
            confianza = "baja"
        
        return {
            'total_pixels': int(total_pixels),
            'pixels_validos': int(pixels_validos),
            'pixels_invalidos': int(pixels_invalidos),
            'porcentaje_validos': round(porcentaje_validos, 2),
            'nubosidad': round(nubosidad, 2),
            'calidad': calidad,
            'confianza': confianza,
            'recomendacion': self._recomendar_uso_imagen(calidad, nubosidad)
        }
    
    def _recomendar_uso_imagen(self, calidad: str, nubosidad: float) -> str:
        """Recomienda si usar o no la imagen"""
        if calidad in ['excelente', 'buena']:
            return "✅ Imagen apta para análisis detallado"
        elif calidad == 'aceptable':
            return "⚠️ Usar con precaución, considerar imagen alternativa"
        else:
            return "❌ Imagen no confiable, buscar fecha alternativa"
    
    def generar_mascara_calidad(
        self,
        valores_array: np.ndarray,
        umbral_min: float = -1.0,
        umbral_max: float = 1.0
    ) -> np.ndarray:
        """
        Genera máscara booleana de píxeles válidos.
        
        Args:
            valores_array: Array con valores del índice
            umbral_min: Valor mínimo válido
            umbral_max: Valor máximo válido
            
        Returns:
            Array booleano (True = válido, False = inválido)
        """
        mascara = (
            np.isfinite(valores_array) &
            (valores_array >= umbral_min) &
            (valores_array <= umbral_max)
        )
        
        self.logger.info(
            f"📊 Máscara generada: {np.sum(mascara)}/{valores_array.size} "
            f"píxeles válidos ({np.sum(mascara)/valores_array.size*100:.1f}%)"
        )
        
        return mascara
    
    def calcular_variabilidad_espacial(
        self,
        valores_array: np.ndarray,
        metodo: str = 'cv'
    ) -> Dict[str, Any]:
        """
        Calcula métricas de variabilidad espacial.
        
        Métodos disponibles:
        - 'cv': Coeficiente de variación
        - 'iqr': Rango intercuartílico
        - 'entropy': Entropía de Shannon
        
        Args:
            valores_array: Array con valores del índice
            metodo: Método de cálculo
            
        Returns:
            Dict con métricas de variabilidad
        """
        valores_validos = valores_array[np.isfinite(valores_array)]
        
        if len(valores_validos) == 0:
            return {'error': 'No hay datos válidos'}
        
        resultados = {}
        
        if metodo in ['cv', 'all']:
            media = np.mean(valores_validos)
            desviacion = np.std(valores_validos)
            cv = (desviacion / media * 100) if media != 0 else 0
            resultados['coef_variacion'] = round(cv, 2)
            resultados['interpretacion_cv'] = self._interpretar_cv(cv)
        
        if metodo in ['iqr', 'all']:
            q75, q25 = np.percentile(valores_validos, [75, 25])
            iqr = q75 - q25
            resultados['iqr'] = round(iqr, 4)
            resultados['interpretacion_iqr'] = self._interpretar_iqr(iqr)
        
        if metodo in ['entropy', 'all']:
            # Entropía de Shannon del histograma normalizado
            hist, _ = np.histogram(valores_validos, bins=20)
            hist_norm = hist / hist.sum()
            # Evitar log(0)
            hist_norm = hist_norm[hist_norm > 0]
            entropia = -np.sum(hist_norm * np.log2(hist_norm))
            resultados['entropia'] = round(entropia, 4)
            resultados['interpretacion_entropia'] = self._interpretar_entropia(entropia)
        
        return resultados
    
    def _interpretar_cv(self, cv: float) -> str:
        """Interpreta coeficiente de variación"""
        if cv < 10:
            return "Muy homogéneo - Baja variabilidad espacial"
        elif cv < 20:
            return "Homogéneo - Variabilidad espacial moderada"
        elif cv < 30:
            return "Heterogéneo - Alta variabilidad espacial"
        else:
            return "Muy heterogéneo - Variabilidad espacial extrema"
    
    def _interpretar_iqr(self, iqr: float) -> str:
        """Interpreta rango intercuartílico"""
        if iqr < 0.1:
            return "Distribución muy concentrada"
        elif iqr < 0.2:
            return "Distribución concentrada"
        elif iqr < 0.3:
            return "Distribución dispersa"
        else:
            return "Distribución muy dispersa"
    
    def _interpretar_entropia(self, entropia: float) -> str:
        """Interpreta entropía de Shannon"""
        # Entropía máxima para 20 bins es log2(20) ≈ 4.32
        if entropia < 2:
            return "Distribución muy concentrada en pocos valores"
        elif entropia < 3:
            return "Distribución moderadamente concentrada"
        elif entropia < 4:
            return "Distribución uniforme"
        else:
            return "Distribución muy uniforme (alta diversidad)"


# Instancia global para uso en el sistema
procesador_raster = ProcesadorRaster()
