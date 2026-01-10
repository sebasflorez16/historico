"""
Reporte Técnico de Análisis Agrícola
====================================

Objeto formal que documenta completamente un análisis agrícola,
incluyendo datos utilizados, metodologías aplicadas, limitaciones
y nivel de confianza.

Este reporte garantiza auditabilidad y defensibilidad técnica completa.

Características:
- Documentación exhaustiva de metodologías
- Registro de bibliotecas y algoritmos utilizados
- Reglas agronómicas aplicadas con referencias
- Limitaciones explícitas del análisis
- Nivel de confianza calculado automáticamente
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NivelConfianza(Enum):
    """Niveles de confianza del análisis"""
    MUY_ALTA = "muy_alta"      # >90% - Datos excelentes, análisis robusto
    ALTA = "alta"              # 75-90% - Datos buenos, análisis confiable
    MEDIA = "media"            # 60-75% - Datos aceptables, conclusiones moderadas
    BAJA = "baja"              # 40-60% - Datos limitados, conclusiones cautelosas
    MUY_BAJA = "muy_baja"      # <40% - Datos insuficientes, conclusiones indicativas


@dataclass
class BibliotecaTecnica:
    """Documenta una biblioteca técnica utilizada"""
    nombre: str
    version: str
    proposito: str
    metodos_utilizados: List[str]
    
    def __str__(self):
        return f"{self.nombre} {self.version} ({self.proposito})"


@dataclass
class ReglaAgronomica:
    """Documenta una regla agronómica aplicada"""
    nombre: str
    descripcion: str
    umbral_aplicado: any
    referencia_cientifica: Optional[str] = None
    aplicada_en: Optional[str] = None
    
    def __str__(self):
        ref = f" [{self.referencia_cientifica}]" if self.referencia_cientifica else ""
        return f"{self.nombre}: {self.descripcion}{ref}"


@dataclass
class Limitacion:
    """Documenta una limitación del análisis"""
    tipo: str  # 'datos', 'metodologia', 'temporal', 'espacial'
    descripcion: str
    impacto: str  # 'bajo', 'medio', 'alto'
    mitigacion: Optional[str] = None
    
    def __str__(self):
        impacto_emoji = {'bajo': '⚪', 'medio': '🟡', 'alto': '🔴'}
        emoji = impacto_emoji.get(self.impacto, '⚪')
        mitg = f" Mitigación: {self.mitigacion}" if self.mitigacion else ""
        return f"{emoji} [{self.tipo.upper()}] {self.descripcion}.{mitg}"


@dataclass
class ReporteTecnico:
    """
    Reporte Técnico de Análisis Agrícola
    
    Documenta de forma exhaustiva un análisis completo, garantizando
    auditabilidad, reproducibilidad y defensibilidad técnica.
    """
    
    # =============================
    # 1. IDENTIFICACIÓN
    # =============================
    id_reporte: str
    fecha_generacion: datetime
    periodo_analisis_inicio: date
    periodo_analisis_fin: date
    
    # =============================
    # 2. DATOS UTILIZADOS
    # =============================
    total_imagenes: int = 0
    imagenes_aceptadas: int = 0
    imagenes_rechazadas: int = 0
    criterio_seleccion: str = "calidad_y_cobertura"
    
    indices_analizados: List[str] = field(default_factory=list)
    puntos_temporales: int = 0
    cobertura_temporal_porcentaje: float = 0.0
    
    # Calidad de datos
    nubosidad_promedio: float = 0.0
    resolucion_promedio: float = 10.0
    satelites_utilizados: List[str] = field(default_factory=list)
    
    # =============================
    # 3. METODOLOGÍAS APLICADAS
    # =============================
    bibliotecas_tecnicas: List[BibliotecaTecnica] = field(default_factory=list)
    reglas_agronomicas: List[ReglaAgronomica] = field(default_factory=list)
    algoritmos_aplicados: List[str] = field(default_factory=list)
    
    # =============================
    # 4. RESULTADOS PRINCIPALES
    # =============================
    conclusiones_principales: List[str] = field(default_factory=list)
    tendencias_identificadas: List[str] = field(default_factory=list)
    anomalias_detectadas: List[str] = field(default_factory=list)
    recomendaciones: List[Dict] = field(default_factory=list)
    
    # =============================
    # 5. LIMITACIONES
    # =============================
    limitaciones: List[Limitacion] = field(default_factory=list)
    
    # =============================
    # 6. CONFIANZA Y VALIDACIÓN
    # =============================
    nivel_confianza: NivelConfianza = NivelConfianza.MEDIA
    puntuacion_confianza: float = 0.7
    factores_confianza: Dict[str, float] = field(default_factory=dict)
    
    # =============================
    # 7. METADATOS
    # =============================
    tipo_cultivo: Optional[str] = None
    area_hectareas: Optional[float] = None
    ubicacion_geografica: Optional[str] = None
    analista: str = "Motor de Análisis Automatizado v2.0"
    
    def __post_init__(self):
        """Inicialización automática"""
        if not self.id_reporte:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.id_reporte = f"RT-{timestamp}"
        
        # Registrar bibliotecas estándar
        self._registrar_bibliotecas_standard()
    
    def _registrar_bibliotecas_standard(self):
        """Registra bibliotecas técnicas utilizadas por defecto"""
        bibliotecas_default = [
            BibliotecaTecnica(
                nombre="NumPy",
                version="1.24+",
                proposito="Cálculos numéricos y estadísticos",
                metodos_utilizados=["mean", "std", "percentile", "polyfit", "corrcoef"]
            ),
            BibliotecaTecnica(
                nombre="SciPy",
                version="1.11+",
                proposito="Análisis estadístico avanzado",
                metodos_utilizados=["stats.linregress", "stats.zscore", "signal.find_peaks"]
            ),
            BibliotecaTecnica(
                nombre="scikit-learn",
                version="1.3+",
                proposito="Aprendizaje automático y clustering",
                metodos_utilizados=["KMeans", "StandardScaler", "LinearRegression"]
            )
        ]
        
        # Solo agregar si no están ya
        nombres_existentes = {bib.nombre for bib in self.bibliotecas_tecnicas}
        for bib in bibliotecas_default:
            if bib.nombre not in nombres_existentes:
                self.bibliotecas_tecnicas.append(bib)
    
    def agregar_biblioteca(
        self,
        nombre: str,
        version: str,
        proposito: str,
        metodos: List[str]
    ):
        """Agrega una biblioteca técnica utilizada"""
        bib = BibliotecaTecnica(nombre, version, proposito, metodos)
        self.bibliotecas_tecnicas.append(bib)
        logger.debug(f"📚 Biblioteca registrada: {bib}")
    
    def agregar_regla(
        self,
        nombre: str,
        descripcion: str,
        umbral: any,
        referencia: str = None
    ):
        """Agrega una regla agronómica aplicada"""
        regla = ReglaAgronomica(nombre, descripcion, umbral, referencia)
        self.reglas_agronomicas.append(regla)
        logger.debug(f"📏 Regla aplicada: {regla.nombre}")
    
    def agregar_limitacion(
        self,
        tipo: str,
        descripcion: str,
        impacto: str,
        mitigacion: str = None
    ):
        """Agrega una limitación del análisis"""
        limitacion = Limitacion(tipo, descripcion, impacto, mitigacion)
        self.limitaciones.append(limitacion)
        
        # Ajustar confianza según impacto
        if impacto == 'alto':
            self.puntuacion_confianza *= 0.9
        elif impacto == 'medio':
            self.puntuacion_confianza *= 0.95
        
        logger.warning(f"⚠️ Limitación detectada: {limitacion}")
    
    def calcular_confianza(
        self,
        confianza_datos: float,
        completitud_temporal: float,
        variabilidad_datos: float
    ):
        """
        Calcula nivel de confianza del análisis
        
        Args:
            confianza_datos: Confianza promedio de imágenes (0-1)
            completitud_temporal: Porcentaje de cobertura temporal (0-1)
            variabilidad_datos: Variabilidad de datos (0=uniforme, 1=caótico)
        """
        # Factores de confianza
        self.factores_confianza = {
            'calidad_datos': confianza_datos,
            'completitud_temporal': completitud_temporal,
            'consistencia_datos': 1.0 - variabilidad_datos,
            'numero_puntos': min(self.puntos_temporales / 12.0, 1.0),  # 12 meses = ideal
            'cobertura_indices': len(self.indices_analizados) / 3.0  # 3 índices = completo
        }
        
        # Promedio ponderado
        pesos = {
            'calidad_datos': 0.35,
            'completitud_temporal': 0.25,
            'consistencia_datos': 0.20,
            'numero_puntos': 0.15,
            'cobertura_indices': 0.05
        }
        
        self.puntuacion_confianza = sum(
            self.factores_confianza[k] * pesos[k]
            for k in pesos.keys()
        )
        
        # Aplicar penalizaciones por limitaciones
        limitaciones_altas = sum(1 for lim in self.limitaciones if lim.impacto == 'alto')
        limitaciones_medias = sum(1 for lim in self.limitaciones if lim.impacto == 'medio')
        
        penalizacion = (limitaciones_altas * 0.1) + (limitaciones_medias * 0.05)
        self.puntuacion_confianza = max(0.0, self.puntuacion_confianza - penalizacion)
        
        # Clasificar nivel
        if self.puntuacion_confianza >= 0.90:
            self.nivel_confianza = NivelConfianza.MUY_ALTA
        elif self.puntuacion_confianza >= 0.75:
            self.nivel_confianza = NivelConfianza.ALTA
        elif self.puntuacion_confianza >= 0.60:
            self.nivel_confianza = NivelConfianza.MEDIA
        elif self.puntuacion_confianza >= 0.40:
            self.nivel_confianza = NivelConfianza.BAJA
        else:
            self.nivel_confianza = NivelConfianza.MUY_BAJA
        
        logger.info(
            f"🎯 Confianza calculada: {self.nivel_confianza.value} "
            f"({self.puntuacion_confianza:.2%})"
        )
    
    def ponderar_recomendacion(
        self,
        recomendacion: str,
        prioridad_base: str,
        confianza_requerida: float = 0.6
    ) -> Dict:
        """
        Pondera una recomendación según confianza del análisis
        
        Args:
            recomendacion: Texto de la recomendación
            prioridad_base: Prioridad sin ponderar ('alta', 'media', 'baja')
            confianza_requerida: Confianza mínima para mantener prioridad
            
        Returns:
            Diccionario con recomendación ponderada
        """
        # Si confianza es baja, degradar prioridad
        if self.puntuacion_confianza < confianza_requerida:
            # Degradar prioridad
            degradacion = {
                'alta': 'media',
                'media': 'baja',
                'baja': 'baja'
            }
            prioridad_ajustada = degradacion.get(prioridad_base, 'baja')
            
            # Agregar disclaimers
            prefijo = "⚠️ [Confianza limitada] "
            sufijo = f" (Confianza: {self.puntuacion_confianza:.0%})"
            recomendacion_ajustada = prefijo + recomendacion + sufijo
        else:
            prioridad_ajustada = prioridad_base
            recomendacion_ajustada = recomendacion
        
        return {
            'texto': recomendacion_ajustada,
            'prioridad': prioridad_ajustada,
            'confianza': self.puntuacion_confianza,
            'degradada': prioridad_ajustada != prioridad_base
        }
    
    def generar_resumen_ejecutivo(self) -> str:
        """
        Genera resumen ejecutivo del reporte técnico
        
        Returns:
            String con resumen técnico legible
        """
        lineas = [
            "=" * 70,
            "REPORTE TÉCNICO DE ANÁLISIS AGRÍCOLA",
            "=" * 70,
            f"ID Reporte: {self.id_reporte}",
            f"Fecha: {self.fecha_generacion.strftime('%Y-%m-%d %H:%M')}",
            f"Periodo: {self.periodo_analisis_inicio} a {self.periodo_analisis_fin}",
            "",
            "─" * 70,
            "1. DATOS UTILIZADOS",
            "─" * 70,
            f"Imágenes procesadas: {self.total_imagenes} "
            f"({self.imagenes_aceptadas} aceptadas, {self.imagenes_rechazadas} rechazadas)",
            f"Índices analizados: {', '.join(self.indices_analizados)}",
            f"Puntos temporales: {self.puntos_temporales}",
            f"Cobertura temporal: {self.cobertura_temporal_porcentaje:.1f}%",
            f"Nubosidad promedio: {self.nubosidad_promedio:.1f}%",
            f"Satélites: {', '.join(self.satelites_utilizados)}",
            "",
            "─" * 70,
            "2. METODOLOGÍA",
            "─" * 70,
            "Bibliotecas técnicas:",
        ]
        
        for bib in self.bibliotecas_tecnicas:
            lineas.append(f"  • {bib}")
        
        lineas.extend([
            "",
            "Reglas agronómicas aplicadas:",
        ])
        
        for i, regla in enumerate(self.reglas_agronomicas[:5], 1):  # Primeras 5
            lineas.append(f"  {i}. {regla}")
        
        if len(self.reglas_agronomicas) > 5:
            lineas.append(f"  ... y {len(self.reglas_agronomicas) - 5} reglas más")
        
        lineas.extend([
            "",
            "─" * 70,
            "3. NIVEL DE CONFIANZA",
            "─" * 70,
            f"Nivel: {self.nivel_confianza.value.upper()} ({self.puntuacion_confianza:.1%})",
            "",
            "Factores de confianza:",
        ])
        
        for factor, valor in self.factores_confianza.items():
            emoji = "✅" if valor > 0.7 else "⚠️" if valor > 0.5 else "❌"
            lineas.append(f"  {emoji} {factor.replace('_', ' ').title()}: {valor:.1%}")
        
        if self.limitaciones:
            lineas.extend([
                "",
                "─" * 70,
                "4. LIMITACIONES DEL ANÁLISIS",
                "─" * 70,
            ])
            for lim in self.limitaciones:
                lineas.append(f"  {lim}")
        
        lineas.extend([
            "",
            "─" * 70,
            "5. CONCLUSIONES PRINCIPALES",
            "─" * 70,
        ])
        
        for i, conclusion in enumerate(self.conclusiones_principales, 1):
            lineas.append(f"  {i}. {conclusion}")
        
        if not self.conclusiones_principales:
            lineas.append("  (Sin conclusiones registradas)")
        
        lineas.extend([
            "",
            "=" * 70,
            f"Analista: {self.analista}",
            "=" * 70,
        ])
        
        return "\n".join(lineas)
    
    def exportar_para_pdf(self) -> Dict:
        """
        Exporta datos formateados para inclusión en PDF
        
        Returns:
            Diccionario con secciones listas para PDF
        """
        return {
            'id_reporte': self.id_reporte,
            'fecha': self.fecha_generacion.strftime('%Y-%m-%d %H:%M'),
            'periodo': {
                'inicio': str(self.periodo_analisis_inicio),
                'fin': str(self.periodo_analisis_fin)
            },
            'datos': {
                'imagenes_totales': self.total_imagenes,
                'imagenes_aceptadas': self.imagenes_aceptadas,
                'nubosidad_promedio': f"{self.nubosidad_promedio:.1f}%",
                'satelites': self.satelites_utilizados,
                'indices': self.indices_analizados,
                'puntos_temporales': self.puntos_temporales
            },
            'metodologia': {
                'bibliotecas': [str(bib) for bib in self.bibliotecas_tecnicas],
                'reglas': [str(regla) for regla in self.reglas_agronomicas]
            },
            'confianza': {
                'nivel': self.nivel_confianza.value,
                'puntuacion': self.puntuacion_confianza,
                'factores': self.factores_confianza
            },
            'limitaciones': [str(lim) for lim in self.limitaciones],
            'conclusiones': self.conclusiones_principales,
            'recomendaciones': self.recomendaciones
        }
