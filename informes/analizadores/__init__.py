"""
Analizadores Inteligentes de Datos Satelitales
Sistema de interpretación automática sin IA externa
"""

from .ndvi_analyzer import AnalizadorNDVI
from .ndmi_analyzer import AnalizadorNDMI
from .savi_analyzer import AnalizadorSAVI
from .ndre_analyzer import AnalizadorNDRE
from .evi_analyzer import AnalizadorEVI
from .tendencias_analyzer import DetectorTendencias
from .recomendaciones_engine import GeneradorRecomendaciones

__all__ = [
    'AnalizadorNDVI',
    'AnalizadorNDMI', 
    'AnalizadorSAVI',
    'AnalizadorNDRE',
    'AnalizadorEVI',
    'DetectorTendencias',
    'GeneradorRecomendaciones'
]
