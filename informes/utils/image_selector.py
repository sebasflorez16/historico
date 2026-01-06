"""
Utilidad para seleccionar y limitar imágenes satelitales para análisis con Gemini AI
Optimiza el consumo de tokens y peticiones a la API
"""
from typing import List, Dict, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Configuración de límites
MAX_IMAGENES_POR_INFORME = 10  # Límite por defecto
MAX_IMAGENES_ANALISIS_COMPLETO = 30  # Para análisis completo (requiere plan de pago)


class ImagenSelector:
    """Selecciona las mejores imágenes para análisis con Gemini AI"""
    
    def __init__(self, max_imagenes: int = MAX_IMAGENES_POR_INFORME):
        self.max_imagenes = max_imagenes
    
    def seleccionar_mejores_imagenes(self, indices_mensuales: List, 
                                     tipo_analisis: str = 'rapido') -> Tuple[List, Dict]:
        """
        Selecciona las mejores N imágenes según calidad, nubosidad y fecha.
        
        Args:
            indices_mensuales: QuerySet o lista de IndiceMensual
            tipo_analisis: 'rapido' (10 imgs) o 'completo' (30 imgs)
        
        Returns:
            Tuple con (indices_seleccionados, estadisticas)
        """
        # Determinar límite según tipo de análisis
        limite = MAX_IMAGENES_ANALISIS_COMPLETO if tipo_analisis == 'completo' else self.max_imagenes
        
        # Convertir QuerySet a lista para manipulación
        indices_lista = list(indices_mensuales)
        total_disponibles = len(indices_lista)
        
        logger.info(f"📊 Seleccionando mejores {limite} imágenes de {total_disponibles} disponibles")
        
        # Si hay menos imágenes que el límite, usar todas
        if total_disponibles <= limite:
            logger.info(f"✅ Usando todas las {total_disponibles} imágenes disponibles")
            return indices_lista, {
                'total_disponibles': total_disponibles,
                'total_seleccionadas': total_disponibles,
                'criterio': 'todas_disponibles'
            }
        
        # Priorizar imágenes por calidad
        indices_puntuados = []
        
        for idx in indices_lista:
            puntuacion = self._calcular_puntuacion_imagen(idx)
            indices_puntuados.append((idx, puntuacion))
        
        # Ordenar por puntuación descendente
        indices_puntuados.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar las mejores N
        indices_seleccionados = [idx for idx, _ in indices_puntuados[:limite]]
        
        # Ordenar cronológicamente para el análisis
        indices_seleccionados.sort(key=lambda x: (x.año, x.mes))
        
        estadisticas = {
            'total_disponibles': total_disponibles,
            'total_seleccionadas': len(indices_seleccionados),
            'criterio': 'calidad_y_cobertura',
            'puntuacion_promedio': sum(p for _, p in indices_puntuados[:limite]) / limite,
            'imagenes_descartadas': total_disponibles - limite
        }
        
        logger.info(f"✅ Seleccionadas {len(indices_seleccionados)} imágenes (puntuación promedio: {estadisticas['puntuacion_promedio']:.2f})")
        
        return indices_seleccionados, estadisticas
    
    def _calcular_puntuacion_imagen(self, indice) -> float:
        """
        Calcula puntuación de calidad de una imagen según múltiples criterios.
        Puntuación más alta = mejor imagen.
        
        Criterios:
        - Nubosidad (40% peso): menos nubes = mejor
        - Calidad de datos (30% peso): excelente > buena > aceptable > baja
        - Fecha (20% peso): más reciente = mejor
        - Cobertura de índices (10% peso): más índices disponibles = mejor
        """
        puntuacion = 0.0
        
        # 1. NUBOSIDAD (40% del peso total, max 40 puntos)
        # Menos nubes = mejor
        nubosidad = getattr(indice, 'nubosidad_imagen', None) or getattr(indice, 'nubosidad_promedio', 50)
        puntuacion_nubosidad = (100 - nubosidad) * 0.4
        puntuacion += puntuacion_nubosidad
        
        # 2. CALIDAD DE DATOS (30% del peso total, max 30 puntos)
        calidad = getattr(indice, 'calidad_datos', 'buena')
        if calidad:
            calidad_map = {
                'excelente': 30,
                'buena': 22,
                'aceptable': 15,
                'baja': 5
            }
            puntuacion += calidad_map.get(calidad.lower(), 15)
        
        # 3. FECHA (20% del peso total, max 20 puntos)
        # Más reciente = mejor
        try:
            # Calcular antigüedad en meses desde hoy
            hoy = date.today()
            fecha_indice = date(indice.año, indice.mes, 1)
            diferencia_meses = (hoy.year - fecha_indice.year) * 12 + (hoy.month - fecha_indice.month)
            
            # Penalizar por antigüedad (máximo 24 meses)
            puntuacion_fecha = max(0, 20 - (diferencia_meses * 0.5))
            puntuacion += puntuacion_fecha
        except:
            puntuacion += 10  # Puntuación neutral si hay error
        
        # 4. COBERTURA DE ÍNDICES (10% del peso total, max 10 puntos)
        # Más índices disponibles = mejor
        indices_disponibles = 0
        if getattr(indice, 'imagen_ndvi', None):
            indices_disponibles += 1
        if getattr(indice, 'imagen_ndmi', None):
            indices_disponibles += 1
        if getattr(indice, 'imagen_savi', None):
            indices_disponibles += 1
        
        puntuacion_indices = (indices_disponibles / 3) * 10
        puntuacion += puntuacion_indices
        
        return puntuacion
    
    def estimar_costo_analisis(self, num_imagenes: int, tokens_por_imagen: int = 500) -> Dict:
        """
        Estima el costo en tokens y peticiones de un análisis.
        
        Args:
            num_imagenes: Número de imágenes a analizar
            tokens_por_imagen: Tokens promedio por imagen (default 500)
        
        Returns:
            Dict con estimación de costos
        """
        total_tokens = num_imagenes * tokens_por_imagen
        total_peticiones = num_imagenes
        
        return {
            'num_imagenes': num_imagenes,
            'tokens_por_imagen': tokens_por_imagen,
            'total_tokens': total_tokens,
            'total_peticiones': total_peticiones,
            'puede_usar_gratis': total_peticiones <= 10,  # Límite típico free tier
            'mensaje': self._generar_mensaje_costo(total_peticiones, total_tokens)
        }
    
    def _generar_mensaje_costo(self, peticiones: int, tokens: int) -> str:
        """Genera mensaje informativo sobre el costo del análisis"""
        if peticiones <= 10:
            return f"✅ {peticiones} peticiones (~{tokens} tokens). Compatible con plan gratuito."
        elif peticiones <= 20:
            return f"⚠️ {peticiones} peticiones (~{tokens} tokens). Puede requerir plan de pago."
        else:
            return f"❌ {peticiones} peticiones (~{tokens} tokens). Requiere plan de pago o reducir imágenes."


# Instancia global del selector (con límite por defecto de 10 imágenes)
image_selector = ImagenSelector(max_imagenes=MAX_IMAGENES_POR_INFORME)
