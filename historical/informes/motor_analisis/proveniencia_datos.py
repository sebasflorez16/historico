"""
Sistema de Proveniencia y Trazabilidad de Datos
==============================================

Registra explícitamente el origen, calidad y procesamiento de todos los datos
utilizados en el análisis agrícola, garantizando auditabilidad completa.

Características:
- Registro de fuentes de datos (caché, descarga, manual)
- Seguimiento de calidad de imágenes satelitales
- Criterios de selección de escenas
- Metadatos de procesamiento
- Historial de transformaciones

Referencias:
- ISO 19115: Geographic information - Metadata
- FAIR Data Principles (Findable, Accessible, Interoperable, Reusable)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class FuenteDatos(Enum):
    """Origen de los datos satelitales"""
    CACHE_LOCAL = "cache_local"
    DESCARGA_EOSDA = "descarga_eosda"
    ENTRADA_MANUAL = "entrada_manual"
    CALCULO_DERIVADO = "calculo_derivado"


class CalidadImagen(Enum):
    """Niveles de calidad de imagen satelital"""
    EXCELENTE = "excelente"  # <5% nubosidad, resolución óptima
    BUENA = "buena"          # 5-15% nubosidad
    ACEPTABLE = "aceptable"  # 15-30% nubosidad
    DEGRADADA = "degradada"  # >30% nubosidad o baja resolución
    RECHAZADA = "rechazada"  # No apta para análisis


@dataclass
class MetadatosImagen:
    """
    Metadatos completos de una imagen satelital
    
    Documenta todos los aspectos técnicos relevantes para auditoría
    """
    # Identificación
    id_imagen: str
    fecha_adquisicion: date
    periodo: str  # e.g., "2024-01"
    
    # Fuente y calidad
    fuente: FuenteDatos
    calidad: CalidadImagen
    nubosidad_porcentaje: float
    resolucion_metros: float
    
    # Satélite
    satelite: str  # e.g., "Sentinel-2", "Landsat-8"
    sensor: str
    orbita: Optional[str] = None
    
    # Georreferenciación
    bbox: Tuple[float, float, float, float] = None  # (min_lat, min_lon, max_lat, max_lon)
    centroide: Tuple[float, float] = None  # (lat, lon)
    srid: int = 4326  # WGS84 por defecto
    
    # Procesamiento
    nivel_procesamiento: str = "L2A"  # L1C, L2A, etc.
    correcciones_aplicadas: List[str] = field(default_factory=list)
    
    # Trazabilidad
    fecha_descarga: Optional[datetime] = None
    hash_archivo: Optional[str] = None
    url_fuente: Optional[str] = None
    
    # Criterios de selección
    razon_seleccion: str = "mejor_calidad"  # mejor_calidad, mas_reciente, unica_disponible
    descartadas: int = 0  # Número de imágenes alternativas descartadas
    
    def nivel_confianza(self) -> float:
        """
        Calcula nivel de confianza (0-1) basado en calidad
        
        Returns:
            Float entre 0 y 1 representando confianza en los datos
        """
        if self.calidad == CalidadImagen.EXCELENTE:
            return 0.95
        elif self.calidad == CalidadImagen.BUENA:
            return 0.85
        elif self.calidad == CalidadImagen.ACEPTABLE:
            return 0.70
        elif self.calidad == CalidadImagen.DEGRADADA:
            return 0.50
        else:
            return 0.0
    
    def es_apta_analisis(self) -> bool:
        """Verifica si la imagen es apta para análisis técnico"""
        return self.calidad != CalidadImagen.RECHAZADA and self.nubosidad_porcentaje < 40
    
    def to_dict(self) -> Dict:
        """Serializa a diccionario para logging"""
        return {
            'id_imagen': self.id_imagen,
            'fecha_adquisicion': str(self.fecha_adquisicion),
            'periodo': self.periodo,
            'fuente': self.fuente.value,
            'calidad': self.calidad.value,
            'nubosidad': f"{self.nubosidad_porcentaje:.1f}%",
            'resolucion': f"{self.resolucion_metros}m",
            'satelite': self.satelite,
            'nivel_confianza': f"{self.nivel_confianza():.2f}",
            'razon_seleccion': self.razon_seleccion,
            'descartadas': self.descartadas
        }


@dataclass
class RegistroIndice:
    """
    Registro de un índice vegetativo calculado
    
    Documenta el cálculo completo de un índice (NDVI, NDMI, SAVI, etc.)
    """
    # Identificación
    tipo_indice: str  # 'NDVI', 'NDMI', 'SAVI', etc.
    periodo: str
    fecha_calculo: datetime
    
    # Valor y estadísticas
    valor_promedio: float
    valor_mediana: float
    desviacion_estandar: float
    min_valor: float
    max_valor: float
    
    # Proveniencia
    metadatos_imagen: MetadatosImagen
    
    # Procesamiento
    bandas_utilizadas: List[str] = field(default_factory=list)
    algoritmo: str = "estándar"
    parametros: Dict = field(default_factory=dict)
    
    # Validación
    pixels_validos: int = 0
    pixels_totales: int = 0
    pixels_nubosos: int = 0
    pixels_fuera_rango: int = 0
    
    def porcentaje_cobertura(self) -> float:
        """Porcentaje de pixels válidos"""
        if self.pixels_totales == 0:
            return 0.0
        return (self.pixels_validos / self.pixels_totales) * 100
    
    def nivel_confianza(self) -> float:
        """
        Nivel de confianza del índice (0-1)
        
        Combina calidad de imagen y cobertura válida
        """
        confianza_imagen = self.metadatos_imagen.nivel_confianza()
        cobertura = self.porcentaje_cobertura() / 100.0
        
        # Promedio ponderado (imagen 70%, cobertura 30%)
        return (confianza_imagen * 0.7) + (cobertura * 0.3)
    
    def to_dict(self) -> Dict:
        """Serializa a diccionario"""
        return {
            'indice': self.tipo_indice,
            'periodo': self.periodo,
            'valor_promedio': round(self.valor_promedio, 4),
            'nivel_confianza': round(self.nivel_confianza(), 2),
            'cobertura': f"{self.porcentaje_cobertura():.1f}%",
            'imagen': self.metadatos_imagen.to_dict()
        }


class RegistradorProveniencia:
    """
    Gestor central de trazabilidad de datos
    
    Mantiene un registro auditable de todas las fuentes de datos,
    transformaciones y criterios de selección utilizados en el análisis.
    """
    
    def __init__(self):
        """Inicializa registrador"""
        self.imagenes: List[MetadatosImagen] = []
        self.indices: List[RegistroIndice] = []
        self.transformaciones: List[Dict] = []
        self.advertencias: List[str] = []
    
    def registrar_imagen(self, metadatos: MetadatosImagen) -> None:
        """
        Registra una imagen satelital utilizada
        
        Args:
            metadatos: Metadatos completos de la imagen
        """
        self.imagenes.append(metadatos)
        
        # Validar y generar advertencias
        if not metadatos.es_apta_analisis():
            self.advertencias.append(
                f"⚠️ Imagen {metadatos.id_imagen} de calidad {metadatos.calidad.value} "
                f"(nubosidad: {metadatos.nubosidad_porcentaje:.1f}%)"
            )
        
        logger.info(
            f"📸 Imagen registrada: {metadatos.periodo} | "
            f"Calidad: {metadatos.calidad.value} | "
            f"Confianza: {metadatos.nivel_confianza():.2f}"
        )
    
    def registrar_indice(self, registro: RegistroIndice) -> None:
        """
        Registra cálculo de un índice vegetativo
        
        Args:
            registro: Registro completo del índice
        """
        self.indices.append(registro)
        
        # Advertencias de cobertura
        if registro.porcentaje_cobertura() < 70:
            self.advertencias.append(
                f"⚠️ {registro.tipo_indice} {registro.periodo}: "
                f"Cobertura baja ({registro.porcentaje_cobertura():.1f}%)"
            )
        
        logger.info(
            f"📊 Índice calculado: {registro.tipo_indice} {registro.periodo} | "
            f"Valor: {registro.valor_promedio:.3f} | "
            f"Confianza: {registro.nivel_confianza():.2f}"
        )
    
    def registrar_transformacion(
        self,
        operacion: str,
        descripcion: str,
        parametros: Dict = None
    ) -> None:
        """
        Registra una transformación aplicada a los datos
        
        Args:
            operacion: Nombre de la operación
            descripcion: Descripción detallada
            parametros: Parámetros utilizados
        """
        transformacion = {
            'timestamp': datetime.now(),
            'operacion': operacion,
            'descripcion': descripcion,
            'parametros': parametros or {}
        }
        self.transformaciones.append(transformacion)
        logger.debug(f"🔄 Transformación: {operacion}")
    
    def estadisticas_calidad(self) -> Dict:
        """
        Calcula estadísticas de calidad del conjunto de datos
        
        Returns:
            Diccionario con métricas de calidad
        """
        if not self.imagenes:
            return {
                'total_imagenes': 0,
                'confianza_promedio': 0.0,
                'advertencias': self.advertencias
            }
        
        # Distribución por calidad
        calidades = {}
        for img in self.imagenes:
            calidad = img.calidad.value
            calidades[calidad] = calidades.get(calidad, 0) + 1
        
        # Distribución por fuente
        fuentes = {}
        for img in self.imagenes:
            fuente = img.fuente.value
            fuentes[fuente] = fuentes.get(fuente, 0) + 1
        
        # Confianza promedio
        confianzas = [img.nivel_confianza() for img in self.imagenes]
        confianza_promedio = sum(confianzas) / len(confianzas) if confianzas else 0.0
        
        # Nubosidad promedio
        nubosidad_promedio = sum(img.nubosidad_porcentaje for img in self.imagenes) / len(self.imagenes)
        
        return {
            'total_imagenes': len(self.imagenes),
            'total_indices': len(self.indices),
            'distribucion_calidad': calidades,
            'distribucion_fuente': fuentes,
            'confianza_promedio': confianza_promedio,
            'nubosidad_promedio': nubosidad_promedio,
            'advertencias': self.advertencias,
            'imagenes_rechazadas': sum(1 for img in self.imagenes if not img.es_apta_analisis())
        }
    
    def generar_resumen_proveniencia(self) -> str:
        """
        Genera resumen legible de la proveniencia de datos
        
        Returns:
            String con resumen técnico
        """
        stats = self.estadisticas_calidad()
        
        resumen = [
            "=" * 60,
            "RESUMEN DE PROVENIENCIA DE DATOS",
            "=" * 60,
            f"Total de imágenes procesadas: {stats['total_imagenes']}",
            f"Total de índices calculados: {stats['total_indices']}",
            f"Confianza promedio: {stats['confianza_promedio']:.2%}",
            f"Nubosidad promedio: {stats['nubosidad_promedio']:.1f}%",
            "",
            "Distribución por calidad:",
        ]
        
        for calidad, count in stats['distribucion_calidad'].items():
            resumen.append(f"  - {calidad}: {count} imágenes")
        
        resumen.append("")
        resumen.append("Distribución por fuente:")
        for fuente, count in stats['distribucion_fuente'].items():
            resumen.append(f"  - {fuente}: {count} imágenes")
        
        if stats['advertencias']:
            resumen.append("")
            resumen.append(f"⚠️  {len(stats['advertencias'])} advertencias detectadas")
        
        resumen.append("=" * 60)
        
        return "\n".join(resumen)
    
    def exportar_auditoria(self) -> Dict:
        """
        Exporta información completa de auditoría
        
        Returns:
            Diccionario con todos los detalles de trazabilidad
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'estadisticas': self.estadisticas_calidad(),
            'imagenes': [img.to_dict() for img in self.imagenes],
            'indices': [idx.to_dict() for idx in self.indices],
            'transformaciones': self.transformaciones,
            'advertencias': self.advertencias
        }
