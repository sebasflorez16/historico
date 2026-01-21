# 🔍 AUDITORÍA COMPLETA: Errores Matemáticos y Lógicos del Sistema de Diagnóstico

**Fecha:** Enero 2026  
**Sistema:** AgroTech Histórico - Generación de Informes PDF  
**Módulo Principal:** `cerebro_diagnostico.py` + `generador_pdf.py`

---

## 📋 RESUMEN EJECUTIVO

Se han identificado **5 problemas matemáticos y de lógica críticos** en el sistema de diagnóstico satelital:

### ✅ PROBLEMAS CORREGIDOS (Correcciones Previas)
1. ✓ Unión de máscaras implementada (`_calcular_area_afectada_union`)
2. ✓ Normalización de porcentajes con clip [0, 100]
3. ✓ Validación pixel-a-hectárea
4. ✓ Eliminación de gráficos obsoletos (comparación de barras)

### ⚠️ PROBLEMAS PENDIENTES (Esta Auditoría)
1. **Área afectada > Área total del lote** (validación insuficiente)
2. **KPIs inconsistentes entre secciones del PDF** (eficiencia vs área afectada)
3. **Umbrales de severidad irreales** (100% del lote sale como crítico)
4. **Falta de recorte por máscara del polígono** (análisis incluye áreas fuera del cultivo)
5. **Inconsistencia de decimales** (1 decimal vs 2 decimales)

---

## 🔴 PROBLEMA #1: Área Afectada Supera Área Total

### Descripción del Error
El cálculo de área afectada mediante unión de máscaras puede superar el área total de la parcela debido a:
- Reconstrucción de máscaras desde bbox (aproximación rectangular)
- No se aplica máscara del polígono de cultivo (cropeo)
- El clip final es reactivo, no preventivo

### Ubicación del Código
**Archivo:** `informes/motor_analisis/cerebro_diagnostico.py`  
**Función:** `_calcular_area_afectada_union()` (línea ~915)

```python
# CORRECCIÓN ACTUAL (INSUFICIENTE)
if area_hectareas > self.area_parcela_ha:
    logger.error(f"❌ ADVERTENCIA: Área calculada ({area_hectareas:.2f} ha) > Área parcela")
    area_hectareas = self.area_parcela_ha  # Clip post-facto
```

### Impacto
- **Matemática incorrecta:** 15.2 ha afectadas de 10.0 ha totales
- **KPIs incoherentes:** Eficiencia 45% pero 152% afectado
- **Pérdida de confianza del cliente**

### Solución Propuesta
```python
# CORRECCIÓN: Aplicar MÁSCARA DEL POLÍGONO antes de calcular unión
def _calcular_area_afectada_union(self, zonas, shape, mascara_cultivo=None):
    """
    Args:
        mascara_cultivo: np.ndarray (bool) - Máscara del polígono real del lote
    """
    mascara_union = np.zeros(shape, dtype=bool)
    
    for zona in zonas:
        mascara_zona = self._reconstruir_mascara_zona(zona, shape)
        mascara_union = np.logical_or(mascara_union, mascara_zona)
    
    # ✅ APLICAR RECORTE POR POLÍGONO REAL
    if mascara_cultivo is not None:
        mascara_union = np.logical_and(mascara_union, mascara_cultivo)
    
    pixeles_afectados = np.sum(mascara_union)
    area_hectareas = np.clip(
        pixeles_afectados * self.area_pixel_ha,
        0.0,
        self.area_parcela_ha  # Hard limit
    )
    
    return area_hectareas, mascara_union
```

---

## 🔴 PROBLEMA #2: KPIs Inconsistentes Entre Secciones

### Descripción del Error
Los KPIs (área afectada, porcentaje afectado, eficiencia) se calculan en múltiples lugares sin usar una **única fuente de verdad**:

1. **Sección 1 (Resumen Ejecutivo):** `eficiencia_lote = 45%`
2. **Sección 2 (Tabla de Severidad):** `area_afectada = 8.2 ha (82%)`
3. **Sección 3 (Diagnóstico Detallado):** `porcentaje_afectado = 55%`

### Ubicación del Código
**Archivo:** `informes/generador_pdf.py`  
**Funciones:**
- `_crear_resumen_ejecutivo()` (línea ~936)
- `_crear_seccion_guia_intervencion()` (línea ~2129)
- Múltiples cálculos ad-hoc de porcentajes

