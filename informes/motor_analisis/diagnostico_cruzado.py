"""
Motor de Diagnóstico Cruzado Multi-Índice
=========================================

Realiza diagnósticos agronómicos integrando múltiples índices vegetativos
para detectar patrones complejos y generar recomendaciones fundamentadas.

Características:
- Análisis combinado de NDVI, NDMI, SAVI y otros índices
- Detección de patrones cruzados (ej: vigor bajo + humedad baja)
- Diagnósticos diferenciales basados en combinaciones de índices
- Recomendaciones ponderadas por confianza de datos
- Integración con reporte técnico y proveniencia

Ejemplos de diagnósticos cruzados:
- NDVI bajo + NDMI bajo → Estrés hídrico severo
- NDVI alto + NDMI bajo → Maduración o senescencia
- NDVI bajo + NDMI alto → Problema nutricional o enfermedad
- SAVI-NDVI divergente → Alta influencia del suelo
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .procesador_multiindice import ProcesadorMultiIndice, TipoIndice
from .reporte_tecnico import ReporteTecnico, NivelConfianza, ReglaAgronomica
from .proveniencia_datos import RegistradorProveniencia

logger = logging.getLogger(__name__)


@dataclass
class PatronCruzado:
    """Patrón detectado al comparar múltiples índices"""
    nombre: str
    descripcion: str
    indices_involucrados: List[str]
    condiciones: Dict[str, any]  # Condiciones que definen el patrón
    interpretacion_agronomica: str
    severidad: str  # 'baja', 'media', 'alta'
    recomendaciones: List[str]
    confianza_requerida: float = 0.6  # Confianza mínima para diagnosticar


class MotorDiagnosticoCruzado:
    """
    Motor principal de diagnóstico multi-índice
    
    Coordina el análisis de múltiples índices vegetativos y genera
    diagnósticos técnicos basados en reglas agronómicas validadas.
    """
    
    def __init__(self, tipo_cultivo: str = None):
        """
        Inicializa motor
        
        Args:
            tipo_cultivo: Tipo de cultivo para ajustar umbrales
        """
        self.tipo_cultivo = tipo_cultivo
        self.procesador = ProcesadorMultiIndice()
        self.patrones = self._definir_patrones_cruzados()
    
    def _definir_patrones_cruzados(self) -> List[PatronCruzado]:
        """
        Define patrones de diagnóstico cruzado
        
        Cada patrón representa una combinación específica de estados
        de índices que indica una condición agronómica particular.
        """
        return [
            # PATRÓN 1: Estrés hídrico severo
            PatronCruzado(
                nombre="estres_hidrico_severo",
                descripcion="Bajo vigor combinado con baja humedad",
                indices_involucrados=['ndvi', 'ndmi'],
                condiciones={
                    'ndvi': ('<=', 0.4),
                    'ndmi': ('<=', 0.1),
                    'ndvi_tendencia': ('==', 'deterioro'),
                },
                interpretacion_agronomica=(
                    "El cultivo presenta estrés hídrico severo, evidenciado por "
                    "bajo vigor vegetativo (NDVI) combinado con bajo contenido de "
                    "humedad (NDMI). Esta condición puede causar pérdidas significativas "
                    "de rendimiento si no se corrige urgentemente."
                ),
                severidad='alta',
                recomendaciones=[
                    "Implementar riego inmediato con monitoreo de humedad del suelo",
                    "Evaluar sistema de riego y distribución de agua en parcela",
                    "Considerar aplicación de agentes anti-transpirantes si disponible",
                    "Monitorear diariamente hasta observar recuperación"
                ],
                confianza_requerida=0.7
            ),
            
            # PATRÓN 2: Estrés hídrico moderado
            PatronCruzado(
                nombre="estres_hidrico_moderado",
                descripcion="Vigor moderado con humedad descendente",
                indices_involucrados=['ndvi', 'ndmi'],
                condiciones={
                    'ndvi': ('between', (0.4, 0.6)),
                    'ndmi': ('<', 0.2),
                    'ndmi_tendencia': ('==', 'deterioro')
                },
                interpretacion_agronomica=(
                    "Se detecta estrés hídrico moderado. Aunque el vigor vegetativo "
                    "aún se mantiene en niveles aceptables, la humedad está descendiendo. "
                    "Acción preventiva ahora puede evitar pérdidas futuras."
                ),
                severidad='media',
                recomendaciones=[
                    "Programar riego preventivo en los próximos 3-5 días",
                    "Monitorear evolución de NDMI semanalmente",
                    "Verificar condiciones de pronóstico meteorológico",
                    "Preparar sistema de riego para intervención si es necesario"
                ],
                confianza_requerida=0.6
            ),
            
            # PATRÓN 3: Maduración o senescencia natural
            PatronCruzado(
                nombre="maduracion_natural",
                descripcion="Vigor descendente pero humedad adecuada",
                indices_involucrados=['ndvi', 'ndmi'],
                condiciones={
                    'ndvi_tendencia': ('==', 'deterioro'),
                    'ndmi': ('>=', 0.3),
                    'ndvi': ('between', (0.4, 0.7))
                },
                interpretacion_agronomica=(
                    "El descenso de NDVI con humedad adecuada sugiere maduración natural "
                    "del cultivo o entrada en fase de senescencia. Esto es normal en "
                    "cultivos que se aproximan a cosecha."
                ),
                severidad='baja',
                recomendaciones=[
                    "Evaluar estado fenológico del cultivo en campo",
                    "Planificar fecha de cosecha según cronograma",
                    "Reducir aplicaciones de insumos si el cultivo está en maduración",
                    "Monitorear para detectar cosecha óptima"
                ],
                confianza_requerida=0.65
            ),
            
            # PATRÓN 4: Problema nutricional o fitosanitario
            PatronCruzado(
                nombre="problema_nutricional",
                descripcion="Bajo vigor con humedad suficiente",
                indices_involucrados=['ndvi', 'ndmi'],
                condiciones={
                    'ndvi': ('<=', 0.5),
                    'ndmi': ('>=', 0.3),
                    'ndvi_tendencia': ('in', ['deterioro', 'estable'])
                },
                interpretacion_agronomica=(
                    "Vigor bajo a pesar de humedad suficiente indica posible deficiencia "
                    "nutricional, problema fitosanitario (plagas/enfermedades) o estrés "
                    "abiótico no hídrico (temperatura, compactación, salinidad)."
                ),
                severidad='media',
                recomendaciones=[
                    "Inspección de campo para detectar plagas, enfermedades o síntomas nutricionales",
                    "Análisis de suelo para evaluar disponibilidad de nutrientes",
                    "Considerar aplicación foliar de micronutrientes si deficiencia es evidente",
                    "Revisar drenaje del suelo (exceso de humedad puede causar problemas radiculares)"
                ],
                confianza_requerida=0.65
            ),
            
            # PATRÓN 5: Desarrollo óptimo
            PatronCruzado(
                nombre="desarrollo_optimo",
                descripcion="Alto vigor con humedad adecuada",
                indices_involucrados=['ndvi', 'ndmi'],
                condiciones={
                    'ndvi': ('>=', 0.7),
                    'ndmi': ('>=', 0.3),
                    'ndvi_tendencia': ('in', ['mejora', 'mejora_leve', 'estable'])
                },
                interpretacion_agronomica=(
                    "El cultivo presenta condiciones óptimas de desarrollo, con alto vigor "
                    "vegetativo y humedad adecuada. Mantener prácticas actuales de manejo."
                ),
                severidad='baja',
                recomendaciones=[
                    "Mantener programa de riego actual",
                    "Continuar con plan de nutrición establecido",
                    "Monitoreo preventivo de plagas y enfermedades",
                    "Documentar prácticas actuales como referencia para futuros ciclos"
                ],
                confianza_requerida=0.7
            ),
            
            # PATRÓN 6: Alta influencia del suelo
            PatronCruzado(
                nombre="influencia_suelo",
                descripcion="SAVI-NDVI divergen significativamente",
                indices_involucrados=['ndvi', 'savi'],
                condiciones={
                    'ndvi_savi_ratio': ('>', 1.2)  # NDVI significativamente mayor que SAVI
                },
                interpretacion_agronomica=(
                    "La divergencia entre SAVI y NDVI indica alta reflectancia del suelo, "
                    "común en cultivos con cobertura incompleta o en etapas tempranas. "
                    "SAVI proporciona estimación más precisa en estas condiciones."
                ),
                severidad='baja',
                recomendaciones=[
                    "Priorizar SAVI sobre NDVI para análisis en esta parcela",
                    "Evaluar densidad de siembra y cobertura del suelo",
                    "Considerar prácticas de manejo de residuos o coberturas",
                    "Re-evaluar cuando el cultivo alcance mayor cobertura"
                ],
                confianza_requerida=0.6
            ),
            
            # PATRÓN 7: Exceso de humedad
            PatronCruzado(
                nombre="exceso_humedad",
                descripcion="Humedad muy alta con vigor afectado",
                indices_involucrados=['ndvi', 'ndmi'],
                condiciones={
                    'ndmi': ('>=', 0.6),
                    'ndvi': ('<', 0.6),
                    'ndvi_tendencia': ('==', 'deterioro')
                },
                interpretacion_agronomica=(
                    "NDMI muy alto combinado con NDVI bajo puede indicar exceso de humedad "
                    "o saturación del suelo, causando estrés radicular y reduciendo vigor."
                ),
                severidad='media',
                recomendaciones=[
                    "Verificar drenaje de la parcela",
                    "Suspender riego temporalmente",
                    "Inspeccionar sistema radicular en campo para detectar pudrición",
                    "Evaluar topografía y zonas de acumulación de agua",
                    "Considerar aplicación de fungicidas si hay riesgo de enfermedades radiculares"
                ],
                confianza_requerida=0.65
            ),
        ]
    
    def analizar_multiindice(
        self,
        datos: Dict[str, List[Dict]],
        metadatos: Dict[str, List] = None
    ) -> Dict:
        """
        Realiza análisis multi-índice completo
        
        Args:
            datos: Dict con listas de valores por índice
                   Ej: {'ndvi': [{'periodo': '2024-01', 'valor': 0.65}, ...],
                        'ndmi': [...], 'savi': [...]}
            metadatos: Metadatos de imágenes por índice (opcional)
            
        Returns:
            Diccionario con análisis completo y diagnóstico cruzado
        """
        logger.info("=" * 70)
        logger.info("🔬 ANÁLISIS MULTI-ÍNDICE INICIADO")
        logger.info("=" * 70)
        
        # Procesar cada índice independientemente
        resultados_indices = {}
        for tipo_indice, valores_lista in datos.items():
            valores = np.array([v['valor'] for v in valores_lista])
            periodos = [v['periodo'] for v in valores_lista]
            
            resultado = self.procesador.procesar_indice(
                tipo_indice, valores, periodos
            )
            resultados_indices[tipo_indice] = resultado
            
            logger.info(
                f"✅ {tipo_indice.upper()}: promedio={resultado['estadisticas']['promedio']:.3f}, "
                f"tendencia={resultado['tendencia']['tipo']}"
            )
        
        # Análisis cruzado
        logger.info("\n🔍 Realizando análisis cruzado...")
        patrones_detectados = self._detectar_patrones_cruzados(resultados_indices)
        
        # Generar diagnóstico consolidado
        diagnostico = self._generar_diagnostico_consolidado(
            resultados_indices, patrones_detectados
        )
        
        logger.info(f"✅ Análisis completado: {len(patrones_detectados)} patrones detectados")
        
        return {
            'indices_individuales': resultados_indices,
            'patrones_detectados': patrones_detectados,
            'diagnostico_consolidado': diagnostico,
            'timestamp': datetime.now().isoformat()
        }
    
    def _detectar_patrones_cruzados(
        self,
        resultados: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Detecta patrones cruzados en resultados de múltiples índices
        
        Args:
            resultados: Resultados de análisis individual de cada índice
            
        Returns:
            Lista de patrones detectados con severidad y recomendaciones
        """
        patrones_detectados = []
        
        for patron in self.patrones:
            # Verificar si tenemos todos los índices necesarios
            indices_disponibles = [
                idx for idx in patron.indices_involucrados
                if idx in resultados and resultados[idx]['estadisticas']
            ]
            
            if len(indices_disponibles) < len(patron.indices_involucrados):
                continue  # No hay datos suficientes
            
            # Evaluar condiciones del patrón
            cumple = self._evaluar_condiciones_patron(patron, resultados)
            
            if cumple:
                logger.info(f"🎯 Patrón detectado: {patron.nombre}")
                patrones_detectados.append({
                    'nombre': patron.nombre,
                    'descripcion': patron.descripcion,
                    'interpretacion': patron.interpretacion_agronomica,
                    'severidad': patron.severidad,
                    'recomendaciones': patron.recomendaciones,
                    'indices_utilizados': patron.indices_involucrados,
                    'confianza_requerida': patron.confianza_requerida
                })
        
        return patrones_detectados
    
    def _evaluar_condiciones_patron(
        self,
        patron: PatronCruzado,
        resultados: Dict[str, Dict]
    ) -> bool:
        """
        Evalúa si se cumplen las condiciones de un patrón
        
        Args:
            patron: Patrón a evaluar
            resultados: Resultados de análisis de índices
            
        Returns:
            True si se cumplen todas las condiciones
        """
        for condicion, criterio in patron.condiciones.items():
            # Desempacar criterio (puede ser tupla de 2 o 3 elementos)
            if isinstance(criterio, tuple):
                if len(criterio) == 2:
                    operador, valor_referencia = criterio
                else:
                    # Si tiene más elementos, tomar los primeros 2
                    operador, valor_referencia = criterio[0], criterio[1]
            else:
                # Si no es tupla, asumir igualdad
                operador, valor_referencia = '==', criterio
            
            # Parsear condición (ej: 'ndvi', 'tendencia_ndvi', 'ndvi_savi_ratio')
            partes = condicion.split('_', 1)
            indice_base = partes[0]
            
            if indice_base not in resultados:
                return False
            
            resultado_indice = resultados[indice_base]
            
            # Obtener valor a comparar
            if condicion.endswith('_tendencia') or 'tendencia' in condicion:
                if 'tendencia' not in resultado_indice or not resultado_indice['tendencia']:
                    return False
                valor_actual = resultado_indice['tendencia']['tipo']
            elif '_' in condicion and 'ratio' in condicion:
                # Ratio entre índices (ej: ndvi_savi_ratio)
                idx1, idx2 = condicion.replace('_ratio', '').split('_')
                if idx1 in resultados and idx2 in resultados:
                    val1 = resultados[idx1]['estadisticas']['promedio']
                    val2 = resultados[idx2]['estadisticas']['promedio']
                    valor_actual = val1 / val2 if val2 != 0 else 1.0
                else:
                    return False
            else:
                # Valor promedio del índice
                if not resultado_indice['estadisticas']:
                    return False
                valor_actual = resultado_indice['estadisticas']['promedio']
            
            # Evaluar operador
            if operador == '<=':
                if not (valor_actual <= valor_referencia):
                    return False
            elif operador == '>=':
                if not (valor_actual >= valor_referencia):
                    return False
            elif operador == '<':
                if not (valor_actual < valor_referencia):
                    return False
            elif operador == '>':
                if not (valor_actual > valor_referencia):
                    return False
            elif operador == '==':
                if valor_actual != valor_referencia:
                    return False
            elif operador == 'between':
                # valor_referencia debe ser tupla/lista con (min, max)
                if isinstance(valor_referencia, (tuple, list)) and len(valor_referencia) == 2:
                    min_val, max_val = valor_referencia
                    if not (min_val <= valor_actual <= max_val):
                        return False
                else:
                    # Si no es tupla válida, saltar esta condición
                    logger.warning(f"Condición 'between' con valor inválido: {valor_referencia}")
                    return False
            elif operador == 'in':
                if valor_actual not in valor_referencia:
                    return False
        
        return True
    
    def _generar_diagnostico_consolidado(
        self,
        resultados: Dict[str, Dict],
        patrones: List[Dict]
    ) -> Dict:
        """
        Genera diagnóstico consolidado integrando todos los análisis
        
        Args:
            resultados: Resultados de índices individuales
            patrones: Patrones cruzados detectados
            
        Returns:
            Diccionario con diagnóstico consolidado
        """
        # Resumen de estado por índice
        estados = {}
        for indice, resultado in resultados.items():
            if resultado['estadisticas']:
                estados[indice] = {
                    'valor': resultado['estadisticas']['promedio'],
                    'clasificacion': resultado['estado_actual']['clasificacion'],
                    'tendencia': resultado['tendencia']['tipo'],
                    'interpretacion': resultado['interpretacion']
                }
        
        # Priorizar patrones por severidad
        severidades = {'alta': 3, 'media': 2, 'baja': 1}
        patrones_ordenados = sorted(
            patrones,
            key=lambda p: severidades.get(p['severidad'], 0),
            reverse=True
        )
        
        # Conclusión principal
        if patrones_ordenados and patrones_ordenados[0]['severidad'] == 'alta':
            conclusion_principal = patrones_ordenados[0]['interpretacion']
        elif 'ndvi' in estados:
            conclusion_principal = estados['ndvi']['interpretacion']
        else:
            conclusion_principal = "Análisis completado. Ver detalles por índice."
        
        # Recomendaciones consolidadas (sin duplicados)
        recomendaciones_set = set()
        recomendaciones_lista = []
        
        for patron in patrones_ordenados:
            for rec in patron['recomendaciones']:
                if rec not in recomendaciones_set:
                    recomendaciones_set.add(rec)
                    recomendaciones_lista.append({
                        'texto': rec,
                        'prioridad': patron['severidad'],
                        'fuente_patron': patron['nombre']
                    })
        
        return {
            'conclusion_principal': conclusion_principal,
            'estados_indices': estados,
            'patrones_activos': len(patrones),
            'severidad_maxima': patrones_ordenados[0]['severidad'] if patrones_ordenados else 'baja',
            'recomendaciones': recomendaciones_lista[:10],  # Top 10
            'numero_indices_analizados': len(resultados)
        }


