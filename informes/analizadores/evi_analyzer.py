"""
Analizador EVI - Enhanced Vegetation Index
Interpreta biomasa y estructura del dosel sin saturación
Especialmente relevante para cultivos densos como palma aceitera
"""
import statistics
from typing import Dict, List, Any


class AnalizadorEVI:
    """
    Analiza datos de EVI - resistente a saturación en biomasa alta
    
    EVI incorpora corrección atmosférica (banda Blue) y no satura donde
    NDVI pierde sensibilidad (LAI > 3). Ideal para cultivos densos tropicales.
    Ideal para: palma aceitera, café, cacao, bosques, cultivos con dosel cerrado.
    """
    
    UMBRAL_BAJO = 0.3
    UMBRAL_MODERADO = 0.45
    UMBRAL_BUENO = 0.6
    UMBRAL_EXCELENTE = 0.75
    
    def __init__(self, tipo_cultivo: str = "General"):
        self.tipo_cultivo = tipo_cultivo
        if tipo_cultivo.lower() in ('palma', 'palma_aceitera', 'palma africana', 'oil_palm'):
            self.UMBRAL_BAJO = 0.35
            self.UMBRAL_MODERADO = 0.5
            self.UMBRAL_BUENO = 0.65
            self.UMBRAL_EXCELENTE = 0.8
    
    def analizar(self, datos_evi: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza serie temporal de EVI"""
        if not datos_evi:
            return self._resultado_sin_datos()
        
        valores = [d.get('evi', 0) for d in datos_evi if d.get('evi') is not None]
        
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
            'indice': 'EVI',
            'nombre': 'Índice de Vegetación Mejorado',
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
            'densidad_dosel_estimada': self._estimar_densidad_dosel(promedio)
        }
    
    def _calcular_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula tendencia temporal"""
        if len(valores) < 3:
            return {'direccion': 'estable', 'magnitud': 0, 'cambio_porcentual': 0,
                    'descripcion': 'Datos insuficientes'}
        
        n = len(valores)
        cambio_promedio = sum(valores[i] - valores[i-1] for i in range(1, n)) / (n - 1)
        cambio_porcentual = (valores[-1] - valores[0]) / valores[0] * 100 if valores[0] != 0 else 0
        
        if abs(cambio_promedio) < 0.02:
            direccion = 'estable'
            descripcion = 'Biomasa y estructura del dosel estables'
        elif cambio_promedio > 0.04:
            direccion = 'ascendente_fuerte'
            descripcion = 'Aumento significativo de biomasa'
        elif cambio_promedio > 0:
            direccion = 'ascendente'
            descripcion = 'Biomasa en aumento'
        elif cambio_promedio < -0.04:
            direccion = 'descendente_fuerte'
            descripcion = 'Pérdida significativa de biomasa'
        else:
            direccion = 'descendente'
            descripcion = 'Biomasa en descenso'
        
        return {
            'direccion': direccion,
            'magnitud': round(cambio_promedio, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'descripcion': descripcion
        }
    
    def _clasificar_estado(self, promedio: float) -> Dict[str, str]:
        """Clasifica estado de biomasa"""
        if promedio < self.UMBRAL_BAJO:
            return {
                'nivel': 'bajo',
                'etiqueta': 'Biomasa Baja',
                'color': '#fd7e14',
                'icono': '⚠️'
            }
        elif promedio < self.UMBRAL_MODERADO:
            return {
                'nivel': 'moderado',
                'etiqueta': 'Biomasa Moderada',
                'color': '#ffc107',
                'icono': '📊'
            }
        elif promedio < self.UMBRAL_BUENO:
            return {
                'nivel': 'bueno',
                'etiqueta': 'Alta Biomasa',
                'color': '#28a745',
                'icono': '✅'
            }
        else:
            return {
                'nivel': 'excelente',
                'etiqueta': 'Biomasa Óptima',
                'color': '#20c997',
                'icono': '🌟'
            }
    
    def _generar_interpretacion_tecnica(self, promedio: float, desv_std: float,
                                       tendencia: Dict, estado: Dict) -> str:
        """Interpretación técnica"""
        interpretacion = f"""
<strong>Análisis EVI - Biomasa y Estructura del Dosel</strong><br><br>

El EVI promedio de <strong>{promedio:.3f}</strong> indica 
<strong>{estado['etiqueta'].lower()}</strong>.<br><br>

<strong>Parámetros de Biomasa:</strong><br>
• Densidad del dosel estimada: <strong>{self._estimar_densidad_dosel(promedio)}</strong><br>
• Índice de área foliar (LAI) estimado: <strong>{self._estimar_lai(promedio)}</strong><br>
• Variabilidad espacial: σ={desv_std:.3f}<br><br>

<strong>Ventaja sobre NDVI:</strong><br>
EVI no pierde sensibilidad en doseles densos (LAI &gt; 3) donde NDVI se satura.
Incluye corrección atmosférica usando banda azul, importante en zonas tropicales húmedas.
{self._interpretar_evi_tecnica(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{tendencia['descripcion']} ({tendencia['cambio_porcentual']:+.1f}%).
"""
        return interpretacion.strip()
    
    def _generar_interpretacion_simple(self, promedio: float, tendencia: Dict, estado: Dict) -> str:
        """Interpretación simple para el agricultor"""
        interpretacion = f"""
<strong>¿Cuánta vegetación tiene su cultivo?</strong><br><br>

{estado['icono']} La biomasa de su parcela es <strong>{estado['etiqueta'].lower()}</strong>. 
{self._explicar_simple(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{self._explicar_tendencia_simple(tendencia)}
"""
        return interpretacion.strip()
    
    def _generar_alertas(self, promedio: float, tendencia: Dict) -> List[Dict]:
        """Genera alertas de biomasa"""
        alertas = []
        
        if promedio < self.UMBRAL_BAJO:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'media',
                'icono': '🌿',
                'titulo': 'Biomasa Baja Detectada',
                'mensaje': f'EVI de {promedio:.2f} indica baja biomasa o dosel poco denso.',
                'accion': 'Verificar estado del dosel, posible defoliación o pérdida de hojas'
            })
        
        if tendencia['direccion'] in ['descendente', 'descendente_fuerte']:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'media',
                'icono': '📉',
                'titulo': 'Reducción de Biomasa',
                'mensaje': f"La biomasa ha disminuido {abs(tendencia['cambio_porcentual']):.1f}%.",
                'accion': 'Investigar causa: defoliación, poda excesiva o estrés'
            })
        
        return alertas
    
    def _resultado_sin_datos(self) -> Dict:
        """Resultado cuando no hay datos"""
        return {
            'indice': 'EVI',
            'nombre': 'Índice de Vegetación Mejorado',
            'error': 'No hay datos disponibles',
            'estadisticas': {},
            'estado': {'nivel': 'sin_datos', 'etiqueta': 'Sin Datos', 'icono': '❓'},
            'interpretacion_tecnica': 'No hay datos EVI disponibles.',
            'interpretacion_simple': 'Aún no tenemos información sobre la biomasa.',
            'alertas': []
        }
    
    def _estimar_densidad_dosel(self, evi: float) -> str:
        """Estima densidad del dosel"""
        if evi < 0.25:
            return 'Muy abierto (<30%)'
        elif evi < 0.4:
            return 'Abierto (30-50%)'
        elif evi < 0.55:
            return 'Moderado (50-70%)'
        elif evi < 0.7:
            return 'Denso (70-85%)'
        else:
            return 'Cerrado (>85%)'
    
    def _estimar_lai(self, evi: float) -> str:
        """Estima índice de área foliar (LAI)"""
        lai_estimado = evi * 6.0  # Aproximación lineal simplificada
        if lai_estimado < 1:
            return f'{lai_estimado:.1f} (bajo)'
        elif lai_estimado < 3:
            return f'{lai_estimado:.1f} (moderado)'
        elif lai_estimado < 5:
            return f'{lai_estimado:.1f} (alto)'
        else:
            return f'{lai_estimado:.1f} (muy alto)'
    
    def _interpretar_evi_tecnica(self, evi: float) -> str:
        """Interpretación técnica del valor EVI"""
        if evi < 0.3:
            return ("Baja biomasa. En palma aceitera puede indicar palmas jóvenes, "
                    "defoliación por plagas o estrés severo.")
        elif evi < 0.45:
            return ("Biomasa moderada. Normal en plantaciones jóvenes o en recuperación. "
                    "Monitorear evolución mensual.")
        elif evi < 0.6:
            return ("Buena biomasa con dosel bien establecido. "
                    "Productividad fotosintética adecuada.")
        else:
            return ("Biomasa óptima con dosel cerrado. Alta capacidad fotosintética. "
                    "En palma adulta, indica plantación productiva bien manejada.")
    
    def _explicar_simple(self, evi: float) -> str:
        """Explicación simple"""
        if evi < 0.3:
            return "Las plantas tienen poca masa vegetal. Puede ser normal si son jóvenes."
        elif evi < 0.45:
            return "La vegetación está creciendo. Hay espacio para mejorar la densidad."
        elif evi < 0.6:
            return "Buena cantidad de vegetación. Las plantas se ven saludables y densas."
        else:
            return "¡Excelente! Máxima vegetación posible. Las plantas están en su mejor momento productivo."
    
    def _explicar_tendencia_simple(self, tendencia: Dict) -> str:
        """Explicación simple de tendencia"""
        if 'ascendente' in tendencia['direccion']:
            return (f"📈 La vegetación está ganando masa "
                    f"({tendencia['cambio_porcentual']:.0f}% más). ¡Está creciendo bien!")
        elif 'descendente' in tendencia['direccion']:
            return (f"📉 La vegetación está perdiendo masa "
                    f"({abs(tendencia['cambio_porcentual']):.0f}% menos). Revisar qué está pasando.")
        else:
            return "➡️ La vegetación se mantiene estable. Sin cambios importantes."
    
    def _calcular_puntuacion(self, promedio: float, tendencia: Dict) -> float:
        """Calcula puntuación 0-10"""
        puntuacion_base = min((promedio / 0.8) * 10, 10)
        
        if tendencia['direccion'] == 'ascendente_fuerte':
            ajuste = 0.5
        elif tendencia['direccion'] == 'descendente_fuerte':
            ajuste = -0.5
        else:
            ajuste = 0
        
        return round(max(0, min(10, puntuacion_base + ajuste)), 1)
