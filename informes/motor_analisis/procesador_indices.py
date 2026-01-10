"""
Procesador de Índices Vegetativos
=================================

Procesa series temporales de índices vegetativos (NDVI, NDMI, SAVI, etc.)
calculando estadísticas descriptivas, tendencias y patrones.

Metodología:
- Estadística descriptiva: media, mediana, desviación estándar, percentiles
- Análisis temporal: regresión lineal, tendencias, estacionalidad
- Detección de outliers: Z-score, IQR
- Agregaciones espaciales: promedio por zona, histogramas

Tecnologías:
- NumPy: Cálculos numéricos
- SciPy: Regresión lineal, estadística
- Pandas: Manejo de series temporales (opcional)
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
from datetime import date, datetime
import logging

from .config_umbrales import (
    obtener_umbrales_ndvi,
    UMBRALES_NDMI,
    UMBRALES_SAVI,
    calcular_puntuacion,
    interpretar_tendencia,
    ConfigAnomalias
)

logger = logging.getLogger(__name__)


class ProcesadorIndices:
    """
    Procesador profesional de índices vegetativos
    
    Características:
    - Cálculo de estadísticas descriptivas robustas
    - Análisis de tendencias temporales
    - Detección de anomalías
    - Clasificación automática según umbrales
    """
    
    def __init__(self, tipo_cultivo: str = None):
        """
        Inicializa procesador
        
        Args:
            tipo_cultivo: Tipo de cultivo para ajustar umbrales
        """
        self.tipo_cultivo = tipo_cultivo
        self.umbrales_ndvi = obtener_umbrales_ndvi(tipo_cultivo)
        self.umbrales_ndmi = UMBRALES_NDMI
        self.umbrales_savi = UMBRALES_SAVI
    
    def procesar_serie_temporal(
        self,
        datos: List[Dict],
        indice: str = 'ndvi'
    ) -> Dict:
        """
        Procesa serie temporal de un índice
        
        Args:
            datos: Lista de diccionarios con {periodo, valor}
            indice: Nombre del índice ('ndvi', 'ndmi', 'savi')
            
        Returns:
            Diccionario con estadísticas y análisis
        """
        # Validar datos
        if not datos:
            raise ValueError("No hay datos para procesar")
        
        # Extraer valores
        valores = np.array([d.get(indice) for d in datos if d.get(indice) is not None])
        
        if len(valores) == 0:
            logger.warning(f"No hay valores válidos para {indice}")
            return self._resultado_vacio(indice)
        
        # Calcular estadísticas
        estadisticas = self._calcular_estadisticas(valores)
        
        # Analizar tendencia
        tendencia = self._analizar_tendencia(valores)
        
        # Detectar anomalías
        anomalias = self._detectar_anomalias(valores)
        
        # Clasificar estado
        estado = self._clasificar_estado(estadisticas['promedio'], indice)
        
        # Calcular puntuación
        umbrales = self._obtener_umbrales(indice)
        puntuacion = calcular_puntuacion(estadisticas['promedio'], umbrales)
        
        return {
            'indice': indice.upper(),
            'estadisticas': estadisticas,
            'tendencia': tendencia,
            'anomalias': anomalias,
            'estado': estado,
            'puntuacion': puntuacion,
            'n_observaciones': len(valores),
            'calidad_datos': self._evaluar_calidad_datos(valores, datos)
        }
    
    def _calcular_estadisticas(self, valores: np.ndarray) -> Dict:
        """
        Calcula estadísticas descriptivas robustas
        
        Args:
            valores: Array de valores numéricos
            
        Returns:
            Diccionario con estadísticas
        """
        return {
            'promedio': float(np.mean(valores)),
            'mediana': float(np.median(valores)),
            'desviacion_estandar': float(np.std(valores, ddof=1)),
            'minimo': float(np.min(valores)),
            'maximo': float(np.max(valores)),
            'percentil_25': float(np.percentile(valores, 25)),
            'percentil_75': float(np.percentile(valores, 75)),
            'rango': float(np.max(valores) - np.min(valores)),
            'coeficiente_variacion': float(np.std(valores, ddof=1) / np.mean(valores)) if np.mean(valores) != 0 else 0,
        }
    
    def _analizar_tendencia(self, valores: np.ndarray) -> Dict:
        """
        Analiza tendencia temporal usando regresión lineal
        
        Args:
            valores: Array de valores temporales
            
        Returns:
            Diccionario con análisis de tendencia
        """
        if len(valores) < 3:
            return {
                'tiene_tendencia': False,
                'direccion': 'insuficiente',
                'pendiente': 0.0,
                'r_cuadrado': 0.0,
                'cambio_total_pct': 0.0
            }
        
        # Regresión lineal
        x = np.arange(len(valores))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, valores)
        
        # Calcular cambio porcentual
        valor_inicial = valores[0] if valores[0] != 0 else 0.001
        cambio_total = ((valores[-1] - valores[0]) / abs(valor_inicial)) * 100
        
        # Interpretar tendencia
        interpretacion = interpretar_tendencia(slope, r_value**2)
        
        return {
            'tiene_tendencia': abs(cambio_total) >= ConfigAnomalias.CAMBIO_MINIMO_TENDENCIA,
            'direccion': interpretacion['direccion'],
            'pendiente': float(slope),
            'r_cuadrado': float(r_value**2),
            'p_value': float(p_value),
            'cambio_total_pct': float(cambio_total),
            'confianza': interpretacion['confianza'],
            'significativa': p_value < 0.05
        }
    
    def _detectar_anomalias(self, valores: np.ndarray) -> Dict:
        """
        Detecta outliers y valores anómalos
        
        Args:
            valores: Array de valores
            
        Returns:
            Diccionario con detección de anomalías
        """
        if len(valores) < 4:
            return {'outliers': [], 'n_outliers': 0}
        
        # Método Z-score
        mean = np.mean(valores)
        std = np.std(valores, ddof=1)
        
        if std == 0:
            return {'outliers': [], 'n_outliers': 0}
        
        z_scores = np.abs((valores - mean) / std)
        outliers_indices = np.where(z_scores > ConfigAnomalias.UMBRAL_OUTLIER_SIGMA)[0]
        
        # Método IQR (más robusto)
        q1 = np.percentile(valores, 25)
        q3 = np.percentile(valores, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers_iqr = np.where((valores < lower_bound) | (valores > upper_bound))[0]
        
        # Combinar detecciones
        outliers_unicos = np.unique(np.concatenate([outliers_indices, outliers_iqr]))
        
        return {
            'outliers': [int(idx) for idx in outliers_unicos],
            'n_outliers': len(outliers_unicos),
            'porcentaje_outliers': (len(outliers_unicos) / len(valores)) * 100 if len(valores) > 0 else 0,
            'metodo': 'Z-score + IQR'
        }
    
    def _clasificar_estado(self, valor_promedio: float, indice: str) -> Dict:
        """
        Clasifica estado según umbrales
        
        Args:
            valor_promedio: Valor promedio del índice
            indice: Tipo de índice
            
        Returns:
            Diccionario con clasificación
        """
        umbrales = self._obtener_umbrales(indice)
        clasificacion = umbrales.clasificar(valor_promedio)
        
        # Mapeo a etiquetas legibles
        etiquetas = {
            'muy_bajo': ('Muy Bajo - Crítico', '🔴'),
            'bajo': ('Bajo - Requiere Atención', '🟠'),
            'medio': ('Medio - Aceptable', '🟡'),
            'alto': ('Alto - Bueno', '🟢'),
            'muy_alto': ('Muy Alto - Excelente', '💚')
        }
        
        etiqueta, icono = etiquetas.get(clasificacion, ('Desconocido', '❓'))
        
        return {
            'clasificacion': clasificacion,
            'etiqueta': etiqueta,
            'icono': icono,
            'nivel_numerico': umbrales.nivel_numerico(valor_promedio)
        }
    
    def _obtener_umbrales(self, indice: str):
        """Obtiene umbrales para un índice específico"""
        umbrales_map = {
            'ndvi': self.umbrales_ndvi,
            'ndmi': self.umbrales_ndmi,
            'savi': self.umbrales_savi
        }
        return umbrales_map.get(indice, self.umbrales_ndvi)
    
    def _evaluar_calidad_datos(self, valores: np.ndarray, datos_originales: List) -> Dict:
        """
        Evalúa calidad de los datos
        
        Args:
            valores: Valores procesados
            datos_originales: Datos originales
            
        Returns:
            Diccionario con evaluación de calidad
        """
        total_esperado = len(datos_originales)
        total_validos = len(valores)
        
        completitud = (total_validos / total_esperado) * 100 if total_esperado > 0 else 0
        
        # Clasificar calidad
        if completitud >= 90:
            calidad = 'excelente'
        elif completitud >= 75:
            calidad = 'buena'
        elif completitud >= 50:
            calidad = 'aceptable'
        else:
            calidad = 'deficiente'
        
        return {
            'completitud_pct': completitud,
            'datos_faltantes': total_esperado - total_validos,
            'calidad': calidad
        }
    
    def _resultado_vacio(self, indice: str) -> Dict:
        """Retorna resultado vacío cuando no hay datos"""
        return {
            'indice': indice.upper(),
            'estadisticas': {},
            'tendencia': {},
            'anomalias': {'outliers': [], 'n_outliers': 0},
            'estado': {'clasificacion': 'desconocido', 'etiqueta': 'Sin datos', 'icono': '❓'},
            'puntuacion': 0.0,
            'n_observaciones': 0,
            'calidad_datos': {'completitud_pct': 0, 'calidad': 'sin_datos'}
        }
    
    def comparar_periodos(
        self,
        valores_actual: np.ndarray,
        valores_anterior: np.ndarray
    ) -> Dict:
        """
        Compara dos períodos temporales
        
        Args:
            valores_actual: Valores del período actual
            valores_anterior: Valores del período anterior
            
        Returns:
            Diccionario con comparación
        """
        if len(valores_actual) == 0 or len(valores_anterior) == 0:
            return {'comparacion_valida': False}
        
        # Promedios
        prom_actual = np.mean(valores_actual)
        prom_anterior = np.mean(valores_anterior)
        
        # Cambio absoluto y relativo
        cambio_abs = prom_actual - prom_anterior
        cambio_rel = (cambio_abs / abs(prom_anterior)) * 100 if prom_anterior != 0 else 0
        
        # Test estadístico (t-test)
        try:
            t_stat, p_value = stats.ttest_ind(valores_actual, valores_anterior)
            diferencia_significativa = p_value < 0.05
        except:
            t_stat, p_value = 0, 1.0
            diferencia_significativa = False
        
        # Interpretación
        if abs(cambio_rel) < 5:
            interpretacion = 'sin_cambios'
        elif cambio_rel > 0:
            interpretacion = 'mejora'
        else:
            interpretacion = 'deterioro'
        
        return {
            'comparacion_valida': True,
            'promedio_actual': float(prom_actual),
            'promedio_anterior': float(prom_anterior),
            'cambio_absoluto': float(cambio_abs),
            'cambio_relativo_pct': float(cambio_rel),
            'interpretacion': interpretacion,
            'diferencia_significativa': diferencia_significativa,
            'p_value': float(p_value)
        }