# Función de utilidad para uso rápido
def analizar_parcela(
    datos_ndvi: List[Dict],
    datos_ndmi: List[Dict] = None,
    datos_savi: List[Dict] = None,
    tipo_cultivo: str = None
) -> Dict:
    """
    Función de utilidad para análisis rápido de parcela
    
    Args:
        datos_ndvi: Lista con [{'periodo': 'YYYY-MM', 'valor': float}, ...]
        datos_ndmi: Lista con datos NDMI (opcional)
        datos_savi: Lista con datos SAVI (opcional)
        tipo_cultivo: Tipo de cultivo (opcional)
        
    Returns:
        Diccionario con análisis completo
        
    Example:
        >>> resultado = analizar_parcela(
        ...     datos_ndvi=[
        ...         {'periodo': '2024-01', 'valor': 0.65},
        ...         {'periodo': '2024-02', 'valor': 0.68},
        ...     ],
        ...     tipo_cultivo='maíz'
        ... )
    """
    motor = MotorDiagnosticoCruzado(tipo_cultivo)
    
    datos = {'ndvi': datos_ndvi}
    if datos_ndmi:
        datos['ndmi'] = datos_ndmi
    if datos_savi:
        datos['savi'] = datos_savi
    
    return motor.analizar_multiindice(datos)
