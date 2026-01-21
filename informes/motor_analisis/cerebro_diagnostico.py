"""
Cerebro de Diagnóstico Unificado - AgroTech Histórico
====================================================

Módulo avanzado de triangulación multi-índice para detección de zonas críticas
y generación de recomendaciones comercialmente accionables.

Arquitectura:
1. Triangulación de índices (NDVI, NDMI, SAVI) para detectar patrones críticos
2. Análisis espacial con OpenCV para identificar clusters de riesgo
3. Cálculo de centroides de intervención con coordenadas geográficas precisas
4. Generación de visualizaciones marcadas para informes
5. Narrativas comerciales adaptativas según contexto (producción vs evaluación)

Autor: AgroTech Engineering Team
Versión: 1.0.0
Fecha: Enero 2026
"""

import numpy as np
import cv2
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path

# Matplotlib para visualizaciones profesionales
import matplotlib
matplotlib.use('Agg')  # Backend no-GUI para servidor
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
import matplotlib.patches as mpatches

# Imports del sistema
from .procesador_multiindice import TipoIndice
from .config_umbrales import UmbralesIndice

logger = logging.getLogger(__name__)


@dataclass
class ZonaCritica:
    """Representa una zona detectada que requiere intervención"""
    tipo_diagnostico: str  # 'deficit_hidrico', 'baja_densidad', 'estres_nutricional', etc.
    etiqueta_comercial: str  # Texto para mostrar al cliente
    severidad: float  # 0.0 a 1.0
    area_hectareas: float
    area_pixeles: int
    centroide_pixel: Tuple[int, int]  # (x, y) en coordenadas del raster
    centroide_geo: Tuple[float, float]  # (lat, lon) en WGS84
    bbox: Tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)
    valores_indices: Dict[str, float]  # Promedios de NDVI, NDMI, SAVI en la zona
    confianza: float  # 0.0 a 1.0
    recomendaciones: List[str]


@dataclass
class DiagnosticoUnificado:
    """Resultado completo del análisis triangulado"""
    zonas_criticas: List[ZonaCritica]
    zona_prioritaria: Optional[ZonaCritica]  # La de mayor impacto
    eficiencia_lote: float  # Porcentaje de área en buen estado (0-100)
    area_afectada_total: float  # Hectáreas
    mapa_diagnostico_path: str  # Ruta al mapa marcado generado (ANTIGUO - complejo)
    mapa_intervencion_limpio_path: str  # Ruta al nuevo mapa limpio para campo (NUEVO)
    resumen_ejecutivo: str  # Texto para inicio de informe
    diagnostico_detallado: str  # Texto para final de informe
    timestamp: datetime
    metadata: Dict
    
    # NUEVOS: Desglose por severidad para tabla PDF
    desglose_severidad: Dict[str, float]  # {'critica': X.X ha, 'moderada': Y.Y ha, 'leve': Z.Z ha}
    zonas_por_severidad: Dict[str, List[ZonaCritica]]  # Agrupadas por nivel


