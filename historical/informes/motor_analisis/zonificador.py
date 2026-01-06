"""
Zonificador de Productividad
============================

Clasifica áreas de un lote en zonas de productividad (baja, media, alta)
basándose en índices vegetativos y análisis estadístico.

Metodología:
- Clasificación por percentiles (33%, 66%)
- Análisis de variabilidad espacial
- Generación de mapas de productividad
- Cálculo de áreas por zona

Aplicaciones:
- Manejo sitio-específico
- Aplicación variable de insumos
- Zonificación para muestreo de suelo
"""

import numpy as np
from typing import Dict, List, Tuple
import logging

from .config_umbrales import ZonaProductividad

logger = logging.getLogger(__name__)


class ZonificadorProductivo:
    """
    Clasifica un lote en zonas de productividad
    
    Usa percentiles para dividir en:
    - Zona Baja: percentil 0-33
    - Zona Media: percentil 33-66
    - Zona Alta: percentil 66-100
    """
    
    def __init__(self):
        self.config = ZonaProductividad()
    
    def zonificar(
        self,
        valores: np.ndarray,
        metodo: str = 'percentiles'
    ) -> Dict:
        """
        Zonifica valores en áreas de productividad
        
        Args:
            valores: Array con valores del índice
            metodo: Método de zonificación ('percentiles', 'kmeans')
            
        Returns:
            Diccionario con zonificación y estadísticas
        """
        if len(valores) == 0:
            return self._resultado_vacio()
        
        if metodo == 'percentiles':
            return self._zonificar_percentiles(valores)
        elif metodo == 'kmeans':
            return self._zonificar_kmeans(valores)
        else:
            raise ValueError(f"Método {metodo} no soportado")
    
    def _zonificar_percentiles(self, valores: np.ndarray) -> Dict:
        """
        Zonifica usando percentiles fijos
        
        Args:
            valores: Array de valores
            
        Returns:
            Diccionario con zonificación
        """
        # Calcular percentiles
        p33 = np.percentile(valores, self.config.PERCENTIL_BAJA)
        p66 = np.percentile(valores, self.config.PERCENTIL_MEDIA)
        
        # Clasificar cada valor
        zonas = np.zeros(len(valores), dtype=int)
        zonas[valores < p33] = 1  # Baja
        zonas[(valores >= p33) & (valores < p66)] = 2  # Media
        zonas[valores >= p66] = 3  # Alta
        
        # Calcular estadísticas por zona
        n_total = len(valores)
        n_baja = np.sum(zonas == 1)
        n_media = np.sum(zonas == 2)
        n_alta = np.sum(zonas == 3)
        
        # Calcular áreas (asumiendo píxeles del mismo tamaño)
        pct_baja = (n_baja / n_total) * 100
        pct_media = (n_media / n_total) * 100
        pct_alta = (n_alta / n_total) * 100
        
        # Valores promedio por zona
        prom_baja = float(np.mean(valores[zonas == 1])) if n_baja > 0 else 0
        prom_media = float(np.mean(valores[zonas == 2])) if n_media > 0 else 0
        prom_alta = float(np.mean(valores[zonas == 3])) if n_alta > 0 else 0
        
        return {
            'metodo': 'percentiles',
            'umbrales': {
                'baja_media': float(p33),
                'media_alta': float(p66)
            },
            'distribucion': {
                'zona_baja': {
                    'n_pixeles': int(n_baja),
                    'porcentaje_area': float(pct_baja),
                    'valor_promedio': prom_baja
                },
                'zona_media': {
                    'n_pixeles': int(n_media),
                    'porcentaje_area': float(pct_media),
                    'valor_promedio': prom_media
                },
                'zona_alta': {
                    'n_pixeles': int(n_alta),
                    'porcentaje_area': float(pct_alta),
                    'valor_promedio': prom_alta
                }
            },
            'interpretacion': self._interpretar_zonificacion(pct_baja, pct_media, pct_alta)
        }
    
    def _zonificar_kmeans(self, valores: np.ndarray) -> Dict:
        """
        Zonifica usando K-means clustering
        
        Nota: Requiere scikit-learn. Implementación simplificada sin sklearn.
        
        Args:
            valores: Array de valores
            
        Returns:
            Diccionario con zonificación
        """
        # Por ahora, usar percentiles como fallback
        logger.warning("K-means requiere scikit-learn. Usando percentiles como alternativa.")
        return self._zonificar_percentiles(valores)
    
    def _interpretar_zonificacion(
        self,
        pct_baja: float,
        pct_media: float,
        pct_alta: float
    ) -> Dict:
        """
        Interpreta la distribución de zonas
        
        Args:
            pct_baja, pct_media, pct_alta: Porcentajes de cada zona
            
        Returns:
            Diccionario con interpretación
        """
        # Determinar homogeneidad
        desviacion = np.std([pct_baja, pct_media, pct_alta])
        
        if desviacion < 5:
            homogeneidad = 'muy_homogeneo'
            desc = 'El lote es muy homogéneo con distribución uniforme de productividad'
        elif desviacion < 10:
            homogeneidad = 'homogeneo'
            desc = 'El lote presenta buena homogeneidad con baja variabilidad'
        elif desviacion < 20:
            homogeneidad = 'heterogeneo'
            desc = 'El lote muestra variabilidad espacial significativa'
        else:
            homogeneidad = 'muy_heterogeneo'
            desc = 'El lote presenta alta variabilidad espacial - ideal para manejo sitio-específico'
        
        # Identificar zona dominante
        zonas = {'baja': pct_baja, 'media': pct_media, 'alta': pct_alta}
        zona_dominante = max(zonas, key=zonas.get)
        
        # Alertas
        alertas = []
        if pct_baja > 40:
            alertas.append({
                'tipo': 'critico',
                'mensaje': f'Más del {pct_baja:.1f}% del área presenta baja productividad'
            })
        elif pct_baja > 25:
            alertas.append({
                'tipo': 'advertencia',
                'mensaje': f'{pct_baja:.1f}% del área requiere atención para mejorar productividad'
            })
        
        if pct_alta > 60:
            alertas.append({
                'tipo': 'positivo',
                'mensaje': f'Excelente: {pct_alta:.1f}% del área presenta alta productividad'
            })
        
        return {
            'homogeneidad': homogeneidad,
            'descripcion': desc,
            'zona_dominante': zona_dominante,
            'alertas': alertas,
            'requiere_manejo_diferenciado': homogeneidad in ['heterogeneo', 'muy_heterogeneo']
        }
    
    def calcular_variabilidad(self, valores: np.ndarray) -> Dict:
        """
        Calcula métricas de variabilidad espacial
        
        Args:
            valores: Array de valores
            
        Returns:
            Diccionario con métricas de variabilidad
        """
        if len(valores) == 0:
            return {'variabilidad': 'sin_datos'}
        
        # Coeficiente de variación
        mean = np.mean(valores)
        std = np.std(valores, ddof=1)
        cv = (std / mean) * 100 if mean != 0 else 0
        
        # Rango
        rango = np.max(valores) - np.min(valores)
        rango_rel = (rango / mean) * 100 if mean != 0 else 0
        
        # Clasificar variabilidad
        if cv < self.config.VARIABILIDAD_BAJA * 100:
            clasificacion = 'baja'
            desc = 'Baja variabilidad - lote homogéneo'
        elif cv < self.config.VARIABILIDAD_MEDIA * 100:
            clasificacion = 'media'
            desc = 'Variabilidad moderada'
        elif cv < self.config.VARIABILIDAD_ALTA * 100:
            clasificacion = 'alta'
            desc = 'Alta variabilidad - considerar manejo diferenciado'
        else:
            clasificacion = 'muy_alta'
            desc = 'Variabilidad muy alta - manejo sitio-específico recomendado'
        
        return {
            'coeficiente_variacion': float(cv),
            'rango_absoluto': float(rango),
            'rango_relativo_pct': float(rango_rel),
            'desviacion_estandar': float(std),
            'clasificacion': clasificacion,
            'descripcion': desc
        }
    
    def generar_recomendaciones_zonificacion(self, resultado_zonificacion: Dict) -> List[Dict]:
        """
        Genera recomendaciones basadas en zonificación
        
        Args:
            resultado_zonificacion: Resultado de zonificar()
            
        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []
        
        distribucion = resultado_zonificacion['distribucion']
        pct_baja = distribucion['zona_baja']['porcentaje_area']
        interpretacion = resultado_zonificacion['interpretacion']
        
        # Recomendación por área baja
        if pct_baja > 30:
            recomendaciones.append({
                'titulo': 'Intervención Urgente en Zonas de Baja Productividad',
                'prioridad': 'alta',
                'descripcion': f'El {pct_baja:.1f}% del área presenta baja productividad',
                'acciones': [
                    'Realizar muestreo de suelo en zonas identificadas',
                    'Inspeccionar causas (drenaje, compactación, nutrición)',
                    'Evaluar ajustes en plan de fertilización',
                    'Considerar enmiendas o mejoras localizadas'
                ]
            })
        elif pct_baja > 15:
            recomendaciones.append({
                'titulo': 'Atención a Zonas de Baja Productividad',
                'prioridad': 'media',
                'descripcion': f'{pct_baja:.1f}% del área requiere atención',
                'acciones': [
                    'Monitorear evolución de zonas identificadas',
                    'Inspeccionar factores limitantes',
                    'Evaluar beneficio de intervenciones localizadas'
                ]
            })
        
        # Recomendación por heterogeneidad
        if interpretacion['requiere_manejo_diferenciado']:
            recomendaciones.append({
                'titulo': 'Implementar Agricultura de Precisión',
                'prioridad': 'media',
                'descripcion': 'La alta variabilidad espacial justifica manejo diferenciado',
                'acciones': [
                    'Zonificar lote para manejo por ambientes',
                    'Aplicación variable de fertilizantes',
                    'Ajustar densidad de siembra por zona',
                    'Monitoreo diferenciado por zona'
                ]
            })
        
        return recomendaciones
    
    def _resultado_vacio(self) -> Dict:
        """Retorna resultado vacío"""
        return {
            'metodo': 'ninguno',
            'umbrales': {},
            'distribucion': {},
            'interpretacion': {'homogeneidad': 'sin_datos'}
        }
