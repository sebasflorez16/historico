"""
Analizador NDRE - Normalized Difference Red Edge
Interpreta contenido de clorofila y nitrógeno foliar
Especialmente relevante para palma aceitera (correlación 88% con N foliar)
"""
import statistics
from typing import Dict, List, Any


class AnalizadorNDRE:
    """
    Analiza datos de NDRE - sensible a clorofila profunda y estado nutricional
    
    NDRE usa la banda de borde rojo (Red Edge, ~720nm) que penetra más
    en el dosel que Red, detectando estrés nutricional antes que NDVI.
    Ideal para: palma aceitera, cultivos perennes densos, detección temprana de deficiencia N.
    """
    
    UMBRAL_BAJO = 0.2
    UMBRAL_MODERADO = 0.35
    UMBRAL_BUENO = 0.5
    UMBRAL_EXCELENTE = 0.65
    
    def __init__(self, tipo_cultivo: str = "General"):
        self.tipo_cultivo = tipo_cultivo
        if tipo_cultivo.lower() in ('palma', 'palma_aceitera', 'palma africana', 'oil_palm'):
            self.UMBRAL_BAJO = 0.22
            self.UMBRAL_MODERADO = 0.35
            self.UMBRAL_BUENO = 0.48
            self.UMBRAL_EXCELENTE = 0.60
    
    def analizar(self, datos_ndre: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza serie temporal de NDRE"""
        if not datos_ndre:
            return self._resultado_sin_datos()
        
        valores = [d.get('ndre', 0) for d in datos_ndre if d.get('ndre') is not None]
        
        if not valores:
            return self._resultado_sin_datos()
        
        promedio = statistics.mean(valores)
        mediana = statistics.median(valores)
        minimo = min(valores)
        maximo = max(valores)
        desv_std = statistics.stdev(valores) if len(valores) > 1 else 0
        
        tendencia = self._calcular_tendencia(valores)
        estado = self._clasificar_estado(promedio)
        
        interpretacion_tecnica = self._generar_interpretacion_tecnica(
            promedio, desv_std, tendencia, estado
        )
        interpretacion_simple = self._generar_interpretacion_simple(
            promedio, tendencia, estado
        )
        alertas = self._generar_alertas(promedio, tendencia)
        
        return {
            'indice': 'NDRE',
            'nombre': 'Índice de Borde Rojo Normalizado',
            'estadisticas': {
                'promedio': round(promedio, 3),
                'mediana': round(mediana, 3),
                'minimo': round(minimo, 3),
                'maximo': round(maximo, 3),
                'desviacion_estandar': round(desv_std, 3)
            },
            'estado': estado,
            'tendencia': tendencia,
            'interpretacion_tecnica': interpretacion_tecnica,
            'interpretacion_simple': interpretacion_simple,
            'alertas': alertas,
            'puntuacion': self._calcular_puntuacion(promedio, tendencia),
            'nivel_nitrogeno_estimado': self._estimar_nivel_nitrogeno(promedio)
        }
    
    def _calcular_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula tendencia temporal"""
        if len(valores) < 3:
            return {'direccion': 'estable', 'magnitud': 0, 'cambio_porcentual': 0,
                    'descripcion': 'Datos insuficientes'}
        
        n = len(valores)
        cambio_promedio = sum(valores[i] - valores[i-1] for i in range(1, n)) / (n - 1)
        cambio_porcentual = (valores[-1] - valores[0]) / valores[0] * 100 if valores[0] != 0 else 0
        
        if abs(cambio_promedio) < 0.015:
            direccion = 'estable'
            descripcion = 'Contenido de clorofila estable'
        elif cambio_promedio > 0.03:
            direccion = 'ascendente_fuerte'
            descripcion = 'Aumento significativo de clorofila/nitrógeno'
        elif cambio_promedio > 0:
            direccion = 'ascendente'
            descripcion = 'Clorofila en aumento'
        elif cambio_promedio < -0.03:
            direccion = 'descendente_fuerte'
            descripcion = 'Pérdida significativa de clorofila/nitrógeno'
        else:
            direccion = 'descendente'
            descripcion = 'Clorofila en descenso'
        
        return {
            'direccion': direccion,
            'magnitud': round(cambio_promedio, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'descripcion': descripcion
        }
    
    def _clasificar_estado(self, promedio: float) -> Dict[str, str]:
        """Clasifica estado nutricional"""
        if promedio < self.UMBRAL_BAJO:
            return {
                'nivel': 'bajo',
                'etiqueta': 'Deficiencia Nutricional',
                'color': '#dc3545',
                'icono': '🔴'
            }
        elif promedio < self.UMBRAL_MODERADO:
            return {
                'nivel': 'moderado',
                'etiqueta': 'Nutrición Moderada',
                'color': '#ffc107',
                'icono': '🟡'
            }
        elif promedio < self.UMBRAL_BUENO:
            return {
                'nivel': 'bueno',
                'etiqueta': 'Buena Nutrición',
                'color': '#28a745',
                'icono': '✅'
            }
        else:
            return {
                'nivel': 'excelente',
                'etiqueta': 'Nutrición Óptima',
                'color': '#20c997',
                'icono': '🌟'
            }
    
    def _generar_interpretacion_tecnica(self, promedio: float, desv_std: float,
                                       tendencia: Dict, estado: Dict) -> str:
        """Interpretación técnica"""
        interpretacion = f"""
<strong>Análisis NDRE - Contenido de Clorofila y Nitrógeno</strong><br><br>

El NDRE promedio de <strong>{promedio:.3f}</strong> indica 
<strong>{estado['etiqueta'].lower()}</strong>.<br><br>

<strong>Parámetros Nutricionales:</strong><br>
• Nivel de nitrógeno estimado: <strong>{self._estimar_nivel_nitrogeno(promedio)}</strong><br>
• Contenido de clorofila: <strong>{self._estimar_clorofila(promedio)}</strong><br>
• Variabilidad espacial: σ={desv_std:.3f}<br><br>

<strong>Interpretación Agronómica:</strong><br>
NDRE utiliza la banda de borde rojo (Red Edge ~720nm) que penetra más profundamente
en el dosel vegetal. Detecta estrés nutricional 2-3 semanas antes que NDVI.
{self._interpretar_ndre_tecnica(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{tendencia['descripcion']} ({tendencia['cambio_porcentual']:+.1f}%).
"""
        return interpretacion.strip()
    
    def _generar_interpretacion_simple(self, promedio: float, tendencia: Dict, estado: Dict) -> str:
        """Interpretación simple para el agricultor"""
        interpretacion = f"""
<strong>¿Cómo está la nutrición del cultivo?</strong><br><br>

{estado['icono']} El estado nutricional es <strong>{estado['etiqueta'].lower()}</strong>. 
{self._explicar_simple(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{self._explicar_tendencia_simple(tendencia)}
"""
        return interpretacion.strip()
    
    def _generar_alertas(self, promedio: float, tendencia: Dict) -> List[Dict]:
        """Genera alertas nutricionales"""
        alertas = []
        
        if promedio < self.UMBRAL_BAJO:
            alertas.append({
                'tipo': 'critica',
                'prioridad': 'alta',
                'icono': '🔴',
                'titulo': 'Deficiencia de Nitrógeno Detectada',
                'mensaje': f'NDRE de {promedio:.2f} indica deficiencia nutricional significativa.',
                'accion': 'Realizar análisis foliar urgente y evaluar plan de fertilización nitrogenada'
            })
        elif promedio < self.UMBRAL_MODERADO:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'media',
                'icono': '🟡',
                'titulo': 'Nutrición Sub-óptima',
                'mensaje': f'NDRE de {promedio:.2f} sugiere contenido bajo de clorofila.',
                'accion': 'Monitorear y considerar fertilización complementaria'
            })
        
        if tendencia['direccion'] in ['descendente', 'descendente_fuerte']:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'media',
                'icono': '📉',
                'titulo': 'Reducción de Clorofila',
                'mensaje': f"El contenido de clorofila ha disminuido {abs(tendencia['cambio_porcentual']):.1f}%.",
                'accion': 'Investigar causa: estrés nutricional, hídrico o fitosanitario'
            })
        
        return alertas
    
    def _resultado_sin_datos(self) -> Dict:
        """Resultado cuando no hay datos"""
        return {
            'indice': 'NDRE',
            'nombre': 'Índice de Borde Rojo Normalizado',
            'error': 'No hay datos disponibles',
            'estadisticas': {},
            'estado': {'nivel': 'sin_datos', 'etiqueta': 'Sin Datos', 'icono': '❓'},
            'interpretacion_tecnica': 'No hay datos NDRE disponibles.',
            'interpretacion_simple': 'Aún no tenemos información sobre nutrición del cultivo.',
            'alertas': []
        }
    
    def _estimar_nivel_nitrogeno(self, ndre: float) -> str:
        """Estima nivel de nitrógeno foliar"""
        if ndre < 0.15:
            return 'Muy Deficiente'
        elif ndre < 0.25:
            return 'Deficiente'
        elif ndre < 0.4:
            return 'Moderado'
        elif ndre < 0.55:
            return 'Adecuado'
        else:
            return 'Óptimo'
    
    def _estimar_clorofila(self, ndre: float) -> str:
        """Estima contenido de clorofila"""
        if ndre < 0.2:
            return 'Bajo (posible clorosis)'
        elif ndre < 0.35:
            return 'Moderado'
        elif ndre < 0.5:
            return 'Bueno'
        else:
            return 'Alto'
    
    def _interpretar_ndre_tecnica(self, ndre: float) -> str:
        """Interpretación técnica del valor NDRE"""
        if ndre < 0.2:
            return ("Valores bajos sugieren deficiencia de nitrógeno o clorofila. "
                    "Realizar análisis foliar para confirmar. Considerar fertilización nitrogenada urgente.")
        elif ndre < 0.35:
            return ("Contenido moderado de clorofila. Monitorear evolución y considerar "
                    "fertilización de mantenimiento según análisis de suelo.")
        elif ndre < 0.5:
            return ("Buen contenido de clorofila indicando nutrición adecuada. "
                    "Mantener plan de fertilización actual.")
        else:
            return ("Contenido óptimo de clorofila y nitrógeno. Dosel altamente productivo. "
                    "El plan nutricional actual es efectivo.")
    
    def _explicar_simple(self, ndre: float) -> str:
        """Explicación simple"""
        if ndre < 0.2:
            return ("Las plantas muestran señales de falta de nutrientes. "
                    "Es como si estuvieran 'hambrientas' de nitrógeno.")
        elif ndre < 0.35:
            return "Las plantas tienen nutrientes aceptables pero podrían mejorar con fertilización."
        elif ndre < 0.5:
            return "Las plantas están bien alimentadas. El verde de las hojas es saludable."
        else:
            return "¡Excelente! Las plantas tienen nutrición óptima, las hojas están verdes y productivas."
    
    def _explicar_tendencia_simple(self, tendencia: Dict) -> str:
        """Explicación simple de tendencia"""
        if 'ascendente' in tendencia['direccion']:
            return (f"📈 Las plantas se están nutriendo mejor "
                    f"({tendencia['cambio_porcentual']:.0f}% mejora). ¡Buena señal!")
        elif 'descendente' in tendencia['direccion']:
            return (f"📉 Las plantas muestran menos nutrición "
                    f"({abs(tendencia['cambio_porcentual']):.0f}% menos). Revisar fertilización.")
        else:
            return "➡️ La nutrición se mantiene estable. Sin cambios importantes."
    
    def _calcular_puntuacion(self, promedio: float, tendencia: Dict) -> float:
        """Calcula puntuación 0-10"""
        puntuacion_base = min((promedio / 0.7) * 10, 10)
        
        if tendencia['direccion'] == 'ascendente_fuerte':
            ajuste = 0.5
        elif tendencia['direccion'] == 'descendente_fuerte':
            ajuste = -0.5
        else:
            ajuste = 0
        
        return round(max(0, min(10, puntuacion_base + ajuste)), 1)