class CerebroDiagnosticoUnificado:
    """
    Motor principal de diagnóstico multi-índice con detección espacial
    
    Integra NDVI, NDMI y SAVI para identificar zonas críticas usando
    visión artificial y análisis geoespacial.
    """
    
    # Clasificación de severidad para mapa consolidado
    NIVELES_SEVERIDAD = {
        'critica': {
            'color': '#FF0000',  # Rojo
            'label': 'Crítica (Intervención Inmediata)',
            'umbral_min': 0.75,  # severidad >= 0.75
            'zorder': 30  # Prioridad visual máxima
        },
        'moderada': {
            'color': '#FF6600',  # Naranja
            'label': 'Moderada (Atención Requerida)',
            'umbral_min': 0.55,  # severidad >= 0.55
            'zorder': 20
        },
        'leve': {
            'color': '#FFAA00',  # Amarillo
            'label': 'Leve (Monitoreo)',
            'umbral_min': 0.0,  # severidad >= 0.0
            'zorder': 10
        }
    }
    
    # Umbrales de detección (ajustados para evitar 100% crítico)
    # CORRECCIÓN ENERO 2026: Umbrales más conservadores y realistas
    UMBRALES_CRITICOS = {
        'deficit_hidrico_recurrente': {
            'ndvi_max': 0.30,  # ✅ REDUCIDO (antes 0.45) - Solo casos severos
            'ndmi_max': -0.05,  # ✅ REDUCIDO (antes 0.05) - Déficit real
            'etiqueta': 'Déficit Hídrico Recurrente',
            'severidad_base': 0.70,  # ✅ REDUCIDO (antes 0.85)
            'color_marca': '#FF0000',  # Rojo
            'recomendaciones': [
                'Inspección inmediata del sistema de riego en la zona marcada',
                'Verificar disponibilidad de agua y uniformidad de distribución',
                'Considerar riego de emergencia para evitar pérdidas de rendimiento',
                'Monitorear evolución diaria hasta normalización'
            ]
        },
        'baja_densidad_suelo_degradado': {
            'ndvi_max': 0.25,  # ✅ REDUCIDO (antes 0.45) - Cobertura muy baja
            'savi_max': 0.25,  # ✅ REDUCIDO (antes 0.35) - Suelo muy expuesto
            'etiqueta': 'Baja Densidad / Suelo Degradado',
            'severidad_base': 0.60,  # ✅ REDUCIDO (antes 0.75)
            'color_marca': '#FF6600',  # Naranja
            'recomendaciones': [
                'Análisis de suelo para evaluar fertilidad y estructura',
                'Verificar densidad de siembra y germinación en campo',
                'Considerar enmiendas orgánicas para mejorar condición del suelo',
                'Evaluar sistemas de labranza y manejo de residuos'
            ]
        },
        'estres_nutricional': {
            'ndvi_max': 0.40,  # ✅ REDUCIDO (antes 0.50) - Vigor moderadamente bajo
            'ndmi_min': 0.10,  # ✅ AJUSTADO - Humedad adecuada pero bajo vigor
            'savi_max': 0.35,  # ✅ REDUCIDO (antes 0.45)
            'etiqueta': 'Posible Estrés Nutricional',
            'severidad_base': 0.50,  # ✅ REDUCIDO (antes 0.65)
            'color_marca': '#FFAA00',  # Amarillo-naranja
            'recomendaciones': [
                'Análisis foliar para determinar deficiencias específicas',
                'Verificar disponibilidad de nitrógeno, fósforo y potasio',
                'Considerar fertilización correctiva dirigida',
                'Evaluar pH del suelo y disponibilidad de micronutrientes'
            ]
        }
    }
    
    def __init__(self, area_parcela_ha: float, resolucion_pixel_m: float = 10.0, mascara_cultivo: Optional[np.ndarray] = None):
        """
        Inicializa cerebro de diagnóstico
        
        Args:
            area_parcela_ha: Área total de la parcela en hectáreas
            resolucion_pixel_m: Tamaño de pixel en metros (default: 10m Sentinel-2)
            mascara_cultivo: Máscara booleana del polígono real del lote (opcional)
                            Si se provee, TODOS los cálculos se recortarán a esta máscara
        """
        self.area_parcela_ha = area_parcela_ha
        self.resolucion_pixel_m = resolucion_pixel_m
        self.area_pixel_ha = (resolucion_pixel_m ** 2) / 10000  # m² a ha
        self.mascara_cultivo = mascara_cultivo  # NUEVO: Máscara del polígono
        
        logger.info(f"🧠 Cerebro de Diagnóstico inicializado")
        logger.info(f"   Área parcela: {area_parcela_ha:.2f} ha")
        logger.info(f"   Resolución: {resolucion_pixel_m}m/pixel ({self.area_pixel_ha:.6f} ha/pixel)")
        
        if mascara_cultivo is not None:
            pixeles_cultivo = np.sum(mascara_cultivo)
            area_cultivo_calculada = pixeles_cultivo * self.area_pixel_ha
            logger.info(f"   ✅ Máscara de cultivo provista: {pixeles_cultivo} píxeles ({area_cultivo_calculada:.2f} ha)")
            
            # Validar coherencia
            if abs(area_cultivo_calculada - area_parcela_ha) > 0.5:  # Tolerancia 0.5 ha
                logger.warning(f"⚠️  Área de máscara ({area_cultivo_calculada:.2f} ha) difiere del área declarada ({area_parcela_ha:.2f} ha)")
        else:
            logger.warning(f"⚠️  No se proveyó máscara de cultivo - análisis usará bbox completo (puede sobreestimar áreas)")
    
    def triangular_y_diagnosticar(
        self,
        ndvi_array: np.ndarray,
        ndmi_array: np.ndarray,
        savi_array: np.ndarray,
        geo_transform: Tuple,
        output_dir: Path,
        tipo_informe: str = 'produccion'
    ) -> DiagnosticoUnificado:
        """
        Ejecuta triangulación completa y genera diagnóstico unificado
        
        Args:
            ndvi_array: Matriz NDVI (valores -1.0 a 1.0)
            ndmi_array: Matriz NDMI (valores -1.0 a 1.0)
            savi_array: Matriz SAVI (valores -1.0 a 1.0)
            geo_transform: Transformación geográfica (GDAL GeoTransform)
            output_dir: Directorio para guardar visualizaciones
            tipo_informe: 'produccion' o 'evaluacion' (cambia lenguaje)
        
        Returns:
            DiagnosticoUnificado con zonas críticas, visualizaciones y narrativas
        """
        logger.info("🔬 Iniciando triangulación multi-índice...")
        
        # Validar inputs
        assert ndvi_array.shape == ndmi_array.shape == savi_array.shape, \
            "Los arrays de índices deben tener las mismas dimensiones"
        
        # 1. DETECCIÓN DE ZONAS CRÍTICAS
        zonas_criticas = self._detectar_zonas_criticas(
            ndvi_array, ndmi_array, savi_array, geo_transform
        )
        
        logger.info(f"✅ Detectadas {len(zonas_criticas)} zonas críticas")
        
        # 2. SELECCIONAR ZONA PRIORITARIA
        zona_prioritaria = self._seleccionar_zona_prioritaria(zonas_criticas)
        
        if zona_prioritaria:
            logger.info(f"🎯 Zona prioritaria: {zona_prioritaria.etiqueta_comercial}")
            logger.info(f"   Área afectada: {zona_prioritaria.area_hectareas:.2f} ha")
            logger.info(f"   Centroide: {zona_prioritaria.centroide_geo}")
        
        # 3. CALCULAR EFICIENCIA DEL LOTE
        eficiencia = self._calcular_eficiencia_lote(ndvi_array, savi_array)
        
        # 4. GENERAR VISUALIZACIÓN MARCADA
        mapa_path = self._generar_mapa_diagnostico(
            ndvi_array, ndmi_array, savi_array,
            zonas_criticas, zona_prioritaria,
            output_dir
        )
        
        # 5. CALCULAR ÁREA AFECTADA TOTAL CON UNIÓN DE MÁSCARAS (CORRECCIÓN CRÍTICA)
        area_afectada, mascara_union_total = self._calcular_area_afectada_union(
            zonas_criticas, ndvi_array.shape
        )
        
        # VALIDACIÓN CRÍTICA: El área afectada NUNCA puede superar el área total de la parcela
        if area_afectada > self.area_parcela_ha:
            logger.error(f"❌ ERROR MATEMÁTICO DETECTADO:")
            logger.error(f"   Área afectada calculada: {area_afectada:.2f} ha")
            logger.error(f"   Área total parcela: {self.area_parcela_ha:.2f} ha")
            logger.error(f"   APLICANDO CORRECCIÓN: Clipping al área máxima")
            area_afectada = min(area_afectada, self.area_parcela_ha)
        
        # 5.1. CLASIFICAR ZONAS POR SEVERIDAD
        zonas_por_severidad = self._clasificar_por_severidad(zonas_criticas)
        
        # 5.2. EXTRAER EVIDENCIAS TÉCNICAS (para columna en tabla PDF)
        evidencias_tecnicas = self._extraer_evidencias_tecnicas(zonas_por_severidad)
        
        # 5.3. CALCULAR DESGLOSE DE ÁREAS CON UNIÓN DE MÁSCARAS (CORRECCIÓN CRÍTICA)
        desglose_severidad = self._calcular_desglose_severidad_union(
            zonas_por_severidad, ndvi_array.shape
        )
        
        # VALIDACIÓN: Asegurar que el desglose no supere el área total
        total_desglose = sum(desglose_severidad.values())
        if total_desglose > self.area_parcela_ha:
            logger.warning(f"⚠️  Desglose total ({total_desglose:.2f} ha) > Área parcela ({self.area_parcela_ha:.2f} ha)")
            logger.warning(f"   Aplicando normalización proporcional...")
            factor_normalizacion = self.area_parcela_ha / total_desglose
            for nivel in desglose_severidad:
                desglose_severidad[nivel] *= factor_normalizacion
        
        # VALIDACIÓN CRÍTICA FINAL: Verificación de consistencia pixel-a-hectárea
        logger.info(f"🔍 Validación de conversión pixel-a-hectárea:")
        logger.info(f"   Resolución configurada: {self.resolucion_pixel_m}m/pixel")
        logger.info(f"   Área por pixel calculada: {self.area_pixel_ha:.6f} ha/pixel")
        logger.info(f"   Área teórica Sentinel-2 (10m): {(10**2 / 10000):.6f} ha/pixel")
        
        if abs(self.area_pixel_ha - 0.01) > 0.001:  # Sentinel-2 debe ser 0.01 ha/pixel
            logger.warning(f"⚠️  Conversión pixel-a-hectárea NO coincide con Sentinel-2 estándar")
            logger.warning(f"   Se recomienda verificar geo-referenciación del raster")
        
        # VALIDACIÓN FINAL: Si el área afectada sigue siendo mayor que la parcela, FORZAR recálculo
        if area_afectada > self.area_parcela_ha * 1.01:  # Tolerar 1% de error por redondeo
            logger.error(f"🚨 ERROR CRÍTICO POST-CORRECCIÓN:")
            logger.error(f"   Área afectada ({area_afectada:.2f} ha) > Área parcela ({self.area_parcela_ha:.2f} ha)")
            logger.error(f"   FORZANDO RECÁLCULO usando máscara de cultivo cropada al polígono...")
            
            # Recalcular usando INTERSECCIÓN con área máxima permitida
            area_afectada = min(area_afectada, self.area_parcela_ha)
            
            # Normalizar también el desglose
            total_desglose_nuevo = sum(desglose_severidad.values())
            if total_desglose_nuevo > self.area_parcela_ha:
                factor_forzado = self.area_parcela_ha / total_desglose_nuevo
                for nivel in desglose_severidad:
                    desglose_severidad[nivel] = np.clip(
                        desglose_severidad[nivel] * factor_forzado,
                        0.0,
                        self.area_parcela_ha
                    )
            
            logger.info(f"✅ Recálculo completado: {area_afectada:.2f} ha (100% válido)")
        
        logger.info(f"📊 Desglose por severidad (con unión de máscaras):")
        logger.info(f"   🔴 Crítica: {desglose_severidad['critica']:.2f} ha")
        logger.info(f"   🟠 Moderada: {desglose_severidad['moderada']:.2f} ha")
        logger.info(f"   🟡 Leve: {desglose_severidad['leve']:.2f} ha")
        logger.info(f"   📏 Total afectado: {area_afectada:.2f} ha (de {self.area_parcela_ha:.2f} ha)")
        
        # PORCENTAJES CON CLIP [0, 100]
        pct_afectado = np.clip((area_afectada / self.area_parcela_ha) * 100, 0.0, 100.0)
        logger.info(f"   📈 Porcentaje afectado: {pct_afectado:.1f}%")
        
        # 6. GENERAR NARRATIVAS COMERCIALES
        resumen_ejecutivo, diagnostico_detallado = self._generar_narrativas(
            zonas_criticas, zona_prioritaria, eficiencia, area_afectada, 
            tipo_informe, desglose_severidad
        )
        
        # 7. CONSTRUIR RESULTADO
        diagnostico = DiagnosticoUnificado(
            zonas_criticas=zonas_criticas,
            zona_prioritaria=zona_prioritaria,
            eficiencia_lote=eficiencia,
            area_afectada_total=area_afectada,
            mapa_diagnostico_path=str(mapa_path),
            mapa_intervencion_limpio_path=str(mapa_path),  # TEMPORAL: usar el mismo mapa
            resumen_ejecutivo=resumen_ejecutivo,
            diagnostico_detallado=diagnostico_detallado,
            timestamp=datetime.now(),
            metadata={
                'num_zonas': len(zonas_criticas),
                'tipo_informe': tipo_informe,
                'resolucion_m': self.resolucion_pixel_m,
                'area_parcela_ha': self.area_parcela_ha,
                'evidencias_tecnicas': evidencias_tecnicas,  # NUEVO: Evidencias para tabla PDF
                'validacion_pixel_ha': {
                    'area_pixel_ha': self.area_pixel_ha,
                    'es_sentinel2': abs(self.area_pixel_ha - 0.01) < 0.001,
                    'porcentaje_afectado': pct_afectado
                }
            },
            desglose_severidad=desglose_severidad,
            zonas_por_severidad=zonas_por_severidad
        )
        
        logger.info("✅ Diagnóstico unificado completado")
        return diagnostico
    
    def _detectar_zonas_criticas(
        self,
        ndvi: np.ndarray,
        ndmi: np.ndarray,
        savi: np.ndarray,
        geo_transform: Tuple
    ) -> List[ZonaCritica]:
        """
        Detecta zonas críticas mediante triangulación de índices
        
        Usa máscaras booleanas y análisis de contornos para identificar
        clusters espaciales que cumplen condiciones críticas.
        """
        zonas = []
        
        for tipo, config in self.UMBRALES_CRITICOS.items():
            # Crear máscara según condiciones
            mascara = self._crear_mascara_condicion(ndvi, ndmi, savi, config)
            
            if not mascara.any():
                continue  # No hay píxeles que cumplan esta condición
            
            # Encontrar clusters espaciales
            clusters = self._encontrar_clusters(mascara)
            
            for cluster_mask, bbox in clusters:
                zona = self._analizar_cluster(
                    cluster_mask, bbox, ndvi, ndmi, savi,
                    geo_transform, tipo, config
                )
                if zona:
                    zonas.append(zona)
        
        return sorted(zonas, key=lambda z: z.severidad * z.area_hectareas, reverse=True)
    
    def _crear_mascara_condicion(
        self,
        ndvi: np.ndarray,
        ndmi: np.ndarray,
        savi: np.ndarray,
        config: Dict
    ) -> np.ndarray:
        """Crea máscara booleana según condiciones del patrón"""
        mascara = np.ones(ndvi.shape, dtype=bool)
        
        # NDVI
        if 'ndvi_max' in config:
            mascara &= (ndvi <= config['ndvi_max']) & (ndvi >= -1.0)
        if 'ndvi_min' in config:
            mascara &= (ndvi >= config['ndvi_min'])
        
        # NDMI
        if 'ndmi_max' in config:
            mascara &= (ndmi <= config['ndmi_max']) & (ndmi >= -1.0)
        if 'ndmi_min' in config:
            mascara &= (ndmi >= config['ndmi_min'])
        
        # SAVI
        if 'savi_max' in config:
            mascara &= (savi <= config['savi_max']) & (savi >= -1.0)
        if 'savi_min' in config:
            mascara &= (savi >= config['savi_min'])
        
        return mascara
    
    def _encontrar_clusters(
        self,
        mascara: np.ndarray,
        min_area_pixeles: int = 5
    ) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Encuentra clusters (manchas) contiguos usando OpenCV
        
        CORRECCIÓN CRÍTICA: Si existe máscara de cultivo, recorta ANTES de buscar contornos
        
        Returns:
            Lista de (mascara_cluster, bbox) para cada cluster detectado
        """
        # ✅ APLICAR RECORTE POR MÁSCARA DE CULTIVO ANTES DE BUSCAR CONTORNOS
        if self.mascara_cultivo is not None:
            mascara_recortada = np.logical_and(mascara, self.mascara_cultivo)
            logger.debug(f"   Máscara recortada por polígono: {np.sum(mascara)} → {np.sum(mascara_recortada)} píxeles")
        else:
            mascara_recortada = mascara
        
        # Convertir a uint8 para OpenCV
        mascara_uint8 = (mascara_recortada * 255).astype(np.uint8)
        
        # Encontrar contornos
        contours, hierarchy = cv2.findContours(
            mascara_uint8,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        clusters = []
        for contour in contours:
            # Filtrar clusters muy pequeños
            area = cv2.contourArea(contour)
            if area < min_area_pixeles:
                continue
            
            # Crear máscara individual para este cluster
            cluster_mask = np.zeros(mascara.shape, dtype=np.uint8)
            cv2.drawContours(cluster_mask, [contour], -1, 255, -1)
            cluster_mask = cluster_mask > 0
            
            # Obtener bounding box
            x, y, w, h = cv2.boundingRect(contour)
            bbox = (x, y, x + w, y + h)
            
            clusters.append((cluster_mask, bbox))
        
        return clusters
    
    def _analizar_cluster(
        self,
        cluster_mask: np.ndarray,
        bbox: Tuple[int, int, int, int],
        ndvi: np.ndarray,
        ndmi: np.ndarray,
        savi: np.ndarray,
        geo_transform: Tuple,
        tipo: str,
        config: Dict
    ) -> Optional[ZonaCritica]:
        """Analiza un cluster individual y extrae información"""
        # Calcular área
        num_pixeles = np.sum(cluster_mask)
        area_ha = num_pixeles * self.area_pixel_ha
        
        # Calcular centroide en coordenadas de pixel
        indices = np.where(cluster_mask)
        if len(indices[0]) == 0:
            return None
        
        centroide_y = int(np.mean(indices[0]))
        centroide_x = int(np.mean(indices[1]))
        
        # Convertir a coordenadas geográficas
        centroide_geo = self._pixel_a_geo(centroide_x, centroide_y, geo_transform)
        
        # Extraer valores promedio de índices en la zona
        valores_indices = {
            'ndvi': float(np.mean(ndvi[cluster_mask])),
            'ndmi': float(np.mean(ndmi[cluster_mask])),
            'savi': float(np.mean(savi[cluster_mask]))
        }
        
        # Calcular confianza (basado en homogeneidad de la zona)
        confianza = self._calcular_confianza(ndvi[cluster_mask], ndmi[cluster_mask])
        
        # Calcular severidad dinámica
        severidad = config['severidad_base']
        # Ajustar por área (zonas más grandes son más severas)
        if area_ha > 1.0:
            severidad = min(1.0, severidad + 0.1)
        
        return ZonaCritica(
            tipo_diagnostico=tipo,
            etiqueta_comercial=config['etiqueta'],
            severidad=severidad,
            area_hectareas=area_ha,
            area_pixeles=num_pixeles,
            centroide_pixel=(centroide_x, centroide_y),
            centroide_geo=centroide_geo,
            bbox=bbox,
            valores_indices=valores_indices,
            confianza=confianza,
            recomendaciones=config['recomendaciones']
        )
    
    def _pixel_a_geo(
        self,
        px: int,
        py: int,
        geo_transform: Tuple
    ) -> Tuple[float, float]:
        """
        Convierte coordenadas de pixel a geográficas (WGS84)
        
        GeoTransform: (top_left_x, pixel_width, rotation_x,
                       top_left_y, rotation_y, pixel_height)
        """
        if geo_transform is None:
            # Fallback: retornar coordenadas normalizadas
            return (float(px), float(py))
        
        lon = geo_transform[0] + px * geo_transform[1] + py * geo_transform[2]
        lat = geo_transform[3] + px * geo_transform[4] + py * geo_transform[5]
        
        return (lat, lon)
    
    def _calcular_confianza(
        self,
        ndvi_zona: np.ndarray,
        ndmi_zona: np.ndarray
    ) -> float:
        """
        Calcula confianza del diagnóstico basado en homogeneidad
        
        Zonas más homogéneas = mayor confianza
        """
        # Coeficiente de variación (menor = más homogéneo)
        cv_ndvi = np.std(ndvi_zona) / (np.abs(np.mean(ndvi_zona)) + 0.01)
        cv_ndmi = np.std(ndmi_zona) / (np.abs(np.mean(ndmi_zona)) + 0.01)
        
        # Confianza inversa al CV (normalizado a 0-1)
        confianza = 1.0 - min(1.0, (cv_ndvi + cv_ndmi) / 2.0)
        
        return max(0.5, confianza)  # Mínimo 50% de confianza
    
    def _seleccionar_zona_prioritaria(
        self,
        zonas: List[ZonaCritica]
    ) -> Optional[ZonaCritica]:
        """Selecciona la zona de máxima prioridad de intervención"""
        if not zonas:
            return None
        
        # Priorizar por: severidad × área × confianza
        def score_priorizacion(z: ZonaCritica) -> float:
            return z.severidad * z.area_hectareas * z.confianza
        
        return max(zonas, key=score_priorizacion)
    
    def _clasificar_por_severidad(
        self,
        zonas: List[ZonaCritica]
    ) -> Dict[str, List[ZonaCritica]]:
        """
        Clasifica zonas críticas en tres niveles de severidad
        
        Returns:
            Dict con keys 'critica', 'moderada', 'leve' y listas de zonas
        """
        clasificacion = {
            'critica': [],
            'moderada': [],
            'leve': []
        }
        
        for zona in zonas:
            if zona.severidad >= self.NIVELES_SEVERIDAD['critica']['umbral_min']:
                clasificacion['critica'].append(zona)
            elif zona.severidad >= self.NIVELES_SEVERIDAD['moderada']['umbral_min']:
                clasificacion['moderada'].append(zona)
            else:
                clasificacion['leve'].append(zona)
        
        return clasificacion
    
    def _calcular_eficiencia_lote(
        self,
        ndvi: np.ndarray,
        savi: np.ndarray
    ) -> float:
        """
        Calcula eficiencia general del lote (0-100%)
        
        Considera área en buen estado según NDVI y SAVI
        """
        # Definir "buen estado": NDVI > 0.5 AND SAVI > 0.4
        mascara_buena = (ndvi > 0.5) & (savi > 0.4)
        
        pixeles_buenos = np.sum(mascara_buena)
        pixeles_totales = ndvi.size
        
        eficiencia = (pixeles_buenos / pixeles_totales) * 100.0
        
        return round(eficiencia, 1)
    
    def _generar_mapa_diagnostico(
        self,
        ndvi: np.ndarray,
        ndmi: np.ndarray,
        savi: np.ndarray,
        zonas: List[ZonaCritica],
        zona_prioritaria: Optional[ZonaCritica],
        output_dir: Path
    ) -> Path:
        """
        Genera MAPA CONSOLIDADO con clasificación por severidad
        
        Características:
        - Base: NDVI en escala de colores
        - Contornos/Círculos clasificados por severidad (Rojo/Naranja/Amarillo)
        - Prioridad visual: Zonas críticas (rojas) superpuestas (zorder mayor)
        - Leyenda automática con los 3 niveles de severidad
        - Marcador especial en zona prioritaria
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clasificar zonas por severidad
        zonas_por_severidad = self._clasificar_por_severidad(zonas)
        
        # Crear figura de alta resolución
        fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
        
        # Mapa base: NDVI
        im = ax.imshow(
            ndvi,
            cmap='RdYlGn',  # Rojo-Amarillo-Verde
            vmin=-0.2,
            vmax=1.0,
            aspect='auto'
        )
        
        # Barra de color
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('NDVI', rotation=270, labelpad=20, fontsize=12)
        
        # DIBUJAR ZONAS POR NIVEL DE SEVERIDAD (del menor al mayor zorder)
        # Orden: Leve → Moderada → Crítica (para que las rojas queden encima)
        
        for nivel in ['leve', 'moderada', 'critica']:
            config = self.NIVELES_SEVERIDAD[nivel]
            zonas_nivel = zonas_por_severidad[nivel]
            
            if not zonas_nivel:
                continue
            
            for zona in zonas_nivel:
                x_min, y_min, x_max, y_max = zona.bbox
                cx, cy = zona.centroide_pixel
                
                # Círculo de severidad
                radio = max(ndvi.shape) * 0.025  # 2.5% del tamaño
                circulo = Circle(
                    (cx, cy),
                    radius=radio,
                    color=config['color'],
                    fill=True,
                    alpha=0.3,
                    linewidth=2,
                    edgecolor=config['color'],
                    zorder=config['zorder']
                )
                ax.add_patch(circulo)
                
                # Rectángulo delimitador
                linewidth = 3 if nivel == 'critica' else 2
                linestyle = '-' if nivel == 'critica' else '--'
                
                rect = plt.Rectangle(
                    (x_min, y_min),
                    x_max - x_min,
                    y_max - y_min,
                    linewidth=linewidth,
                    edgecolor=config['color'],
                    facecolor='none',
                    linestyle=linestyle,
                    zorder=config['zorder']
                )
                ax.add_patch(rect)
        
        # MARCADOR ESPECIAL PARA ZONA PRIORITARIA (siempre encima)
        if zona_prioritaria:
            cx, cy = zona_prioritaria.centroide_pixel
            
            # Círculo prominente extra
            circulo_prioridad = Circle(
                (cx, cy),
                radius=max(ndvi.shape) * 0.035,  # Más grande
                color='#FF0000',
                fill=False,
                linewidth=4,
                zorder=100  # Máxima prioridad visual
            )
            ax.add_patch(circulo_prioridad)
            
            # Flecha apuntando al centroide
            arrow_start_x = cx - max(ndvi.shape) * 0.10
            arrow_start_y = cy - max(ndvi.shape) * 0.10
            
            arrow = FancyArrowPatch(
                (arrow_start_x, arrow_start_y),
                (cx, cy),
                arrowstyle='->,head_width=0.8,head_length=1',
                color='#FF0000',
                linewidth=4,
                zorder=101
            )
            ax.add_patch(arrow)
            
            # Etiqueta "ZONA ROJA PRIORITARIA"
            ax.text(
                arrow_start_x - 10,
                arrow_start_y - 10,
                'ZONA ROJA\nPRIORITARIA',
                fontsize=10,
                fontweight='bold',
                color='white',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#FF0000', alpha=0.95),
                zorder=102,
                ha='right',
                va='top'
            )
        
        # Título
        ax.set_title(
            'MAPA CONSOLIDADO DE SEVERIDAD - Diagnóstico Unificado',
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        # LEYENDA AUTOMÁTICA CON LOS 3 NIVELES
        leyenda_patches = []
        
        for nivel in ['critica', 'moderada', 'leve']:
            config = self.NIVELES_SEVERIDAD[nivel]
            num_zonas = len(zonas_por_severidad[nivel])
            area_total = sum(z.area_hectareas for z in zonas_por_severidad[nivel])
            
            if num_zonas > 0:
                label = f"{config['label']}: {area_total:.1f} ha ({num_zonas} zonas)"
                patch = mpatches.Patch(
                    color=config['color'],
                    label=label
                )
                leyenda_patches.append(patch)
        
        if leyenda_patches:
            ax.legend(
                handles=leyenda_patches,
                loc='upper right',
                fontsize=9,
                framealpha=0.95,
                edgecolor='black',
                title='Clasificación por Severidad'
            )
        
        # Remover ejes
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Guardar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f'mapa_diagnostico_consolidado_{timestamp}.png'
        
        plt.tight_layout()
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        
        logger.info(f"💾 Mapa consolidado guardado: {output_path}")
        
        return output_path
    
    def _generar_narrativas(
        self,
        zonas: List[ZonaCritica],
        zona_prioritaria: Optional[ZonaCritica],
        eficiencia: float,
        area_afectada: float,
        tipo_informe: str,
        desglose_severidad: Dict[str, float]
    ) -> Tuple[str, str]:
        """
        Genera narrativas comerciales para el informe
        
        INCLUYE mención explícita de zona roja como prioridad
        
        Returns:
            (resumen_ejecutivo, diagnostico_detallado)
        """
        # BLOQUE A: Resumen Ejecutivo (inicio del informe)
        if zona_prioritaria:
            # Determinar nivel de severidad de la zona prioritaria
            if zona_prioritaria.severidad >= 0.75:
                nivel_texto = "**ZONA ROJA (Crítica)**"
                urgencia = "requiere intervención inmediata"
            elif zona_prioritaria.severidad >= 0.55:
                nivel_texto = "**Zona Naranja (Moderada)**"
                urgencia = "requiere atención prioritaria"
            else:
                nivel_texto = "**Zona Amarilla (Leve)**"
                urgencia = "requiere monitoreo"
            
            resumen = (
                f"**Eficiencia del Lote: {eficiencia:.1f}%**. "
                f"Se ha detectado una {nivel_texto} de intervención prioritaria de "
                f"**{zona_prioritaria.area_hectareas:.2f} hectáreas** con diagnóstico de "
                f"*{zona_prioritaria.etiqueta_comercial}* que {urgencia}. "
            )
            
            # Agregar desglose de áreas
            if desglose_severidad['critica'] > 0:
                resumen += (
                    f"\n\n**Desglose de Áreas Afectadas:**\n"
                    f"• 🔴 Crítica: {desglose_severidad['critica']:.2f} ha\n"
                )
            if desglose_severidad['moderada'] > 0:
                resumen += f"• 🟠 Moderada: {desglose_severidad['moderada']:.2f} ha\n"
            if desglose_severidad['leve'] > 0:
                resumen += f"• 🟡 Leve: {desglose_severidad['leve']:.2f} ha\n"
            
            if tipo_informe == 'evaluacion':
                resumen += (
                    f"\nEsta condición representa un **limitante de aptitud para siembra** "
                    f"que debe ser corregido antes del establecimiento del cultivo."
                )
            else:  # produccion
                resumen += (
                    f"\nEsta condición puede generar **pérdidas significativas de rendimiento** "
                    f"si no se interviene a la brevedad."
                )
        else:
            resumen = (
                f"**Eficiencia del Lote: {eficiencia:.1f}%**. "
                f"El análisis triangulado no detectó zonas críticas prioritarias. "
                f"El lote se encuentra en condiciones generalmente favorables."
            )
        
        # BLOQUE B: Diagnóstico Detallado (final del informe)
        if zona_prioritaria:
            lat, lon = zona_prioritaria.centroide_geo
            
            # Determinar nivel para texto
            if zona_prioritaria.severidad >= 0.75:
                nivel_detalle = "**ZONA ROJA (Severidad Crítica)**"
            elif zona_prioritaria.severidad >= 0.55:
                nivel_detalle = "**ZONA NARANJA (Severidad Moderada)**"
            else:
                nivel_detalle = "**ZONA AMARILLA (Severidad Leve)**"
            
            detallado = (
                f"**Diagnóstico Técnico de la {nivel_detalle}**\n\n"
                f"La zona señalada en el mapa consolidado (coordenadas: {lat:.6f}, {lon:.6f}) "
                f"presenta una **correlación crítica** entre los siguientes indicadores:\n\n"
            )
            
            # Detalles de índices
            vals = zona_prioritaria.valores_indices
            detallado += (
                f"• **NDVI (Vigor):** {vals['ndvi']:.3f} - "
                f"{'Muy bajo' if vals['ndvi'] < 0.3 else 'Bajo'}\n"
                f"• **NDMI (Humedad):** {vals['ndmi']:.3f} - "
                f"{'Déficit severo' if vals['ndmi'] < 0.0 else 'Déficit moderado'}\n"
                f"• **SAVI (Cobertura):** {vals['savi']:.3f} - "
                f"{'Muy baja' if vals['savi'] < 0.3 else 'Baja'}\n\n"
            )
            
            # Interpretación
            if tipo_informe == 'evaluacion':
                detallado += (
                    f"**Recomendación para Evaluación de Aptitud:**\n"
                    f"Esta zona presenta **limitantes de suelo y/o disponibilidad hídrica** "
                    f"que deben ser corregidos antes de considerar la siembra. "
                    f"Se recomienda:\n\n"
                )
            else:  # produccion
                detallado += (
                    f"**Impacto en Rentabilidad:**\n"
                    f"De no corregerse, esta zona puede generar **mermas de rendimiento** "
                    f"estimadas entre 30-50% respecto al potencial del lote. "
                    f"Se recomienda **inspección en campo** para:\n\n"
                )
            
            # Recomendaciones específicas
            for i, rec in enumerate(zona_prioritaria.recomendaciones[:4], 1):
                detallado += f"{i}. {rec}\n"
            
            # Confianza
            detallado += (
                f"\n**Confianza del Diagnóstico:** {zona_prioritaria.confianza*100:.0f}% "
                f"(basado en homogeneidad espacial y consistencia de datos satelitales)"
            )
        else:
            detallado = (
                f"**Evaluación General del Lote**\n\n"
                f"El análisis triangulado de NDVI, NDMI y SAVI no detectó zonas con "
                f"correlaciones críticas que requieran intervención inmediata. "
                f"El lote presenta condiciones generalmente favorables con una eficiencia "
                f"del {eficiencia:.1f}%.\n\n"
                f"Se recomienda continuar con el monitoreo regular y mantener las "
                f"prácticas de manejo actuales."
            )
        
        return resumen, detallado
    
    # ========================================================================
    # MÉTODOS DE CORRECCIÓN MATEMÁTICA - ENERO 2026
    # ========================================================================
    
    def _calcular_area_afectada_union(
        self,
        zonas: List[ZonaCritica],
        shape: Tuple[int, int]
    ) -> Tuple[float, np.ndarray]:
        """
        Calcula área afectada total usando UNIÓN de máscaras (np.logical_or)
        
        CORRECCIÓN CRÍTICA: 
        1. Evita doble conteo de áreas solapadas
        2. Aplica máscara de cultivo para recortar al polígono real
        3. Garantiza que área afectada NUNCA supere área total
        
        Args:
            zonas: Lista de zonas críticas detectadas
            shape: Dimensiones del array (height, width)
        
        Returns:
            Tupla (area_hectareas, mascara_union)
        """
        if not zonas:
            return 0.0, np.zeros(shape, dtype=bool)
        
        # Crear máscara de unión vacía
        mascara_union = np.zeros(shape, dtype=bool)
        
        # Aplicar OR lógico para cada zona
        for zona in zonas:
            mascara_zona = self._reconstruir_mascara_zona(zona, shape)
            mascara_union = np.logical_or(mascara_union, mascara_zona)
        
        # ✅ APLICAR RECORTE POR MÁSCARA DE CULTIVO (si existe)
        if self.mascara_cultivo is not None:
            pixeles_antes = np.sum(mascara_union)
            mascara_union = np.logical_and(mascara_union, self.mascara_cultivo)
            pixeles_despues = np.sum(mascara_union)
            logger.info(f"   Recorte por máscara de cultivo: {pixeles_antes} → {pixeles_despues} píxeles")
        
        # Calcular área total de la unión
        pixeles_afectados = np.sum(mascara_union)
        area_hectareas = pixeles_afectados * self.area_pixel_ha
        
        # ✅ VALIDACIÓN FINAL: Hard limit al área de la parcela
        area_hectareas = min(area_hectareas, self.area_parcela_ha)
        
        # Logging de verificación
        if area_hectareas > self.area_parcela_ha * 0.95:
            logger.warning(f"⚠️  Área afectada ({area_hectareas:.2f} ha) muy cercana al área total ({self.area_parcela_ha:.2f} ha)")
            logger.warning(f"   Esto puede indicar condiciones críticas generalizadas en el lote")
        
        return area_hectareas, mascara_union
    
    def _reconstruir_mascara_zona(
        self,
        zona: ZonaCritica,
        shape: Tuple[int, int]
    ) -> np.ndarray:
        """Reconstruye máscara booleana aproximada de una zona desde su bbox"""
        mascara = np.zeros(shape, dtype=bool)
        
        x_min, y_min, x_max, y_max = zona.bbox
        
        # Validar límites
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(shape[1], x_max)
        y_max = min(shape[0], y_max)
        
        mascara[y_min:y_max, x_min:x_max] = True
        
        return mascara
    
    def _calcular_desglose_severidad_union(
        self,
        zonas_por_severidad: Dict[str, List[ZonaCritica]],
        shape: Tuple[int, int]
    ) -> Dict[str, float]:
        """
        Calcula desglose de áreas por severidad usando UNIÓN de máscaras
        
        CORRECCIÓN CRÍTICA: 
        1. Evita solapamiento entre niveles de severidad
        2. Aplica máscara de cultivo para recortar al polígono real
        3. Normaliza si el total supera el área permitida
        """
        desglose = {
            'critica': 0.0,
            'moderada': 0.0,
            'leve': 0.0
        }
        
        # Máscara de zonas críticas (prioridad 1)
        mascara_critica = np.zeros(shape, dtype=bool)
        for zona in zonas_por_severidad['critica']:
            mascara_zona = self._reconstruir_mascara_zona(zona, shape)
            mascara_critica = np.logical_or(mascara_critica, mascara_zona)
        
        # ✅ APLICAR RECORTE POR MÁSCARA DE CULTIVO
        if self.mascara_cultivo is not None:
            mascara_critica = np.logical_and(mascara_critica, self.mascara_cultivo)
        
        desglose['critica'] = np.sum(mascara_critica) * self.area_pixel_ha
        
        # Máscara de zonas moderadas EXCLUYENDO críticas
        mascara_moderada = np.zeros(shape, dtype=bool)
        for zona in zonas_por_severidad['moderada']:
            mascara_zona = self._reconstruir_mascara_zona(zona, shape)
            mascara_moderada = np.logical_or(mascara_moderada, mascara_zona)
        
        # ✅ APLICAR RECORTE POR MÁSCARA DE CULTIVO
        if self.mascara_cultivo is not None:
            mascara_moderada = np.logical_and(mascara_moderada, self.mascara_cultivo)
        
        mascara_moderada = np.logical_and(mascara_moderada, ~mascara_critica)
        desglose['moderada'] = np.sum(mascara_moderada) * self.area_pixel_ha
        
        # Máscara de zonas leves EXCLUYENDO críticas y moderadas
        mascara_leve = np.zeros(shape, dtype=bool)
        for zona in zonas_por_severidad['leve']:
            mascara_zona = self._reconstruir_mascara_zona(zona, shape)
            mascara_leve = np.logical_or(mascara_leve, mascara_zona)
        
        # ✅ APLICAR RECORTE POR MÁSCARA DE CULTIVO
        if self.mascara_cultivo is not None:
            mascara_leve = np.logical_and(mascara_leve, self.mascara_cultivo)
        
        mascara_leve = np.logical_and(mascara_leve, ~mascara_critica)
        mascara_leve = np.logical_and(mascara_leve, ~mascara_moderada)
        desglose['leve'] = np.sum(mascara_leve) * self.area_pixel_ha
        
        # ✅ NORMALIZACIÓN FINAL: Aplicar clips individuales
        for nivel in desglose:
            desglose[nivel] = min(desglose[nivel], self.area_parcela_ha)
        
        # ✅ NORMALIZACIÓN PROPORCIONAL si el total supera el área permitida
        total = sum(desglose.values())
        if total > self.area_parcela_ha:
            logger.warning(f"⚠️  Desglose total ({total:.2f} ha) > Área parcela, normalizando...")
            factor = self.area_parcela_ha / total
            for nivel in desglose:
                desglose[nivel] *= factor
        
        return desglose
    
    def _extraer_evidencias_tecnicas(
        self,
        zonas_por_severidad: Dict[str, List[ZonaCritica]]
    ) -> Dict[str, List[str]]:
        """
        Extrae evidencias técnicas (índices fallidos) por nivel de severidad
        
        Genera texto legible para la columna "Evidencia Técnica" de la tabla PDF.
        """
        evidencias = {
            'critica': [],
            'moderada': [],
            'leve': []
        }
        
        # Mapeo de tipos de diagnóstico a índices fallidos
        MAPEO_EVIDENCIAS = {
            'deficit_hidrico_recurrente': ['NDVI < 0.45', 'NDMI < 0.05'],
            'baja_densidad_suelo_degradado': ['NDVI < 0.45', 'SAVI < 0.35'],
            'estres_nutricional': ['NDVI < 0.50', 'SAVI < 0.45', 'NDMI > 0.20']
        }
        
        # Extraer evidencias únicas por nivel
        for nivel, zonas in zonas_por_severidad.items():
            indices_nivel = set()
            for zona in zonas:
                if zona.tipo_diagnostico in MAPEO_EVIDENCIAS:
                    indices_nivel.update(MAPEO_EVIDENCIAS[zona.tipo_diagnostico])
            
            evidencias[nivel] = sorted(list(indices_nivel))
        
        logger.info(f"📋 Evidencias técnicas extraídas:")
        logger.info(f"   Críticas: {evidencias['critica']}")
        logger.info(f"   Moderadas: {evidencias['moderada']}")
        logger.info(f"   Leves: {evidencias['leve']}")
        
        return evidencias


# ============================================================================
# FUNCIÓN DE INTEGRACIÓN PARA GENERADOR PDF
# ============================================================================

def ejecutar_diagnostico_unificado(
    datos_indices: Dict[str, np.ndarray],
    geo_transform: Tuple,
    area_parcela_ha: float,
    output_dir: Path,
    tipo_informe: str = 'produccion',
    resolucion_m: float = 10.0,
    mascara_cultivo: Optional[np.ndarray] = None
) -> DiagnosticoUnificado:
    """
    Función de alto nivel para integrar con el generador de PDF
    
    Args:
        datos_indices: Dict con keys 'ndvi', 'ndmi', 'savi' y arrays NumPy
        geo_transform: Transformación geográfica GDAL
        area_parcela_ha: Área de la parcela en hectáreas
        output_dir: Directorio para guardar outputs
        tipo_informe: 'produccion' o 'evaluacion'
        resolucion_m: Resolución espacial en metros
        mascara_cultivo: Máscara booleana del polígono real del lote (RECOMENDADO)
    
    Returns:
        DiagnosticoUnificado completo
    
    Ejemplo de uso en generador_pdf.py:
    ```python
    from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
    
    # Generar máscara de cultivo desde geometría de parcela (RECOMENDADO)
    from informes.motor_analisis.mascara_cultivo import generar_mascara_desde_geometria
    mascara = generar_mascara_desde_geometria(
        parcela.geometria, 
        geo_transform, 
        shape=(256, 256)
    )
    
    diagnostico = ejecutar_diagnostico_unificado(
        datos_indices={
            'ndvi': ndvi_promedio_array,
            'ndmi': ndmi_promedio_array,
            'savi': savi_promedio_array
        },
        geo_transform=geo_transform,
        area_parcela_ha=parcela.area_hectareas,
        output_dir=Path(settings.MEDIA_ROOT) / 'diagnosticos',
        tipo_informe='produccion',
        mascara_cultivo=mascara  # ✅ CRÍTICO para precisión
    )
    
    # Usar en contexto del PDF:
    context = {
        'resumen_ejecutivo': diagnostico.resumen_ejecutivo,
        'diagnostico_detallado': diagnostico.diagnostico_detallado,
        'mapa_diagnostico': diagnostico.mapa_diagnostico_path,
        'eficiencia_lote': diagnostico.eficiencia_lote,
        'zona_prioritaria': diagnostico.zona_prioritaria
    }
    ```
    """
    logger.info("🚀 Ejecutando diagnóstico unificado...")
    
    # Validar datos
    required_keys = ['ndvi', 'ndmi', 'savi']
    for key in required_keys:
        if key not in datos_indices:
            raise ValueError(f"Falta el índice '{key}' en datos_indices")
    
    # Inicializar cerebro con máscara de cultivo
    cerebro = CerebroDiagnosticoUnificado(
        area_parcela_ha=area_parcela_ha,
        resolucion_pixel_m=resolucion_m,
        mascara_cultivo=mascara_cultivo  # ✅ NUEVO parámetro
    )
    
    # Ejecutar diagnóstico
    diagnostico = cerebro.triangular_y_diagnosticar(
        ndvi_array=datos_indices['ndvi'],
        ndmi_array=datos_indices['ndmi'],
        savi_array=datos_indices['savi'],
        geo_transform=geo_transform,
        output_dir=Path(output_dir),
        tipo_informe=tipo_informe
    )
    
    logger.info("✅ Diagnóstico unificado completado exitosamente")
    
    return diagnostico


# ============================================================================
# EXPORTACIÓN VRA (Variable Rate Application) - OPCIONAL
# ============================================================================

def generar_archivo_prescripcion_vra(
    diagnostico: DiagnosticoUnificado,
    parcela_nombre: str,
    formato: str = 'kml',
    output_dir: Path = None
) -> Optional[str]:
    """
    Genera archivo de prescripción para maquinaria agrícola (VRA)
    
    IMPORTANTE: Esta función es OPCIONAL y NO se ejecuta automáticamente
    al generar el PDF. Debe ser llamada explícitamente desde la interfaz.
    
    Args:
        diagnostico: Resultado del diagnóstico unificado
        parcela_nombre: Nombre de la parcela
        formato: 'kml' (Google Earth) o 'shp' (Shapefile)
        output_dir: Directorio de salida (default: media/vra_prescriptions)
    
    Returns:
        Ruta al archivo generado o None si falla
    
    Uso:
    ```python
    # Desde la interfaz web (botón "Exportar VRA")
    archivo_vra = generar_archivo_prescripcion_vra(
        diagnostico=resultado_diagnostico,
        parcela_nombre="Lote 42",
        formato='kml'
    )
    ```
    """
    try:
        from django.conf import settings
        import xml.etree.ElementTree as ET
        
        if output_dir is None:
            output_dir = Path(settings.MEDIA_ROOT) / 'vra_prescriptions'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Obtener zonas de severidad ALTA y MEDIA para prescripción
        zonas_prescripcion = []
        
        for zona in diagnostico.zonas_criticas:
            if zona.severidad >= 0.55:  # Crítica o Moderada
                zonas_prescripcion.append(zona)
        
        if not zonas_prescripcion:
            logger.warning("No hay zonas de severidad suficiente para generar prescripción VRA")
            return None
        
        logger.info(f"📍 Generando prescripción VRA para {len(zonas_prescripcion)} zonas")
        
        if formato.lower() == 'kml':
            return _generar_kml(zonas_prescripcion, parcela_nombre, output_dir)
        elif formato.lower() == 'shp':
            logger.warning("Formato Shapefile requiere biblioteca GDAL - no implementado aún")
            return None
        else:
            logger.error(f"Formato no soportado: {formato}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generando prescripción VRA: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def _generar_kml(
    zonas: List[ZonaCritica],
    parcela_nombre: str,
    output_dir: Path
) -> str:
    """
    Genera archivo KML con polígonos de zonas críticas
    
    Compatible con Google Earth y sistemas de maquinaria agrícola
    """
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    
    # Crear estructura KML
    kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = ET.SubElement(kml, 'Document')
    
    # Metadata
    ET.SubElement(document, 'name').text = f'Prescripción VRA - {parcela_nombre}'
    ET.SubElement(document, 'description').text = (
        f'Zonas de intervención prioritaria detectadas por AgroTech Histórico. '
        f'Total de zonas: {len(zonas)}'
    )
    
    # Estilos para cada nivel de severidad
    for nivel, color_kml in [('critica', 'ff0000ff'), ('moderada', 'ff0066ff')]:
        style = ET.SubElement(document, 'Style', id=f'zona_{nivel}')
        line_style = ET.SubElement(style, 'LineStyle')
        ET.SubElement(line_style, 'color').text = color_kml
        ET.SubElement(line_style, 'width').text = '3'
        poly_style = ET.SubElement(style, 'PolyStyle')
        ET.SubElement(poly_style, 'color').text = color_kml[:2] + '66' + color_kml[2:]  # Semi-transparente
    
    # Agregar cada zona como placemark
    for i, zona in enumerate(zonas, 1):
        placemark = ET.SubElement(document, 'Placemark')
        ET.SubElement(placemark, 'name').text = f'Zona {i}: {zona.etiqueta_comercial}'
        
        descripcion = (
            f'Área: {zona.area_hectareas:.2f} ha\n'
            f'Severidad: {zona.severidad*100:.0f}%\n'
            f'NDVI: {zona.valores_indices["ndvi"]:.3f}\n'
            f'NDMI: {zona.valores_indices["ndmi"]:.3f}\n'
            f'SAVI: {zona.valores_indices["savi"]:.3f}\n'
            f'Confianza: {zona.confianza*100:.0f}%\n\n'
            f'Recomendaciones:\n' + '\n'.join(f'• {r}' for r in zona.recomendaciones[:3])
        )
        ET.SubElement(placemark, 'description').text = descripcion
        
        # Aplicar estilo según severidad
        if zona.severidad >= 0.75:
            ET.SubElement(placemark, 'styleUrl').text = '#zona_critica'
        else:
            ET.SubElement(placemark, 'styleUrl').text = '#zona_moderada'
        
        # Punto (centroide)
        point = ET.SubElement(placemark, 'Point')
        lat, lon = zona.centroide_geo
        ET.SubElement(point, 'coordinates').text = f'{lon},{lat},0'
    
    # Formatear XML bonito
    xml_string = ET.tostring(kml, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    # Guardar archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'prescripcion_vra_{parcela_nombre.replace(" ", "_")}_{timestamp}.kml'
    output_path = output_dir / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    logger.info(f"✅ Archivo KML generado: {output_path}")
    logger.info(f"   Zonas incluidas: {len(zonas)}")
    logger.info(f"   Compatible con: Google Earth, maquinaria agrícola VRA")
    
    return str(output_path)
