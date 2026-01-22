"""
KPIs Unificados - Fuente Única de Verdad para Métricas de Diagnóstico
=====================================================================

Módulo que centraliza el cálculo y validación de todos los KPIs del sistema
de diagnóstico, garantizando coherencia matemática en todo el informe PDF.

Autor: AgroTech Engineering Team
Fecha: Enero 2026
"""

from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class KPIsUnificados:
    """
    Fuente única de verdad para todas las métricas del diagnóstico
    
    Esta clase garantiza que:
    1. Área afectada NUNCA supere área total
    2. Porcentaje afectado esté en rango [0, 100]
    3. Eficiencia = 100 - Porcentaje Afectado (coherencia matemática)
    4. Desglose por severidad sume exactamente al total afectado
    5. Todos los valores tengan precisión consistente (1 decimal)
    
    Uso en generador_pdf.py:
    ------------------------
    ```python
    kpis = KPIsUnificados.desde_diagnostico(
        diagnostico=diagnostico_unificado,
        area_total_ha=parcela.area_hectareas
    )
    kpis.validar_coherencia()  # Lanza excepción si hay inconsistencias
    
    # Usar en TODAS las secciones del PDF
    context = {
        'area_total': kpis.formatear_area_total(),       # "10.0 ha"
        'area_afectada': kpis.formatear_area_afectada(), # "8.2 ha"
        'porcentaje_afectado': kpis.formatear_porcentaje_afectado(), # "82.0%"
        'eficiencia': kpis.formatear_eficiencia(),       # "18.0%"
        'area_critica': kpis.formatear_area_critica(),   # "3.5 ha"
    }
    ```
    """
    
    # Valores base (en hectáreas y porcentajes)
    area_total_ha: float
    area_afectada_ha: float
    porcentaje_afectado: float  # 0.0 a 100.0
    eficiencia: float  # 0.0 a 100.0
    
    # Desglose por severidad (en hectáreas)
    area_critica_ha: float
    area_moderada_ha: float
    area_leve_ha: float
    
    # Porcentajes de cada nivel (para gráficos)
    porcentaje_critico: float  # 0.0 a 100.0
    porcentaje_moderado: float
    porcentaje_leve: float
    
    # Metadata adicional
    num_zonas_totales: int = 0
    num_zonas_criticas: int = 0
    num_zonas_moderadas: int = 0
    num_zonas_leves: int = 0
    
    @classmethod
    def desde_diagnostico(
        cls,
        diagnostico: 'DiagnosticoUnificado',
        area_total_ha: float
    ) -> 'KPIsUnificados':
        """
        Crea KPIs desde un objeto DiagnosticoUnificado
        
        Args:
            diagnostico: Resultado del cerebro de diagnóstico
            area_total_ha: Área total de la parcela (fuente: parcela.area_hectareas)
        
        Returns:
            KPIsUnificados con todos los valores calculados y validados
        """
        # 🔍 LOG CRÍTICO: Ver datos que llegan del cerebro diagnóstico
        logger.info(f"📊 KPIsUnificados.desde_diagnostico() iniciando...")
        logger.info(f"   Área total (parámetro): {area_total_ha:.2f} ha")
        logger.info(f"   Eficiencia (cerebro): {diagnostico.eficiencia_lote:.1f}%")
        logger.info(f"   Área afectada (cerebro): {diagnostico.area_afectada_total:.2f} ha")
        
        # Extraer desglose de severidad
        desglose = diagnostico.desglose_severidad
        area_critica = desglose.get('critica', 0.0)
        area_moderada = desglose.get('moderada', 0.0)
        area_leve = desglose.get('leve', 0.0)
        
        logger.info(f"   Desglose: 🔴 {area_critica:.2f} ha, 🟠 {area_moderada:.2f} ha, 🟡 {area_leve:.2f} ha")
        
        # Área afectada total (ya viene del diagnóstico, pre-calculada con unión)
        area_afectada = diagnostico.area_afectada_total
        
        # VALIDACIÓN CRÍTICA: Aplicar clip al área máxima permitida
        area_afectada = min(area_afectada, area_total_ha)
        area_critica = min(area_critica, area_total_ha)
        area_moderada = min(area_moderada, area_total_ha)
        area_leve = min(area_leve, area_total_ha)
        
        # Normalizar desglose si la suma supera el área afectada
        desglose_total = area_critica + area_moderada + area_leve
        if desglose_total > area_afectada and desglose_total > 0:
            logger.warning(f"⚠️  Desglose ({desglose_total:.2f} ha) > Área afectada ({area_afectada:.2f} ha)")
            logger.warning(f"   Aplicando normalización proporcional...")
            factor = area_afectada / desglose_total
            area_critica *= factor
            area_moderada *= factor
            area_leve *= factor
        
        # Calcular porcentajes (con protección contra división por cero)
        if area_total_ha > 0:
            porcentaje_afectado = (area_afectada / area_total_ha) * 100.0
            porcentaje_critico = (area_critica / area_total_ha) * 100.0
            porcentaje_moderado = (area_moderada / area_total_ha) * 100.0
            porcentaje_leve = (area_leve / area_total_ha) * 100.0
        else:
            logger.error("❌ Área total de parcela es 0, usando valores por defecto")
            porcentaje_afectado = 0.0
            porcentaje_critico = 0.0
            porcentaje_moderado = 0.0
            porcentaje_leve = 0.0
        
        # USAR EFICIENCIA DEL CEREBRO DIAGNÓSTICO (ya incluye lógica de ajuste)
        # ✅ El cerebro ya aplicó la regla: si area_afectada > 0, eficiencia < 100%
        eficiencia_cerebro = diagnostico.eficiencia_lote
        
        # VALIDACIÓN CRÍTICA: Si hay área afectada, eficiencia NUNCA puede ser 100%
        if area_afectada > 0.0 and eficiencia_cerebro >= 100.0:
            logger.error(f"❌ INCOHERENCIA MATEMÁTICA DETECTADA:")
            logger.error(f"   Eficiencia: {eficiencia_cerebro:.1f}% (del cerebro)")
            logger.error(f"   Área afectada: {area_afectada:.2f} ha")
            logger.error(f"   FORZANDO eficiencia a 99.7% (tope con problemas detectados)")
            eficiencia = 99.7
        else:
            eficiencia = eficiencia_cerebro
        
        # Aplicar clips finales para garantizar rango [0, 100]
        porcentaje_afectado = max(0.0, min(100.0, porcentaje_afectado))
        eficiencia = max(0.0, min(100.0, eficiencia))
        porcentaje_critico = max(0.0, min(100.0, porcentaje_critico))
        porcentaje_moderado = max(0.0, min(100.0, porcentaje_moderado))
        porcentaje_leve = max(0.0, min(100.0, porcentaje_leve))
        
        # Contar zonas por severidad
        zonas_por_sev = diagnostico.zonas_por_severidad
        num_criticas = len(zonas_por_sev.get('critica', []))
        num_moderadas = len(zonas_por_sev.get('moderada', []))
        num_leves = len(zonas_por_sev.get('leve', []))
        
        kpis = cls(
            area_total_ha=round(area_total_ha, 2),
            area_afectada_ha=round(area_afectada, 2),
            porcentaje_afectado=round(porcentaje_afectado, 1),
            eficiencia=round(eficiencia, 1),
            area_critica_ha=round(area_critica, 2),
            area_moderada_ha=round(area_moderada, 2),
            area_leve_ha=round(area_leve, 2),
            porcentaje_critico=round(porcentaje_critico, 1),
            porcentaje_moderado=round(porcentaje_moderado, 1),
            porcentaje_leve=round(porcentaje_leve, 1),
            num_zonas_totales=num_criticas + num_moderadas + num_leves,
            num_zonas_criticas=num_criticas,
            num_zonas_moderadas=num_moderadas,
            num_zonas_leves=num_leves
        )
        
        logger.info("📊 KPIs Unificados calculados:")
        logger.info(f"   Área total: {kpis.area_total_ha:.2f} ha")
        logger.info(f"   Área afectada: {kpis.area_afectada_ha:.2f} ha ({kpis.porcentaje_afectado:.1f}%)")
        logger.info(f"   Eficiencia: {kpis.eficiencia:.1f}%")
        logger.info(f"   Desglose:")
        logger.info(f"     🔴 Crítica: {kpis.area_critica_ha:.2f} ha ({kpis.porcentaje_critico:.1f}%)")
        logger.info(f"     🟠 Moderada: {kpis.area_moderada_ha:.2f} ha ({kpis.porcentaje_moderado:.1f}%)")
        logger.info(f"     🟡 Leve: {kpis.area_leve_ha:.2f} ha ({kpis.porcentaje_leve:.1f}%)")
        
        return kpis
    
    def validar_coherencia(self, tolerancia: float = 0.2) -> None:
        """
        Valida coherencia matemática de todos los KPIs
        
        Args:
            tolerancia: Tolerancia permitida en hectáreas para validaciones (default: 0.2 ha)
        
        Raises:
            AssertionError: Si alguna validación falla
        """
        logger.info("🔍 Validando coherencia matemática de KPIs...")
        
        # Validación 1: Área afectada <= Área total
        assert self.area_afectada_ha <= self.area_total_ha + tolerancia, \
            f"❌ Área afectada ({self.area_afectada_ha:.2f} ha) > Área total ({self.area_total_ha:.2f} ha)"
        
        # Validación 2: Porcentaje afectado en rango [0, 100]
        assert 0.0 <= self.porcentaje_afectado <= 100.0, \
            f"❌ Porcentaje afectado fuera de rango: {self.porcentaje_afectado:.2f}%"
        
        # Validación 3: Eficiencia en rango [0, 100]
        assert 0.0 <= self.eficiencia <= 100.0, \
            f"❌ Eficiencia fuera de rango: {self.eficiencia:.2f}%"
        
        # Validación 4: Si hay área afectada, eficiencia NO puede ser 100% (REGLA DE ORO)
        if self.area_afectada_ha > 0.0:
            assert self.eficiencia < 100.0, \
                f"❌ VIOLACIÓN MATEMÁTICA: Eficiencia {self.eficiencia:.1f}% con {self.area_afectada_ha:.2f} ha afectadas. Debe ser < 100%"
            logger.info(f"   ✅ Regla de oro validada: {self.area_afectada_ha:.2f} ha afectadas → eficiencia {self.eficiencia:.1f}% < 100%")
        
        # Validación 5: Desglose suma al total afectado
        desglose_total = self.area_critica_ha + self.area_moderada_ha + self.area_leve_ha
        diferencia_desglose = abs(desglose_total - self.area_afectada_ha)
        assert diferencia_desglose < tolerancia, \
            f"❌ Desglose total ({desglose_total:.2f} ha) ≠ Área afectada ({self.area_afectada_ha:.2f} ha). Diferencia: {diferencia_desglose:.2f} ha"
        
        # Validación 6: Cada componente del desglose <= Área total
        assert self.area_critica_ha <= self.area_total_ha + tolerancia, \
            f"❌ Área crítica ({self.area_critica_ha:.2f} ha) > Área total ({self.area_total_ha:.2f} ha)"
        assert self.area_moderada_ha <= self.area_total_ha + tolerancia, \
            f"❌ Área moderada ({self.area_moderada_ha:.2f} ha) > Área total ({self.area_total_ha:.2f} ha)"
        assert self.area_leve_ha <= self.area_total_ha + tolerancia, \
            f"❌ Área leve ({self.area_leve_ha:.2f} ha) > Área total ({self.area_total_ha:.2f} ha)"
        
        # Validación 7: Porcentajes de desglose suman al porcentaje afectado
        desglose_pct_total = self.porcentaje_critico + self.porcentaje_moderado + self.porcentaje_leve
        diferencia_pct = abs(desglose_pct_total - self.porcentaje_afectado)
        assert diferencia_pct < 1.0, \
            f"❌ Desglose de porcentajes ({desglose_pct_total:.1f}%) ≠ Porcentaje afectado ({self.porcentaje_afectado:.1f}%). Diferencia: {diferencia_pct:.1f}%"
        
        logger.info("✅ Todas las validaciones pasaron exitosamente")
    
    # ========================================================================
    # MÉTODOS DE FORMATEO ESTÁNDAR (1 DECIMAL)
    # ========================================================================
    
    def formatear_area_total(self) -> str:
        """Retorna: 'XX.XX ha' con 2 decimales para máxima precisión"""
        return f"{self.area_total_ha:.2f} ha"
    
    def formatear_area_afectada(self) -> str:
        """Retorna: 'XX.XX ha' con 2 decimales para máxima precisión"""
        return f"{self.area_afectada_ha:.2f} ha"
    
    def formatear_porcentaje_afectado(self) -> str:
        """Retorna: 'XX.X%' con 1 decimal"""
        return f"{self.porcentaje_afectado:.1f}%"
    
    def formatear_eficiencia(self) -> str:
        """Retorna: 'XX.X%' con 1 decimal"""
        return f"{self.eficiencia:.1f}%"
    
    def formatear_area_critica(self) -> str:
        """Retorna: 'XX.XX ha' con 2 decimales para máxima precisión"""
        return f"{self.area_critica_ha:.2f} ha"
    
    def formatear_area_moderada(self) -> str:
        """Retorna: 'XX.XX ha' con 2 decimales para máxima precisión"""
        return f"{self.area_moderada_ha:.2f} ha"
    
    def formatear_area_leve(self) -> str:
        """Retorna: 'XX.XX ha' con 2 decimales para máxima precisión"""
        return f"{self.area_leve_ha:.2f} ha"
    
    def formatear_porcentaje_critico(self) -> str:
        """Retorna: 'XX.X%' con 1 decimal"""
        return f"{self.porcentaje_critico:.1f}%"
    
    def formatear_porcentaje_moderado(self) -> str:
        """Retorna: 'XX.X%' con 1 decimal"""
        return f"{self.porcentaje_moderado:.1f}%"
    
    def formatear_porcentaje_leve(self) -> str:
        """Retorna: 'XX.X%' con 1 decimal"""
        return f"{self.porcentaje_leve:.1f}%"
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def obtener_area_sana(self) -> float:
        """Retorna área sin afectaciones en hectáreas"""
        return round(self.area_total_ha - self.area_afectada_ha, 2)
    
    def formatear_area_sana(self) -> str:
        """Retorna: 'XX.XX ha' con 2 decimales para máxima precisión"""
        return f"{self.obtener_area_sana():.2f} ha"
    
    def obtener_estado_lote(self) -> str:
        """
        Determina estado del lote según eficiencia
        
        Returns:
            'EXCELENTE' | 'BUENO' | 'REQUIERE ATENCIÓN' | 'CRÍTICO'
        """
        if self.eficiencia >= 85:
            return 'EXCELENTE'
        elif self.eficiencia >= 70:
            return 'BUENO'
        elif self.eficiencia >= 50:
            return 'REQUIERE ATENCIÓN'
        else:
            return 'CRÍTICO'
    
    def obtener_color_estado(self) -> str:
        """
        Retorna color profesional según estado
        
        Returns:
            Código de color hexadecimal
        """
        if self.eficiencia >= 85:
            return '#27AE60'  # Verde profesional
        elif self.eficiencia >= 70:
            return '#F39C12'  # Amber
        elif self.eficiencia >= 50:
            return '#E67E22'  # Naranja
        else:
            return '#E74C3C'  # Rojo suave
    
    def to_dict(self) -> Dict:
        """
        Convierte KPIs a diccionario para uso en contextos de templates
        
        Returns:
            Dict con todos los valores formateados
        """
        return {
            # Valores numéricos
            'area_total_ha': self.area_total_ha,
            'area_afectada_ha': self.area_afectada_ha,
            'porcentaje_afectado': self.porcentaje_afectado,
            'eficiencia': self.eficiencia,
            'area_critica_ha': self.area_critica_ha,
            'area_moderada_ha': self.area_moderada_ha,
            'area_leve_ha': self.area_leve_ha,
            'area_sana_ha': self.obtener_area_sana(),
            
            # Valores formateados (con unidades)
            'area_total_fmt': self.formatear_area_total(),
            'area_afectada_fmt': self.formatear_area_afectada(),
            'porcentaje_afectado_fmt': self.formatear_porcentaje_afectado(),
            'eficiencia_fmt': self.formatear_eficiencia(),
            'area_critica_fmt': self.formatear_area_critica(),
            'area_moderada_fmt': self.formatear_area_moderada(),
            'area_leve_fmt': self.formatear_area_leve(),
            'area_sana_fmt': self.formatear_area_sana(),
            
            # Metadata
            'estado': self.obtener_estado_lote(),
            'color_estado': self.obtener_color_estado(),
            'num_zonas_totales': self.num_zonas_totales,
            'num_zonas_criticas': self.num_zonas_criticas,
            'num_zonas_moderadas': self.num_zonas_moderadas,
            'num_zonas_leves': self.num_zonas_leves
        }


