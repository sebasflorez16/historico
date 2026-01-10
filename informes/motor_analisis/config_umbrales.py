"""
Configuración de Umbrales Agronómicos
====================================

Umbrales científicamente validados para clasificación de índices vegetativos.
Basados en literatura científica y mejores prácticas agrícolas.

Referencias:
- Rouse et al. (1974) - NDVI original
- Huete (1988) - SAVI
- Gao (1996) - NDWI/NDMI
- Tucker (1979) - Aplicaciones NDVI

Notas:
- Todos los umbrales son configurables
- Los valores son conservadores para minimizar falsos positivos
- Se ajustan automáticamente por tipo de cultivo cuando está disponible
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class UmbralesIndice:
    """Umbrales para un índice específico"""
    muy_bajo: float
    bajo: float
    medio: float
    alto: float
    muy_alto: float
    
    def clasificar(self, valor: float) -> str:
        """Clasifica un valor según los umbrales"""
        if valor < self.muy_bajo:
            return 'muy_bajo'
        elif valor < self.bajo:
            return 'bajo'
        elif valor < self.medio:
            return 'medio'
        elif valor < self.alto:
            return 'alto'
        else:
            return 'muy_alto'
    
    def nivel_numerico(self, valor: float) -> int:
        """Retorna nivel numérico 1-5"""
        clasificacion = self.clasificar(valor)
        niveles = {
            'muy_bajo': 1,
            'bajo': 2,
            'medio': 3,
            'alto': 4,
            'muy_alto': 5
        }
        return niveles[clasificacion]


# ===========================
# UMBRALES NDVI
# ===========================
# Basados en Rouse et al. (1974) y literatura posterior

UMBRALES_NDVI_GENERAL = UmbralesIndice(
    muy_bajo=0.2,   # Suelo desnudo, agua, áreas sin vegetación
    bajo=0.4,       # Vegetación escasa o estresada
    medio=0.6,      # Vegetación moderada
    alto=0.75,      # Vegetación saludable
    muy_alto=0.85   # Vegetación muy densa y saludable
)

# Umbrales específicos por tipo de cultivo
UMBRALES_NDVI_POR_CULTIVO = {
    'maíz': UmbralesIndice(
        muy_bajo=0.25,
        bajo=0.45,
        medio=0.65,
        alto=0.80,
        muy_alto=0.90
    ),
    'trigo': UmbralesIndice(
        muy_bajo=0.20,
        bajo=0.40,
        medio=0.60,
        alto=0.75,
        muy_alto=0.85
    ),
    'soja': UmbralesIndice(
        muy_bajo=0.25,
        bajo=0.45,
        medio=0.65,
        alto=0.78,
        muy_alto=0.88
    ),
    'arroz': UmbralesIndice(
        muy_bajo=0.30,
        bajo=0.50,
        medio=0.70,
        alto=0.82,
        muy_alto=0.92
    ),
}


# ===========================
# UMBRALES NDMI (Humedad)
# ===========================
# Basados en Gao (1996)

UMBRALES_NDMI = UmbralesIndice(
    muy_bajo=-0.2,  # Estrés hídrico severo
    bajo=0.1,       # Estrés hídrico moderado
    medio=0.3,      # Humedad adecuada
    alto=0.5,       # Buena humedad
    muy_alto=0.7    # Saturación
)


# ===========================
# UMBRALES SAVI
# ===========================
# Basados en Huete (1988)

UMBRALES_SAVI = UmbralesIndice(
    muy_bajo=0.15,
    bajo=0.35,
    medio=0.55,
    alto=0.70,
    muy_alto=0.85
)


# ===========================
# ZONIFICACIÓN PRODUCTIVA
# ===========================

class ZonaProductividad:
    """Configuración para zonificación productiva"""
    
    # Porcentajes de área para clasificación de zonas
    PERCENTIL_BAJA = 33      # Percentil 33: zona baja productividad
    PERCENTIL_MEDIA = 66     # Percentil 66: zona media productividad
    # Resto: zona alta productividad
    
    # Umbrales de variabilidad (desviación estándar)
    VARIABILIDAD_BAJA = 0.05      # Coef. variación < 5%
    VARIABILIDAD_MEDIA = 0.15     # Coef. variación < 15%
    VARIABILIDAD_ALTA = 0.25      # Coef. variación < 25%
    # > 25%: variabilidad muy alta


# ===========================
# DETECCIÓN DE ANOMALÍAS
# ===========================

class ConfigAnomalias:
    """Configuración para detección de anomalías"""
    
    # Desviaciones estándar para considerar outlier
    UMBRAL_OUTLIER_SIGMA = 2.5
    
    # Caída mínima para alerta de deterioro (%)
    CAIDA_CRITICA_NDVI = -15.0
    CAIDA_MODERADA_NDVI = -10.0
    
    # Cambio mínimo para considerar tendencia significativa
    CAMBIO_MINIMO_TENDENCIA = 5.0  # %
    
    # R² mínimo para considerar tendencia confiable
    R2_MINIMO_CONFIABLE = 0.5
    R2_ALTO = 0.7


# ===========================
# RECOMENDACIONES AGRONÓMICAS
# ===========================

class ReglasRecomendaciones:
    """Reglas para generación de recomendaciones"""
    
    # Prioridades según severidad
    PRIORIDAD_ALTA_SI = {
        'ndvi_promedio': lambda v: v < 0.4,
        'ndmi_promedio': lambda v: v < 0.0,
        'caida_ndvi': lambda v: v < -15.0,
        'area_baja_productividad': lambda v: v > 30.0,  # % del área total
    }
    
    PRIORIDAD_MEDIA_SI = {
        'ndvi_promedio': lambda v: 0.4 <= v < 0.6,
        'ndmi_promedio': lambda v: 0.0 <= v < 0.2,
        'caida_ndvi': lambda v: -15.0 <= v < -10.0,
        'area_baja_productividad': lambda v: 15.0 < v <= 30.0,
    }
    
    # Plantillas de recomendaciones
    RECOMENDACIONES_NDVI_BAJO = [
        "Inspeccionar áreas de baja productividad identificadas en el mapa de zonificación",
        "Evaluar estado nutricional del cultivo mediante análisis foliar",
        "Verificar presencia de plagas, enfermedades o estrés abiótico",
        "Considerar fertilización nitrogenada en zonas deficientes",
    ]
    
    RECOMENDACIONES_NDMI_BAJO = [
        "Evaluar sistema de riego y su uniformidad espacial",
        "Inspeccionar zonas con bajo contenido hídrico en el mapa",
        "Considerar riego suplementario según disponibilidad",
        "Verificar funcionamiento de sistemas de drenaje",
    ]
    
    RECOMENDACIONES_VARIABILIDAD_ALTA = [
        "Implementar manejo sitio-específico (agricultura de precisión)",
        "Analizar causas de heterogeneidad (suelo, topografía, manejo)",
        "Considerar aplicación variable de insumos",
        "Zonificar lote para manejo diferenciado",
    ]


# ===========================
# FUNCIONES DE UTILIDAD
# ===========================

def obtener_umbrales_ndvi(tipo_cultivo: str = None) -> UmbralesIndice:
    """
    Obtiene umbrales NDVI apropiados para el tipo de cultivo
    
    Args:
        tipo_cultivo: Tipo de cultivo (opcional)
        
    Returns:
        UmbralesIndice configurados
    """
    if tipo_cultivo:
        cultivo_lower = tipo_cultivo.lower()
        return UMBRALES_NDVI_POR_CULTIVO.get(cultivo_lower, UMBRALES_NDVI_GENERAL)
    return UMBRALES_NDVI_GENERAL


def calcular_puntuacion(valor: float, umbrales: UmbralesIndice, escala: int = 10) -> float:
    """
    Calcula puntuación normalizada (0-escala) para un valor dado
    
    Args:
        valor: Valor del índice
        umbrales: Umbrales de clasificación
        escala: Escala máxima (default: 10)
        
    Returns:
        Puntuación normalizada
    """
    nivel = umbrales.nivel_numerico(valor)
    return (nivel / 5.0) * escala


def interpretar_tendencia(pendiente: float, r2: float) -> Dict[str, str]:
    """
    Interpreta tendencia temporal
    
    Args:
        pendiente: Pendiente de regresión lineal
        r2: Coeficiente de determinación
        
    Returns:
        Diccionario con interpretación
    """
    # Dirección
    if abs(pendiente) < 0.001:
        direccion = 'estable'
    elif pendiente > 0:
        direccion = 'ascendente'
    else:
        direccion = 'descendente'
    
    # Fuerza
    if r2 >= ConfigAnomalias.R2_ALTO:
        confianza = 'alta'
    elif r2 >= ConfigAnomalias.R2_MINIMO_CONFIABLE:
        confianza = 'media'
    else:
        confianza = 'baja'
    
    return {
        'direccion': direccion,
        'confianza': confianza,
        'r_cuadrado': r2
    }