### Impacto
- Cliente recibe información contradictoria
- Imposible validar coherencia matemática
- Pérdida de credibilidad del informe

### Solución Propuesta
**Crear un único objeto de KPIs calculado al inicio:**

```python
@dataclass
class KPIsUnificados:
    """Fuente única de verdad para métricas del lote"""
    area_total_ha: float
    area_afectada_ha: float
    porcentaje_afectado: float  # Calculado: (afectada / total) * 100
    eficiencia: float  # Calculado: 100 - porcentaje_afectado
    
    # Desglose por severidad
    area_critica_ha: float
    area_moderada_ha: float
    area_leve_ha: float
    
    def validar_coherencia(self):
        """Validación matemática de KPIs"""
        assert self.area_afectada_ha <= self.area_total_ha, "Área afectada > total"
        assert 0 <= self.porcentaje_afectado <= 100, "Porcentaje fuera de rango [0,100]"
        assert abs(self.eficiencia - (100 - self.porcentaje_afectado)) < 0.1, "Eficiencia incoherente"
        desglose_total = self.area_critica_ha + self.area_moderada_ha + self.area_leve_ha
        assert abs(desglose_total - self.area_afectada_ha) < 0.01, "Desglose no suma al total"
```

**Usar en todo el PDF:**
```python
# Calcular UNA SOLA VEZ al inicio
kpis = KPIsUnificados(
    area_total_ha=parcela.area_hectareas,
    area_afectada_ha=diagnostico.area_afectada_total,
    porcentaje_afectado=(diagnostico.area_afectada_total / parcela.area_hectareas) * 100,
    eficiencia=100 - ((diagnostico.area_afectada_total / parcela.area_hectareas) * 100),
    area_critica_ha=diagnostico.desglose_severidad['critica'],
    area_moderada_ha=diagnostico.desglose_severidad['moderada'],
    area_leve_ha=diagnostico.desglose_severidad['leve']
)
kpis.validar_coherencia()

# Usar en TODAS las secciones del PDF
context = {
    'kpis': kpis,  # Única fuente de verdad
    'diagnostico': diagnostico
}
```

---

## 🔴 PROBLEMA #3: Umbrales de Severidad Irreales

### Descripción del Error
Los umbrales de severidad actuales son **demasiado estrictos**, causando que el 100% del lote sea clasificado como "crítico":

**Configuración Actual:**
```python
UMBRALES_CRITICOS = {
    'deficit_hidrico_recurrente': {
        'ndvi_max': 0.45,  # ❌ MUY ESTRICTO
        'ndmi_max': 0.05,  # ❌ MUY ESTRICTO
        'severidad_base': 0.85  # ❌ TODO ES CRÍTICO
    },
    'baja_densidad_suelo_degradado': {
        'ndvi_max': 0.45,  # ❌ MUY ESTRICTO
        'savi_max': 0.35,  # ❌ MUY ESTRICTO
        'severidad_base': 0.75
    }
}
```

### Problemas
1. **Parcelas productivas normales cumplen estos umbrales** (NDVI 0.3-0.6 es normal en etapas tempranas)
2. **Severidad base fija** (0.85) → Siempre "crítico"
3. **No hay escala relativa** (no compara con el resto del lote)

### Solución Propuesta
**Opción A: Umbrales Relativos**
```python
def _calcular_severidad_relativa(self, zona: ZonaCritica, ndvi_global: np.ndarray):
    """Severidad relativa al resto del lote"""
    ndvi_zona = zona.valores_indices['ndvi']
    ndvi_p50 = np.percentile(ndvi_global, 50)  # Mediana del lote
    ndvi_p10 = np.percentile(ndvi_global, 10)  # 10% más bajo
    
    # Calcular desviación respecto a la mediana
    if ndvi_zona >= ndvi_p50:
        severidad = 0.0  # Mejor que el promedio
    elif ndvi_zona <= ndvi_p10:
        severidad = 1.0  # 10% peor del lote
    else:
        # Escala lineal entre p10 y p50
        severidad = (ndvi_p50 - ndvi_zona) / (ndvi_p50 - ndvi_p10)
    
    return np.clip(severidad, 0.0, 1.0)
```