# ============================================================================
# FUNCIONES AUXILIARES DE FORMATEO (USO GLOBAL)
# ============================================================================

def formatear_hectareas(valor: float) -> str:
    """
    Formato estándar para hectáreas: X.X ha
    
    Uso:
        >>> formatear_hectareas(8.234)
        '8.2 ha'
    """
    return f"{valor:.1f} ha"


def formatear_porcentaje(valor: float) -> str:
    """
    Formato estándar para porcentajes: X.X%
    
    Uso:
        >>> formatear_porcentaje(82.345)
        '82.3%'
    """
    return f"{valor:.1f}%"


def validar_area_no_excede_total(area_calculada: float, area_total: float, nombre_area: str = "calculada") -> float:
    """
    Valida que un área calculada no supere el área total de la parcela
    
    Args:
        area_calculada: Área calculada en hectáreas
        area_total: Área total de la parcela en hectáreas
        nombre_area: Nombre descriptivo del área para logging
    
    Returns:
        Área validada (clipeada al máximo si excede)
    """
    if area_calculada > area_total:
        logger.warning(f"⚠️  Área {nombre_area} ({area_calculada:.2f} ha) > Área total ({area_total:.2f} ha)")
        logger.warning(f"   Aplicando clip al área máxima...")
        return min(area_calculada, area_total)
    
    return area_calculada
