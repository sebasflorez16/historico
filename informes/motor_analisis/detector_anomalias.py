"""
Detector de Anomalías Temporales
================================

Detecta patrones anómalos, cambios bruscos y eventos críticos
en series temporales de índices vegetativos.

Métodos:
- Detección de caídas bruscas (deterioro)
- Identificación de recuperaciones
- Análisis de patrones estacionales
- Eventos extremos
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .config_umbrales import ConfigAnomalias

logger = logging.getLogger(__name__)


class DetectorAnomalias:
    """
    Detecta anomalías y eventos críticos en series temporales
    """
    
    def __init__(self):
        self.config = ConfigAnomalias()
    
    def detectar_deterioros(
        self,
        valores: np.ndarray,
        periodos: List[str]
    ) -> List[Dict]:
        """
        Detecta caídas significativas en la serie temporal
        
        Args:
            valores: Array de valores
            periodos: Lista de etiquetas de período
            
        Returns:
            Lista de deterioros detectados
        """
        if len(valores) < 2:
            return []
        
        deterioros = []
        
        # Calcular cambios entre períodos consecutivos
        cambios = np.diff(valores)
        cambios_pct = (cambios / valores[:-1]) * 100
        
        for i, cambio_pct in enumerate(cambios_pct):
            if cambio_pct < self.config.CAIDA_CRITICA_NDVI:
                deterioros.append({
                    'periodo_inicio': periodos[i] if i < len(periodos) else f'P{i}',
                    'periodo_fin': periodos[i+1] if i+1 < len(periodos) else f'P{i+1}',
                    'valor_inicial': float(valores[i]),
                    'valor_final': float(valores[i+1]),
                    'cambio_absoluto': float(cambios[i]),
                    'cambio_relativo_pct': float(cambio_pct),
                    'severidad': 'critica' if cambio_pct < self.config.CAIDA_CRITICA_NDVI else 'moderada'
                })
        
        return deterioros
    
    def detectar_recuperaciones(
        self,
        valores: np.ndarray,
        periodos: List[str]
    ) -> List[Dict]:
        """
        Detecta recuperaciones significativas
        
        Args:
            valores: Array de valores
            periodos: Lista de períodos
            
        Returns:
            Lista de recuperaciones detectadas
        """
        if len(valores) < 2:
            return []
        
        recuperaciones = []
        
        # Calcular cambios
        cambios = np.diff(valores)
        cambios_pct = (cambios / valores[:-1]) * 100
        
        for i, cambio_pct in enumerate(cambios_pct):
            if cambio_pct > self.config.CAMBIO_MINIMO_TENDENCIA:
                recuperaciones.append({
                    'periodo_inicio': periodos[i] if i < len(periodos) else f'P{i}',
                    'periodo_fin': periodos[i+1] if i+1 < len(periodos) else f'P{i+1}',
                    'valor_inicial': float(valores[i]),
                    'valor_final': float(valores[i+1]),
                    'cambio_absoluto': float(cambios[i]),
                    'cambio_relativo_pct': float(cambio_pct),
                    'magnitud': 'significativa' if cambio_pct > 15 else 'moderada'
                })
        
        return recuperaciones
    
    def generar_alertas(
        self,
        promedio_actual: float,
        tendencia: Dict,
        deterioros: List[Dict]
    ) -> List[Dict]:
        """
        Genera alertas basadas en el estado actual
        
        Args:
            promedio_actual: Valor promedio actual
            tendencia: Diccionario con análisis de tendencia
            deterioros: Lista de deterioros detectados
            
        Returns:
            Lista de alertas
        """
        alertas = []
        
        # Alerta por valor bajo
        if promedio_actual < 0.3:
            alertas.append({
                'tipo': 'critica',
                'titulo': 'Valor Críticamente Bajo',
                'mensaje': f'El valor promedio ({promedio_actual:.3f}) está en niveles críticos',
                'accion_recomendada': 'Inspección inmediata del cultivo'
            })
        elif promedio_actual < 0.5:
            alertas.append({
                'tipo': 'advertencia',
                'titulo': 'Valor Bajo',
                'mensaje': f'El valor promedio ({promedio_actual:.3f}) está por debajo del óptimo',
                'accion_recomendada': 'Evaluar factores limitantes'
            })
        
        # Alerta por tendencia negativa
        if tendencia.get('direccion') == 'descendente' and tendencia.get('significativa'):
            alertas.append({
                'tipo': 'advertencia',
                'titulo': 'Tendencia Negativa Detectada',
                'mensaje': f'Disminución de {abs(tendencia["cambio_total_pct"]):.1f}% en el período',
                'accion_recomendada': 'Investigar causas del deterioro'
            })
        
        # Alerta por deterioros
        if len(deterioros) > 0:
            peor_deterioro = min(deterioros, key=lambda x: x['cambio_relativo_pct'])
            alertas.append({
                'tipo': 'critica',
                'titulo': 'Caída Brusca Detectada',
                'mensaje': f'Caída de {abs(peor_deterioro["cambio_relativo_pct"]):.1f}% entre {peor_deterioro["periodo_inicio"]} y {peor_deterioro["periodo_fin"]}',
                'accion_recomendada': 'Inspección urgente de la zona afectada'
            })
        
        return alertas