**Opción B: Suavizar Umbrales (Más Conservador)**
```python
UMBRALES_CRITICOS_SUAVIZADOS = {
    'deficit_hidrico_recurrente': {
        'ndvi_max': 0.30,  # ✅ MÁS REALISTA (solo casos severos)
        'ndmi_max': -0.05, # ✅ DÉFICIT REAL
        'severidad_base': 0.70  # ✅ REDUCIDA
    },
    'baja_densidad_suelo_degradado': {
        'ndvi_max': 0.25,  # ✅ MÁS ESTRICTO (verdaderos problemas)
        'savi_max': 0.25,  # ✅ COBERTURA MUY BAJA
        'severidad_base': 0.60
    }
}
```

---

## 🔴 PROBLEMA #4: Falta de Recorte por Máscara del Polígono

### Descripción del Error
El análisis de OpenCV (`findContours`) opera sobre el raster completo, sin recortar por la geometría real del lote:

```python
# CÓDIGO ACTUAL (INCORRECTO)
def _encontrar_clusters(self, mascara: np.ndarray):
    """Encuentra clusters SIN recortar por polígono"""
    contours, hierarchy = cv2.findContours(
        mascara_uint8,  # ❌ Incluye áreas fuera del cultivo
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
```

### Impacto
- Detecta "zonas críticas" en áreas que NO son parte del cultivo
- Sobreestimación del área afectada
- Centroides de intervención fuera del lote

### Solución Propuesta
```python
def _encontrar_clusters(self, mascara: np.ndarray, mascara_cultivo: np.ndarray):
    """
    Args:
        mascara_cultivo: Máscara booleana del polígono real del lote
    """
    # ✅ APLICAR RECORTE ANTES DE BUSCAR CONTORNOS
    mascara_recortada = np.logical_and(mascara, mascara_cultivo)
    
    mascara_uint8 = (mascara_recortada * 255).astype(np.uint8)
    
    contours, hierarchy = cv2.findContours(
        mascara_uint8,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    # ...
```

**Propagación del cambio:**
- `_detectar_zonas_criticas()` → recibir `mascara_cultivo` como parámetro
- `triangular_y_diagnosticar()` → generar `mascara_cultivo` desde geometría de parcela
- `_ejecutar_diagnostico_cerebro()` → pasar geometría de parcela

---

## 🔴 PROBLEMA #5: Inconsistencia de Decimales

### Descripción del Error
Las hectáreas y porcentajes se presentan con diferentes precisiones a lo largo del informe:

**Inconsistencias Detectadas:**
- Tabla de severidad: `8.23 ha` (2 decimales)
- Resumen ejecutivo: `8.2 ha` (1 decimal)
- Diagnóstico detallado: `8 ha` (0 decimales)
- Porcentajes: `82.3%` vs `82%` vs `82.30%`

### Solución Propuesta
**Estandarizar en TODO el documento:**
```python
# ESTÁNDAR DE FORMATEO
FORMATO_HECTAREAS = "{:.1f}"  # Siempre 1 decimal
FORMATO_PORCENTAJE = "{:.1f}" # Siempre 1 decimal

# Usar en helpers
def formatear_hectareas(valor: float) -> str:
    """Formato estándar: X.X ha"""
    return f"{valor:.1f} ha"

def formatear_porcentaje(valor: float) -> str:
    """Formato estándar: X.X%"""
    return f"{valor:.1f}%"
```

**Aplicar en contexto de PDF:**
```python
context = {
    'area_afectada': formatear_hectareas(kpis.area_afectada_ha),  # "8.2 ha"
    'porcentaje_afectado': formatear_porcentaje(kpis.porcentaje_afectado),  # "82.3%"
    'eficiencia': formatear_porcentaje(kpis.eficiencia)  # "17.7%"
}
```

---

## 📊 MATRIZ DE IMPACTO Y PRIORIDAD

| # | Problema | Severidad | Esfuerzo | Prioridad | Archivos Afectados |
|---|----------|-----------|----------|-----------|-------------------|
| 1 | Área afectada > Total | 🔴 Alta | Alto | **P0** | `cerebro_diagnostico.py` |
| 2 | KPIs inconsistentes | 🔴 Alta | Medio | **P0** | `generador_pdf.py` |
| 3 | Umbrales irreales | 🟠 Media | Bajo | **P1** | `cerebro_diagnostico.py` |
| 4 | Sin recorte polígono | 🟠 Media | Alto | **P1** | `cerebro_diagnostico.py` |
| 5 | Decimales inconsistentes | 🟡 Baja | Bajo | **P2** | `generador_pdf.py`, helpers |

