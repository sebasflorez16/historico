"""
Procesador Multi-Índice Unificado
=================================

Arquitectura extensible para procesar cualquier índice vegetativo
bajo una estructura común, facilitando análisis cruzados y comparativos.

Características:
- Registro dinámico de nuevos índices
- Procesamiento uniforme con estadísticas estandarizadas
- Metadatos completos por índice
- Validación automática de rangos válidos
- Soporte para análisis cruzados

Índices soportados:
- NDVI (Normalized Difference Vegetation Index)
- NDMI (Normalized Difference Moisture Index)
- SAVI (Soil-Adjusted Vegetation Index)
- EVI (Enhanced Vegetation Index) - futuro
- NDRE (Normalized Difference Red Edge) - futuro
- Cualquier índice personalizado
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
import logging

from .config_umbrales import UmbralesIndice
from .proveniencia_datos import RegistroIndice, MetadatosImagen

logger = logging.getLogger(__name__)


class TipoIndice(Enum):
    """Tipos de índices vegetativos"""
    NDVI = "ndvi"       # Vigor/biomasa
    NDMI = "ndmi"       # Humedad/estrés hídrico
    SAVI = "savi"       # Vegetación ajustada por suelo
    EVI = "evi"         # Vegetación mejorada
    NDRE = "ndre"       # Borde rojo (nitrógeno)
    CUSTOM = "custom"   # Índice personalizado


@dataclass
class DefinicionIndice:
    """
    Define un índice vegetativo y sus propiedades
    
    Permite agregar nuevos índices dinámicamente al sistema
    """
    tipo: TipoIndice
    nombre_completo: str
    descripcion: str
    rango_valido: Tuple[float, float]  # (min, max)
    rango_tipico: Tuple[float, float]  # (min_esperado, max_esperado)
    umbrales: UmbralesIndice
    interpretacion: Dict[str, str]  # Significado por nivel
    unidades: str = "adimensional"
    bandas_requeridas: List[str] = field(default_factory=list)
    formula: Optional[str] = None
    referencias: List[str] = field(default_factory=list)
    
    def validar_valor(self, valor: float) -> Tuple[bool, Optional[str]]:
        """
        Valida si un valor está en el rango válido
        
        Returns:
            (es_valido, mensaje_error)
        """
        if np.isnan(valor):
            return False, "Valor NaN"
        
        if valor < self.rango_valido[0] or valor > self.rango_valido[1]:
            return False, f"Fuera de rango válido {self.rango_valido}"
        
        if valor < self.rango_tipico[0] or valor > self.rango_tipico[1]:
            # Advertencia, no error
            logger.warning(
                f"{self.tipo.value.upper()} fuera de rango típico: {valor:.3f} "
                f"(esperado: {self.rango_tipico})"
            )
        
        return True, None
    
    def clasificar(self, valor: float) -> str:
        """Clasifica un valor según umbrales"""
        return self.umbrales.clasificar(valor)
    
    def interpretar(self, valor: float) -> str:
        """Retorna interpretación del valor"""
        clasificacion = self.clasificar(valor)
        return self.interpretacion.get(clasificacion, "Sin interpretación")


class RegistroIndices:
    """
    Registro central de definiciones de índices
    
    Permite agregar y consultar índices dinámicamente
    """
    
    def __init__(self):
        """Inicializa registro con índices estándar"""
        self._indices: Dict[str, DefinicionIndice] = {}
        self._registrar_indices_standard()
    
    def _registrar_indices_standard(self):
        """Registra índices vegetativos estándar"""
        # NDVI
        self.registrar(DefinicionIndice(
            tipo=TipoIndice.NDVI,
            nombre_completo="Normalized Difference Vegetation Index",
            descripcion="Mide vigor vegetativo y biomasa verde",
            rango_valido=(-1.0, 1.0),
            rango_tipico=(0.1, 0.9),
            umbrales=UmbralesIndice(
                muy_bajo=0.2,
                bajo=0.4,
                medio=0.6,
                alto=0.75,
                muy_alto=0.85
            ),
            interpretacion={
                'muy_bajo': 'Suelo desnudo o sin vegetación',
                'bajo': 'Vegetación escasa o muy estresada',
                'medio': 'Vegetación moderada',
                'alto': 'Vegetación saludable',
                'muy_alto': 'Vegetación muy densa y vigorosa'
            },
            bandas_requeridas=['NIR', 'Red'],
            formula='(NIR - Red) / (NIR + Red)',
            referencias=[
                'Rouse et al. (1974) - Monitoring vegetation systems',
                'Tucker (1979) - Red and photographic infrared linear combinations'
            ]
        ))
        
        # NDMI
        self.registrar(DefinicionIndice(
            tipo=TipoIndice.NDMI,
            nombre_completo="Normalized Difference Moisture Index",
            descripcion="Mide contenido de humedad y estrés hídrico",
            rango_valido=(-1.0, 1.0),
            rango_tipico=(-0.2, 0.6),
            umbrales=UmbralesIndice(
                muy_bajo=-0.2,
                bajo=0.1,
                medio=0.3,
                alto=0.5,
                muy_alto=0.7
            ),
            interpretacion={
                'muy_bajo': 'Estrés hídrico severo',
                'bajo': 'Estrés hídrico moderado',
                'medio': 'Humedad adecuada',
                'alto': 'Buena humedad',
                'muy_alto': 'Humedad óptima o saturación'
            },
            bandas_requeridas=['NIR', 'SWIR'],
            formula='(NIR - SWIR) / (NIR + SWIR)',
            referencias=[
                'Gao (1996) - NDWI for remote sensing of liquid water',
                'Wilson & Sader (2002) - Detection of forest harvest type'
            ]
        ))
        
        # SAVI
        self.registrar(DefinicionIndice(
            tipo=TipoIndice.SAVI,
            nombre_completo="Soil-Adjusted Vegetation Index",
            descripcion="NDVI ajustado por reflectancia del suelo",
            rango_valido=(-1.0, 1.0),
            rango_tipico=(0.0, 0.8),
            umbrales=UmbralesIndice(
                muy_bajo=0.15,
                bajo=0.3,
                medio=0.5,
                alto=0.65,
                muy_alto=0.8
            ),
            interpretacion={
                'muy_bajo': 'Predomina suelo desnudo',
                'bajo': 'Cobertura vegetal baja',
                'medio': 'Cobertura vegetal moderada',
                'alto': 'Buena cobertura vegetal',
                'muy_alto': 'Cobertura vegetal densa'
            },
            bandas_requeridas=['NIR', 'Red'],
            formula='((NIR - Red) / (NIR + Red + L)) * (1 + L), L=0.5',
            referencias=[
                'Huete (1988) - A soil-adjusted vegetation index (SAVI)',
                'Qi et al. (1994) - Modified SAVI'
            ]
        ))
    
    def registrar(self, definicion: DefinicionIndice):
        """Registra un nuevo índice"""
        clave = definicion.tipo.value
        self._indices[clave] = definicion
        logger.info(f"📊 Índice registrado: {definicion.nombre_completo} ({clave.upper()})")
    
    def obtener(self, tipo: str) -> Optional[DefinicionIndice]:
        """Obtiene definición de un índice"""
        return self._indices.get(tipo.lower())
    
    def listar_disponibles(self) -> List[str]:
        """Lista índices disponibles"""
        return list(self._indices.keys())
    
    def validar_compatibilidad(self, indices: List[str]) -> Dict[str, bool]:
        """
        Valida si múltiples índices pueden analizarse juntos
        
        Returns:
            Dict con compatibilidad de cada par
        """
        resultados = {}
        for i, idx1 in enumerate(indices):
            for idx2 in indices[i+1:]:
                def1 = self.obtener(idx1)
                def2 = self.obtener(idx2)
                
                if def1 and def2:
                    # Compatibles si comparten al menos una banda
                    bandas1 = set(def1.bandas_requeridas)
                    bandas2 = set(def2.bandas_requeridas)
                    compatible = len(bandas1 & bandas2) > 0
                    resultados[f"{idx1}_{idx2}"] = compatible
        
        return resultados


class ProcesadorMultiIndice:
    """
    Procesador unificado para múltiples índices vegetativos
    
    Procesa cualquier índice registrado bajo una arquitectura común,
    facilitando comparaciones y análisis cruzados.
    """
    
    def __init__(self):
        """Inicializa procesador"""
        self.registro = RegistroIndices()
    
    def procesar_indice(
        self,
        tipo_indice: str,
        valores: np.ndarray,
        periodos: List[str],
        metadatos: List[MetadatosImagen] = None
    ) -> Dict:
        """
        Procesa serie temporal de un índice
        
        Args:
            tipo_indice: Tipo de índice ('ndvi', 'ndmi', 'savi', etc.)
            valores: Array con valores del índice
            periodos: Lista de periodos correspondientes
            metadatos: Metadatos de imágenes (opcional)
            
        Returns:
            Diccionario con análisis completo del índice
        """
        # Obtener definición
        definicion = self.registro.obtener(tipo_indice)
        if not definicion:
            raise ValueError(f"Índice no reconocido: {tipo_indice}")
        
        logger.info(f"🔬 Procesando {definicion.nombre_completo}")
        
        # Validar y limpiar datos
        valores_validos, mask_validos = self._validar_valores(valores, definicion)
        
        if len(valores_validos) == 0:
            logger.warning(f"No hay valores válidos para {tipo_indice}")
            return self._resultado_vacio(definicion)
        
        # Calcular estadísticas
        estadisticas = self._calcular_estadisticas(valores_validos, definicion)
        
        # Analizar tendencia
        tendencia = self._analizar_tendencia(valores_validos)
        
        # Clasificar estado actual
        estado_actual = self._clasificar_estado(valores_validos[-1], definicion)
        
        # Detectar cambios significativos
        cambios = self._detectar_cambios(valores_validos, periodos, definicion)
        
        # Generar interpretación
        interpretacion = self._generar_interpretacion(
            estadisticas, tendencia, estado_actual, definicion
        )
        
        return {
            'indice': tipo_indice.upper(),
            'nombre_completo': definicion.nombre_completo,
            'estadisticas': estadisticas,
            'tendencia': tendencia,
            'estado_actual': estado_actual,
            'cambios_detectados': cambios,
            'interpretacion': interpretacion,
            'metadatos': {
                'total_puntos': len(valores),
                'puntos_validos': len(valores_validos),
                'puntos_descartados': len(valores) - len(valores_validos),
                'cobertura': len(valores_validos) / len(valores) if len(valores) > 0 else 0
            }
        }
    
    def _validar_valores(
        self,
        valores: np.ndarray,
        definicion: DefinicionIndice
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Valida y filtra valores según rangos del índice"""
        mask_validos = np.ones(len(valores), dtype=bool)
        
        for i, valor in enumerate(valores):
            es_valido, error = definicion.validar_valor(valor)
            if not es_valido:
                mask_validos[i] = False
                logger.debug(f"Valor descartado en pos {i}: {error}")
        
        valores_validos = valores[mask_validos]
        logger.info(
            f"✅ Validación: {len(valores_validos)}/{len(valores)} valores válidos "
            f"({len(valores_validos)/len(valores)*100:.1f}%)"
        )
        
        return valores_validos, mask_validos
    
    def _calcular_estadisticas(
        self,
        valores: np.ndarray,
        definicion: DefinicionIndice
    ) -> Dict:
        """Calcula estadísticas descriptivas"""
        return {
            'promedio': float(np.mean(valores)),
            'mediana': float(np.median(valores)),
            'desviacion_estandar': float(np.std(valores)),
            'minimo': float(np.min(valores)),
            'maximo': float(np.max(valores)),
            'percentil_25': float(np.percentile(valores, 25)),
            'percentil_75': float(np.percentile(valores, 75)),
            'coeficiente_variacion': float(np.std(valores) / np.mean(valores)) if np.mean(valores) != 0 else 0,
            'rango': float(np.max(valores) - np.min(valores))
        }
    
    def _analizar_tendencia(self, valores: np.ndarray) -> Dict:
        """Analiza tendencia temporal"""
        if len(valores) < 2:
            return {'tipo': 'insuficiente', 'pendiente': 0, 'r2': 0}
        
        x = np.arange(len(valores))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, valores)
        
        # Clasificar tendencia
        if abs(slope) < 0.01:
            tipo = 'estable'
        elif slope > 0:
            tipo = 'mejora' if slope > 0.02 else 'mejora_leve'
        else:
            tipo = 'deterioro' if slope < -0.02 else 'deterioro_leve'
        
        return {
            'tipo': tipo,
            'pendiente': float(slope),
            'r2': float(r_value ** 2),
            'p_value': float(p_value),
            'significativa': p_value < 0.05
        }
    
    def _clasificar_estado(self, valor: float, definicion: DefinicionIndice) -> Dict:
        """Clasifica estado actual del índice"""
        clasificacion = definicion.clasificar(valor)
        interpretacion = definicion.interpretar(valor)
        nivel_numerico = definicion.umbrales.nivel_numerico(valor)
        
        return {
            'valor': float(valor),
            'clasificacion': clasificacion,
            'nivel_numerico': nivel_numerico,
            'interpretacion': interpretacion
        }
    
    def _detectar_cambios(
        self,
        valores: np.ndarray,
        periodos: List[str],
        definicion: DefinicionIndice
    ) -> List[Dict]:
        """Detecta cambios significativos entre periodos"""
        cambios = []
        
        if len(valores) < 2:
            return cambios
        
        # Comparar periodos consecutivos
        for i in range(len(valores) - 1):
            diferencia = valores[i + 1] - valores[i]
            porcentaje_cambio = (diferencia / abs(valores[i])) * 100 if valores[i] != 0 else 0
            
            # Detectar cambios significativos (>10%)
            if abs(porcentaje_cambio) > 10:
                cambios.append({
                    'periodo_inicial': periodos[i] if i < len(periodos) else f"P{i}",
                    'periodo_final': periodos[i+1] if i+1 < len(periodos) else f"P{i+1}",
                    'valor_inicial': float(valores[i]),
                    'valor_final': float(valores[i+1]),
                    'diferencia': float(diferencia),
                    'porcentaje_cambio': float(porcentaje_cambio),
                    'tipo': 'mejora' if diferencia > 0 else 'deterioro',
                    'magnitud': 'fuerte' if abs(porcentaje_cambio) > 25 else 'moderado'
                })
        
        return cambios
    
    def _generar_interpretacion(
        self,
        estadisticas: Dict,
        tendencia: Dict,
        estado_actual: Dict,
        definicion: DefinicionIndice
    ) -> str:
        """Genera interpretación técnica del índice"""
        partes = []
        
        # Estado actual
        partes.append(
            f"El {definicion.tipo.value.upper()} actual ({estado_actual['valor']:.3f}) "
            f"indica {estado_actual['interpretacion'].lower()}."
        )
        
        # Tendencia
        if tendencia['tipo'] == 'mejora':
            partes.append(
                f"Se observa una tendencia de mejora (pendiente: {tendencia['pendiente']:.4f})."
            )
        elif tendencia['tipo'] == 'deterioro':
            partes.append(
                f"Se observa una tendencia de deterioro (pendiente: {tendencia['pendiente']:.4f})."
            )
        else:
            partes.append("La tendencia se mantiene relativamente estable.")
        
        # Variabilidad
        cv = estadisticas['coeficiente_variacion']
        if cv < 0.1:
            partes.append("La variabilidad es baja, indicando condiciones consistentes.")
        elif cv > 0.3:
            partes.append("La variabilidad es alta, sugiriendo condiciones cambiantes.")
        
        return " ".join(partes)
    
    def _resultado_vacio(self, definicion: DefinicionIndice) -> Dict:
        """Retorna resultado vacío cuando no hay datos"""
        return {
            'indice': definicion.tipo.value.upper(),
            'nombre_completo': definicion.nombre_completo,
            'estadisticas': None,
            'tendencia': None,
            'estado_actual': None,
            'cambios_detectados': [],
            'interpretacion': "No hay datos suficientes para análisis",
            'metadatos': {
                'total_puntos': 0,
                'puntos_validos': 0,
                'puntos_descartados': 0,
                'cobertura': 0.0
            }
        }


# Instancia global del registro
registro_indices = RegistroIndices()
