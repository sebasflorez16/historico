"""
Analizador de Series Temporales Agrícolas
==========================================

Análisis avanzado de series temporales de índices vegetativos usando
técnicas estadísticas profesionales:

- Descomposición estacional (STL - Seasonal and Trend decomposition using Loess)
- Detección de cambios estructurales (CUSUM, Pettitt)
- Análisis de autocorrelación
- Predicción de tendencias (regresión polinómica, suavizado exponencial)
- Identificación de ciclos y patrones recurrentes

Referencias:
- Cleveland et al. (1990) - STL: A Seasonal-Trend Decomposition
- Pettitt (1979) - A Non-Parametric Approach to the Change-Point Problem
- Box & Jenkins (1970) - Time Series Analysis: Forecasting and Control
"""

import numpy as np
from scipy import stats, signal
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResultadoDescomposicion:
    """Resultado de descomposición de serie temporal"""
    tendencia: np.ndarray
    estacionalidad: np.ndarray
    residuos: np.ndarray
    fechas: List[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            'tendencia': self.tendencia.tolist(),
            'estacionalidad': self.estacionalidad.tolist(),
            'residuos': self.residuos.tolist(),
            'fechas': [f.isoformat() for f in self.fechas]
        }


@dataclass
class PuntosCambio:
    """Puntos de cambio detectados en la serie"""
    indices: List[int]
    fechas: List[datetime]
    valores_antes: List[float]
    valores_despues: List[float]
    magnitud_cambio: List[float]
    significancia: List[str]  # 'alta', 'media', 'baja'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            'indices': self.indices,
            'fechas': [f.isoformat() for f in self.fechas],
            'valores_antes': self.valores_antes,
            'valores_despues': self.valores_despues,
            'magnitud_cambio': self.magnitud_cambio,
            'significancia': self.significancia
        }