---

## 🎯 PLAN DE CORRECCIÓN

### Fase 1: Correcciones Críticas (P0)
1. **Implementar KPIsUnificados** (1 hora)
   - Crear dataclass con validaciones
   - Refactorizar generador_pdf.py para usar única fuente
   - Validar coherencia matemática

2. **Corregir cálculo de área afectada** (2 horas)
   - Agregar parámetro `mascara_cultivo` a funciones clave
   - Implementar recorte preventivo antes de unión de máscaras
   - Validar con casos de prueba

### Fase 2: Correcciones Importantes (P1)
3. **Ajustar umbrales de severidad** (1 hora)
   - Implementar severidad relativa O suavizar umbrales fijos
   - Validar con datos históricos reales
   - Documentar criterios científicos

4. **Implementar recorte por polígono** (3 horas)
   - Generar mascara_cultivo desde geometría de parcela
   - Propagar cambio a todas las funciones de análisis
   - Validar con parcelas de geometría compleja

### Fase 3: Pulido (P2)
5. **Estandarizar formato de decimales** (30 min)
   - Crear helpers de formateo
   - Reemplazar todos los f-strings en generador_pdf.py
   - Validar visualmente en PDF generado

---

## ✅ CRITERIOS DE ACEPTACIÓN

### Tests de Validación
```python
def test_area_afectada_nunca_supera_total():
    """Test crítico: Área afectada <= Área total SIEMPRE"""
    diagnostico = ejecutar_diagnostico_unificado(...)
    assert diagnostico.area_afectada_total <= area_parcela_ha

def test_kpis_coherentes():
    """Test: Eficiencia = 100 - Porcentaje Afectado"""
    kpis = KPIsUnificados(...)
    assert abs(kpis.eficiencia - (100 - kpis.porcentaje_afectado)) < 0.01

def test_desglose_suma_al_total():
    """Test: Crítica + Moderada + Leve = Total Afectado"""
    desglose_total = (kpis.area_critica_ha + 
                     kpis.area_moderada_ha + 
                     kpis.area_leve_ha)
    assert abs(desglose_total - kpis.area_afectada_ha) < 0.01

def test_formato_consistente():
    """Test: Todos los decimales en 1 dígito"""
    pdf_text = extraer_texto_pdf(ruta_pdf)
    # Verificar que NO hay formatos tipo "8.23 ha" o "82.30%"
    assert not re.search(r'\d+\.\d{2,} ha', pdf_text)
```

### Validación Visual
- [ ] Resumen Ejecutivo: Eficiencia coherente con área afectada
- [ ] Tabla de Severidad: Desglose suma al total, formato 1 decimal
- [ ] Diagnóstico Detallado: Porcentajes coherentes con secciones previas
- [ ] Todas las hectáreas: Formato X.X ha
- [ ] Todos los porcentajes: Formato X.X%

---

## 📚 REFERENCIAS TÉCNICAS

### Documentación Relacionada
- `CORRECCIONES_APLICADAS.md` - Correcciones matemáticas previas
- `ESTADO_FINAL_SISTEMA.md` - Estado documentado del sistema
- `docs/sistema/FLUJO_IMAGENES_SATELITALES.md` - Flujo de datos

### Archivos Clave
- `/informes/motor_analisis/cerebro_diagnostico.py` - Motor de diagnóstico
- `/informes/generador_pdf.py` - Generación de PDF
- `/informes/helpers/diagnostico_pdf_helper.py` - Helpers de formateo

### Herramientas de Validación
- `test_correccion_matematica_parcela2.py` - Script de prueba
- `verificar_pdf_generado.py` - Validación de PDFs

---

## 🚀 PRÓXIMOS PASOS

1. ✅ Revisar y aprobar esta auditoría
2. 🔄 Implementar correcciones en orden de prioridad (P0 → P1 → P2)
3. 🧪 Ejecutar tests de validación
4. 📄 Generar PDF de prueba con Parcela #2
5. 👁️ Validación visual del informe final
6. 📝 Documentar cambios en `CORRECCIONES_FINALES.md`

---

**Última actualización:** Enero 2026  
**Estado:** ⚠️ PENDIENTE DE APROBACIÓN  
**Responsable:** Equipo AgroTech Engineering
