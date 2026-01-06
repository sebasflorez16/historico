"""
Generador de Diagnósticos Agronómicos
=====================================

Componente principal que integra todos los análisis y genera
diagnósticos técnicos, conclusiones y recomendaciones accionables.

Características:
- Integra análisis de múltiples índices
- Genera diagnósticos consolidados
- Produce recomendaciones priorizadas
- Crea resúmenes ejecutivos técnicos
"""

import numpy as np
from typing import Dict, List, Optional
import logging

from .procesador_indices import ProcesadorIndices
from .zonificador import ZonificadorProductivo
from .detector_anomalias import DetectorAnomalias
from .config_umbrales import ReglasRecomendaciones

logger = logging.getLogger(__name__)


class GeneradorDiagnosticos:
    """
    Generador principal de diagnósticos agronómicos
    
    Coordina todos los componentes del motor de análisis para producir
    diagnósticos técnicos completos y accionables.
    """
    
    def __init__(self, tipo_cultivo: str = None):
        """
        Inicializa generador
        
        Args:
            tipo_cultivo: Tipo de cultivo para ajustar umbrales
        """
        self.tipo_cultivo = tipo_cultivo
        self.procesador = ProcesadorIndices(tipo_cultivo)
        self.zonificador = ZonificadorProductivo()
        self.detector = DetectorAnomalias()
        self.reglas = ReglasRecomendaciones()
    
    def generar_diagnostico_completo(
        self,
        datos: List[Dict],
        incluir_zonificacion: bool = True
    ) -> Dict:
        """
        Genera diagnóstico completo del cultivo
        
        Args:
            datos: Lista de datos mensuales con índices
            incluir_zonificacion: Si incluir análisis de zonificación
            
        Returns:
            Diccionario con diagnóstico completo
        """
        logger.info("🔬 Iniciando generación de diagnóstico completo")
        
        # Procesar cada índice
        ndvi_result = self.procesador.procesar_serie_temporal(datos, 'ndvi')
        ndmi_result = self.procesador.procesar_serie_temporal(datos, 'ndmi')
        
        # SAVI (opcional)
        savi_result = None
        if any(d.get('savi') for d in datos):
            savi_result = self.procesador.procesar_serie_temporal(datos, 'savi')
        
        # Extraer valores para análisis adicional
        ndvi_valores = np.array([d.get('ndvi') for d in datos if d.get('ndvi') is not None])
        periodos = [d.get('periodo', f"P{i+1}") for i, d in enumerate(datos)]
        
        # Detectar eventos
        deterioros = self.detector.detectar_deterioros(ndvi_valores, periodos)
        recuperaciones = self.detector.detectar_recuperaciones(ndvi_valores, periodos)
        alertas = self.detector.generar_alertas(
            ndvi_result['estadisticas']['promedio'],
            ndvi_result['tendencia'],
            deterioros
        )
        
        # Zonificación (si se solicita)
        zonificacion = None
        if incluir_zonificacion and len(ndvi_valores) > 0:
            zonificacion = self.zonificador.zonificar(ndvi_valores)
            variabilidad = self.zonificador.calcular_variabilidad(ndvi_valores)
        else:
            variabilidad = None
        
        # Generar conclusiones
        conclusiones = self._generar_conclusiones(
            ndvi_result, ndmi_result, savi_result,
            deterioros, recuperaciones
        )
        
        # Generar recomendaciones
        recomendaciones = self._generar_recomendaciones(
            ndvi_result, ndmi_result, zonificacion,
            deterioros, alertas
        )
        
        # Resumen ejecutivo
        resumen = self._generar_resumen_ejecutivo(
            ndvi_result, ndmi_result, conclusiones
        )
        
        logger.info("✅ Diagnóstico completo generado exitosamente")
        
        return {
            'resumen_ejecutivo': resumen,
            'indices': {
                'ndvi': ndvi_result,
                'ndmi': ndmi_result,
                'savi': savi_result
            },
            'eventos': {
                'deterioros': deterioros,
                'recuperaciones': recuperaciones
            },
            'alertas': alertas,
            'zonificacion': zonificacion,
            'variabilidad': variabilidad,
            'conclusiones': conclusiones,
            'recomendaciones': recomendaciones,
            'metadatos': {
                'tipo_cultivo': self.tipo_cultivo,
                'n_observaciones': len(datos),
                'periodo_analisis': f"{periodos[0]} - {periodos[-1]}" if periodos else "N/A"
            }
        }
    
    def _generar_conclusiones(
        self,
        ndvi_result: Dict,
        ndmi_result: Dict,
        savi_result: Optional[Dict],
        deterioros: List[Dict],
        recuperaciones: List[Dict]
    ) -> List[str]:
        """
        Genera conclusiones técnicas del análisis
        
        Returns:
            Lista de conclusiones textuales
        """
        conclusiones = []
        
        # Conclusión sobre NDVI
        ndvi_prom = ndvi_result['estadisticas']['promedio']
        ndvi_estado = ndvi_result['estado']['etiqueta']
        conclusiones.append(
            f"El índice NDVI promedio es {ndvi_prom:.3f}, clasificado como '{ndvi_estado}', "
            f"con una puntuación de {ndvi_result['puntuacion']:.1f}/10."
        )
        
        # Conclusión sobre tendencia
        if ndvi_result['tendencia'].get('tiene_tendencia'):
            direccion = ndvi_result['tendencia']['direccion']
            cambio = ndvi_result['tendencia']['cambio_total_pct']
            conclusiones.append(
                f"Se observa una tendencia {direccion} con un cambio de {cambio:+.1f}% en el período analizado."
            )
        else:
            conclusiones.append("No se detecta una tendencia temporal clara en el período.")
        
        # Conclusión sobre NDMI
        ndmi_prom = ndmi_result['estadisticas']['promedio']
        ndmi_estado = ndmi_result['estado']['etiqueta']
        conclusiones.append(
            f"El contenido de humedad (NDMI = {ndmi_prom:.3f}) se clasifica como '{ndmi_estado}'."
        )
        
        # Conclusión sobre eventos
        if deterioros:
            conclusiones.append(
                f"Se detectaron {len(deterioros)} evento(s) de deterioro significativo que requieren atención."
            )
        
        if recuperaciones:
            conclusiones.append(
                f"Se registraron {len(recuperaciones)} período(s) de recuperación en el cultivo."
            )
        
        return conclusiones
    
    def _generar_recomendaciones(
        self,
        ndvi_result: Dict,
        ndmi_result: Dict,
        zonificacion: Optional[Dict],
        deterioros: List[Dict],
        alertas: List[Dict]
    ) -> List[Dict]:
        """
        Genera recomendaciones priorizadas
        
        Returns:
            Lista de recomendaciones con prioridad
        """
        recomendaciones = []
        
        ndvi_prom = ndvi_result['estadisticas']['promedio']
        ndmi_prom = ndmi_result['estadisticas']['promedio']
        
        # Recomendaciones por NDVI bajo
        if ndvi_prom < 0.5:
            prioridad = 'alta' if ndvi_prom < 0.4 else 'media'
            recomendaciones.append({
                'titulo': 'Mejorar Salud Vegetal',
                'prioridad': prioridad,
                'descripcion_tecnica': f'NDVI promedio ({ndvi_prom:.3f}) indica vigor vegetativo por debajo del óptimo',
                'descripcion_simple': 'El cultivo muestra signos de bajo vigor que requieren atención',
                'acciones': self.reglas.RECOMENDACIONES_NDVI_BAJO[:3],
                'impacto_esperado': 'Mejora en desarrollo vegetativo y productividad',
                'tiempo_implementacion': '1-2 semanas'
            })
        
        # Recomendaciones por NDMI bajo
        if ndmi_prom < 0.2:
            prioridad = 'alta' if ndmi_prom < 0.0 else 'media'
            recomendaciones.append({
                'titulo': 'Manejo Hídrico',
                'prioridad': prioridad,
                'descripcion_tecnica': f'NDMI ({ndmi_prom:.3f}) indica déficit hídrico',
                'descripcion_simple': 'El cultivo puede estar experimentando estrés por falta de agua',
                'acciones': self.reglas.RECOMENDACIONES_NDMI_BAJO[:3],
                'impacto_esperado': 'Mejora en estado hídrico y reducción de estrés',
                'tiempo_implementacion': 'Inmediato'
            })
        
        # Recomendaciones por variabilidad
        if zonificacion and zonificacion['interpretacion'].get('requiere_manejo_diferenciado'):
            recomendaciones.append({
                'titulo': 'Implementar Manejo Sitio-Específico',
                'prioridad': 'media',
                'descripcion_tecnica': 'La alta variabilidad espacial justifica agricultura de precisión',
                'descripcion_simple': 'El lote presenta zonas muy diferentes que se beneficiarían de manejo individualizado',
                'acciones': self.reglas.RECOMENDACIONES_VARIABILIDAD_ALTA,
                'impacto_esperado': 'Optimización de insumos y mejora de productividad',
                'tiempo_implementacion': '1-2 meses (planificación)'
            })
        
        # Recomendaciones por deterioros
        if len(deterioros) > 0:
            recomendaciones.append({
                'titulo': 'Investigar Causas de Deterioro',
                'prioridad': 'alta',
                'descripcion_tecnica': f'Se detectaron {len(deterioros)} eventos de caída significativa',
                'descripcion_simple': 'El cultivo ha experimentado caídas bruscas que requieren investigación',
                'acciones': [
                    'Inspeccionar visualmente las áreas afectadas',
                    'Descartar plagas o enfermedades',
                    'Evaluar condiciones climáticas del período',
                    'Revisar prácticas de manejo recientes'
                ],
                'impacto_esperado': 'Identificación y corrección de problemas',
                'tiempo_implementacion': 'Inmediato'
            })
        
        # Ordenar por prioridad
        orden_prioridad = {'alta': 1, 'media': 2, 'baja': 3}
        recomendaciones.sort(key=lambda x: orden_prioridad.get(x['prioridad'], 4))
        
        return recomendaciones
    
    def _generar_resumen_ejecutivo(
        self,
        ndvi_result: Dict,
        ndmi_result: Dict,
        conclusiones: List[str]
    ) -> str:
        """
        Genera resumen ejecutivo técnico
        
        Returns:
            Texto de resumen ejecutivo
        """
        # Calcular puntuación general
        punt_ndvi = ndvi_result['puntuacion']
        punt_ndmi = ndmi_result['puntuacion']
        punt_general = (punt_ndvi + punt_ndmi) / 2
        
        # Determinar estado general
        if punt_general >= 8:
            estado = "EXCELENTE"
        elif punt_general >= 6:
            estado = "BUENO"
        elif punt_general >= 4:
            estado = "REGULAR"
        else:
            estado = "CRÍTICO"
        
        resumen = f"""
ESTADO GENERAL DEL CULTIVO: {estado} ({punt_general:.1f}/10)

Basado en análisis multi-temporal de índices vegetativos satelitales, el cultivo presenta:

- Índice de Salud (NDVI): {ndvi_result['estadisticas']['promedio']:.3f} - {ndvi_result['estado']['etiqueta']} (Puntuación: {punt_ndvi:.1f}/10)
- Índice Hídrico (NDMI): {ndmi_result['estadisticas']['promedio']:.3f} - {ndmi_result['estado']['etiqueta']} (Puntuación: {punt_ndmi:.1f}/10)
- Tendencia temporal: {ndvi_result['tendencia'].get('direccion', 'N/A').title()}
- Calidad de datos: {ndvi_result['calidad_datos']['calidad'].title()}

CONCLUSIONES PRINCIPALES:
{chr(10).join(f'• {c}' for c in conclusiones[:3])}

Este análisis se basa en procesamiento determinístico de datos satelitales Sentinel-2
y metodologías científicamente validadas de teledetección agrícola.
"""
        
        return resumen.strip()