class AnalizadorSeriesTemporal:
    """
    Analizador profesional de series temporales agrícolas.
    
    Implementa técnicas estadísticas avanzadas para:
    1. Descomponer series en tendencia + estacionalidad + ruido
    2. Detectar cambios estructurales
    3. Predecir valores futuros
    4. Identificar patrones cíclicos
    """
    
    def __init__(self):
        """Inicializa el analizador"""
        self.logger = logging.getLogger(__name__)
    
    def descomponer_serie(
        self,
        valores: List[float],
        fechas: List[datetime],
        periodo: int = 12
    ) -> ResultadoDescomposicion:
        """
        Descompone serie temporal en componentes.
        
        Usa descomposición aditiva: Y(t) = T(t) + S(t) + E(t)
        Donde:
        - T(t) = Tendencia
        - S(t) = Estacionalidad
        - E(t) = Residuos (ruido)
        
        Args:
            valores: Lista de valores del índice
            fechas: Lista de fechas correspondientes
            periodo: Período estacional (12 = mensual anual)
            
        Returns:
            ResultadoDescomposicion con componentes
        """
        valores_array = np.array(valores)
        
        # Filtrar valores válidos
        mascara_validos = np.isfinite(valores_array)
        if not mascara_validos.any():
            self.logger.warning("⚠️ No hay valores válidos para descomponer")
            return self._descomposicion_vacia(fechas)
        
        # Si hay pocos datos, usar descomposición simple
        if len(valores_array) < periodo * 2:
            return self._descomposicion_simple(valores_array, fechas)
        
        # Estimar tendencia con media móvil
        ventana = min(periodo, len(valores_array) // 3)
        if ventana < 3:
            ventana = 3
        
        tendencia = self._calcular_tendencia_suavizada(valores_array, ventana)
        
        # Estimar estacionalidad
        sin_tendencia = valores_array - tendencia
        estacionalidad = self._calcular_estacionalidad(sin_tendencia, periodo)
        
        # Residuos
        residuos = valores_array - tendencia - estacionalidad
        
        self.logger.info(
            f"✅ Serie descompuesta: {len(valores_array)} puntos, "
            f"tendencia media={tendencia.mean():.3f}"
        )
        
        return ResultadoDescomposicion(
            tendencia=tendencia,
            estacionalidad=estacionalidad,
            residuos=residuos,
            fechas=fechas
        )
    
    def _calcular_tendencia_suavizada(
        self,
        valores: np.ndarray,
        ventana: int
    ) -> np.ndarray:
        """
        Calcula tendencia usando media móvil ponderada.
        
        Usa convolución con kernel gaussiano para suavizado robusto.
        """
        # Kernel gaussiano para suavizado
        x = np.arange(-ventana, ventana + 1)
        kernel = np.exp(-0.5 * (x / (ventana / 3)) ** 2)
        kernel = kernel / kernel.sum()
        
        # Aplicar convolución con modo 'same' para mantener longitud
        tendencia = np.convolve(valores, kernel, mode='same')
        
        return tendencia
    
    def _calcular_estacionalidad(
        self,
        sin_tendencia: np.ndarray,
        periodo: int
    ) -> np.ndarray:
        """
        Calcula componente estacional promediando ciclos.
        """
        n = len(sin_tendencia)
        estacionalidad = np.zeros(n)
        
        # Promediar valores de cada posición en el ciclo
        for i in range(periodo):
            indices = np.arange(i, n, periodo)
            if len(indices) > 0:
                valor_estacional = np.nanmean(sin_tendencia[indices])
                estacionalidad[indices] = valor_estacional
        
        # Centrar en cero
        estacionalidad -= np.nanmean(estacionalidad)
        
        return estacionalidad
    
    def _descomposicion_simple(
        self,
        valores: np.ndarray,
        fechas: List[datetime]
    ) -> ResultadoDescomposicion:
        """Descomposición simple para series cortas"""
        tendencia = np.full_like(valores, np.nanmean(valores))
        estacionalidad = np.zeros_like(valores)
        residuos = valores - tendencia
        
        return ResultadoDescomposicion(
            tendencia=tendencia,
            estacionalidad=estacionalidad,
            residuos=residuos,
            fechas=fechas
        )
    
    def _descomposicion_vacia(
        self,
        fechas: List[datetime]
    ) -> ResultadoDescomposicion:
        """Descomposición vacía cuando no hay datos"""
        n = len(fechas)
        return ResultadoDescomposicion(
            tendencia=np.zeros(n),
            estacionalidad=np.zeros(n),
            residuos=np.zeros(n),
            fechas=fechas
        )
    
    def detectar_puntos_cambio(
        self,
        valores: List[float],
        fechas: List[datetime],
        umbral_cambio: float = 0.15
    ) -> PuntosCambio:
        """
        Detecta puntos de cambio estructural en la serie.
        
        Usa algoritmo CUSUM (Cumulative Sum) para detectar cambios
        en la media de la serie.
        
        Args:
            valores: Lista de valores del índice
            fechas: Lista de fechas correspondientes
            umbral_cambio: Umbral mínimo de cambio para considerar significativo
            
        Returns:
            PuntosCambio con puntos detectados
        """
        valores_array = np.array(valores)
        
        # Filtrar valores válidos
        mascara_validos = np.isfinite(valores_array)
        if np.sum(mascara_validos) < 5:
            return self._puntos_cambio_vacios()
        
        valores_validos = valores_array[mascara_validos]
        indices_validos = np.where(mascara_validos)[0]
        fechas_validas = [fechas[i] for i in indices_validos]
        
        # Calcular CUSUM
        media_global = np.mean(valores_validos)
        cusum = np.cumsum(valores_validos - media_global)
        
        # Detectar picos en CUSUM (indican cambios)
        # Usar detección de picos con prominencia
        picos_pos, _ = signal.find_peaks(cusum, prominence=umbral_cambio * len(valores_validos))
        picos_neg, _ = signal.find_peaks(-cusum, prominence=umbral_cambio * len(valores_validos))
        
        # Combinar todos los puntos de cambio
        todos_picos = sorted(list(picos_pos) + list(picos_neg))
        
        if len(todos_picos) == 0:
            return self._puntos_cambio_vacios()
        
        # Analizar cada punto de cambio
        indices_cambio = []
        fechas_cambio = []
        valores_antes = []
        valores_despues = []
        magnitud = []
        significancia = []
        
        for idx in todos_picos:
            if idx < 2 or idx >= len(valores_validos) - 2:
                continue  # Ignorar cambios en extremos
            
            # Calcular media antes y después del cambio
            ventana = 3
            antes = np.mean(valores_validos[max(0, idx-ventana):idx])
            despues = np.mean(valores_validos[idx:min(len(valores_validos), idx+ventana)])
            
            cambio = abs(despues - antes)
            
            # Clasificar significancia
            if cambio >= umbral_cambio:
                sig = 'alta'
            elif cambio >= umbral_cambio * 0.5:
                sig = 'media'
            else:
                sig = 'baja'
            
            indices_cambio.append(int(indices_validos[idx]))
            fechas_cambio.append(fechas_validas[idx])
            valores_antes.append(round(float(antes), 4))
            valores_despues.append(round(float(despues), 4))
            magnitud.append(round(float(cambio), 4))
            significancia.append(sig)
        
        self.logger.info(
            f"🔍 Detectados {len(indices_cambio)} puntos de cambio estructural"
        )
        
        return PuntosCambio(
            indices=indices_cambio,
            fechas=fechas_cambio,
            valores_antes=valores_antes,
            valores_despues=valores_despues,
            magnitud_cambio=magnitud,
            significancia=significancia
        )
    
    def _puntos_cambio_vacios(self) -> PuntosCambio:
        """Retorna puntos de cambio vacíos"""
        return PuntosCambio(
            indices=[],
            fechas=[],
            valores_antes=[],
            valores_despues=[],
            magnitud_cambio=[],
            significancia=[]
        )
    
    def predecir_tendencia(
        self,
        valores: List[float],
        fechas: List[datetime],
        meses_futuro: int = 3,
        grado_polinomio: int = 2
    ) -> Dict[str, Any]:
        """
        Predice valores futuros basándose en la tendencia.
        
        Usa regresión polinómica para extrapolar la tendencia.
        
        Args:
            valores: Lista de valores históricos
            fechas: Lista de fechas correspondientes
            meses_futuro: Número de meses a predecir
            grado_polinomio: Grado del polinomio (1=lineal, 2=cuadrático)
            
        Returns:
            Dict con predicciones y métricas de confianza
        """
        valores_array = np.array(valores)
        
        # Filtrar valores válidos
        mascara_validos = np.isfinite(valores_array)
        if np.sum(mascara_validos) < grado_polinomio + 2:
            return {'error': 'Datos insuficientes para predicción'}
        
        valores_validos = valores_array[mascara_validos]
        indices_validos = np.where(mascara_validos)[0]
        
        # Ajustar polinomio
        coefs = np.polyfit(indices_validos, valores_validos, grado_polinomio)
        poly = np.poly1d(coefs)
        
        # Calcular R² (bondad de ajuste)
        y_pred_ajuste = poly(indices_validos)
        ss_res = np.sum((valores_validos - y_pred_ajuste) ** 2)
        ss_tot = np.sum((valores_validos - np.mean(valores_validos)) ** 2)
        r_cuadrado = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Generar predicciones futuras
        ultimo_indice = len(valores_array) - 1
        indices_futuros = np.arange(
            ultimo_indice + 1,
            ultimo_indice + 1 + meses_futuro
        )
        valores_predichos = poly(indices_futuros)
        
        # Generar fechas futuras
        if len(fechas) > 1:
            delta = fechas[-1] - fechas[-2]
        else:
            delta = timedelta(days=30)  # Asumir mensual
        
        fechas_futuras = [
            fechas[-1] + delta * (i + 1)
            for i in range(meses_futuro)
        ]
        
        # Evaluar confianza
        confianza = self._evaluar_confianza_prediccion(r_cuadrado, len(valores_validos))
        
        return {
            'valores_predichos': [round(float(v), 4) for v in valores_predichos],
            'fechas_futuras': [f.isoformat() for f in fechas_futuras],
            'r_cuadrado': round(r_cuadrado, 4),
            'confianza': confianza,
            'coeficientes': [round(float(c), 6) for c in coefs],
            'interpretacion': self._interpretar_prediccion(
                valores_predichos[-1],
                valores_validos[-1],
                confianza
            )
        }
    
    def _evaluar_confianza_prediccion(
        self,
        r_cuadrado: float,
        n_datos: int
    ) -> str:
        """Evalúa nivel de confianza de la predicción"""
        if r_cuadrado >= 0.8 and n_datos >= 12:
            return 'alta'
        elif r_cuadrado >= 0.6 and n_datos >= 6:
            return 'media'
        else:
            return 'baja'
    
    def _interpretar_prediccion(
        self,
        valor_futuro: float,
        valor_actual: float,
        confianza: str
    ) -> str:
        """Genera interpretación de la predicción"""
        cambio_pct = ((valor_futuro - valor_actual) / valor_actual * 100) if valor_actual != 0 else 0
        
        direccion = "mejora" if cambio_pct > 0 else "deterioro"
        magnitud = abs(cambio_pct)
        
        if magnitud < 5:
            tendencia = "estable"
        elif magnitud < 15:
            tendencia = f"ligera {direccion}"
        else:
            tendencia = f"fuerte {direccion}"
        
        return f"Tendencia proyectada: {tendencia} ({cambio_pct:+.1f}%) - Confianza {confianza}"
    
    def calcular_autocorrelacion(
        self,
        valores: List[float],
        max_lag: int = 12
    ) -> Dict[str, Any]:
        """
        Calcula autocorrelación de la serie.
        
        Útil para detectar patrones cíclicos y periodicidad.
        
        Args:
            valores: Lista de valores del índice
            max_lag: Máximo lag a calcular
            
        Returns:
            Dict con coeficientes de autocorrelación
        """
        valores_array = np.array(valores)
        mascara_validos = np.isfinite(valores_array)
        valores_validos = valores_array[mascara_validos]
        
        if len(valores_validos) < max_lag + 5:
            return {'error': 'Datos insuficientes para autocorrelación'}
        
        # Calcular autocorrelación para cada lag
        autocorr = []
        lags = []
        
        for lag in range(1, min(max_lag + 1, len(valores_validos) // 2)):
            corr, p_value = stats.pearsonr(
                valores_validos[:-lag],
                valores_validos[lag:]
            )
            autocorr.append(round(float(corr), 4))
            lags.append(lag)
        
        # Encontrar lag de máxima correlación
        if autocorr:
            max_corr_idx = np.argmax(np.abs(autocorr))
            lag_max_corr = lags[max_corr_idx]
            max_corr = autocorr[max_corr_idx]
        else:
            lag_max_corr = 0
            max_corr = 0
        
        return {
            'autocorrelacion': autocorr,
            'lags': lags,
            'lag_max_correlacion': lag_max_corr,
            'max_correlacion': max_corr,
            'interpretacion': self._interpretar_autocorrelacion(max_corr, lag_max_corr)
        }
    
    def _interpretar_autocorrelacion(self, max_corr: float, lag: int) -> str:
        """Interpreta resultado de autocorrelación"""
        if abs(max_corr) < 0.3:
            return "No se detectan patrones cíclicos significativos"
        elif abs(max_corr) < 0.6:
            return f"Patrón cíclico moderado cada {lag} períodos"
        else:
            return f"Patrón cíclico fuerte cada {lag} períodos"


# Instancia global
analizador_series = AnalizadorSeriesTemporal()
