# 🚀 GUÍA RÁPIDA DE INTEGRACIÓN - KPIs Unificados

**Para:** Desarrolladores que integrarán las correcciones en `generador_pdf.py`  
**Tiempo estimado:** 30-45 minutos  
**Dificultad:** Media

---

## 📋 RESUMEN

Integrar el nuevo sistema de KPIs unificados en el generador de PDF para garantizar coherencia matemática en todos los informes.

### Antes (Código Antiguo ❌)
```python
# Múltiples cálculos ad-hoc dispersos en el código
eficiencia = (area_sana / area_total) * 100  # Sección 1
porcentaje = (area_afectada / area_total) * 100  # Sección 2
# ... más cálculos duplicados ...
```

### Después (Código Nuevo ✅)
```python
# Una sola fuente de verdad
from informes.motor_analisis.kpis_unificados import KPIsUnificados

kpis = KPIsUnificados.desde_diagnostico(diagnostico, area_total_ha)
kpis.validar_coherencia()  # Garantiza que todo sea matemáticamente correcto

# Usar en TODAS las secciones
context = {
    'eficiencia': kpis.formatear_eficiencia(),  # "45.0%"
    'area_afectada': kpis.formatear_area_afectada(),  # "5.5 ha"
    # ... todos los valores ya formateados
}
```

---

## 🔧 PASO 1: Modificar `_ejecutar_diagnostico_cerebro()`

**Ubicación:** `informes/generador_pdf.py`, línea ~1950

### Cambio 1.1: Agregar imports
```python
# Al inicio del archivo (después de imports existentes)
from informes.motor_analisis.kpis_unificados import KPIsUnificados
from informes.motor_analisis.mascara_cultivo import obtener_mascara_cultivo_para_diagnostico
```

### Cambio 1.2: Generar máscara de cultivo
```python
def _ejecutar_diagnostico_cerebro(self, parcela: Parcela, indices: List[IndiceMensual]) -> Optional[Dict]:
    # ... código existente ...
    
    # ✅ AGREGAR DESPUÉS de crear geo_transform (línea ~2050)
    
    # Generar máscara de cultivo desde geometría de parcela
    mascara_cultivo = obtener_mascara_cultivo_para_diagnostico(
        parcela=parcela,
        geo_transform=geo_transform,
        shape=size  # (256, 256)
    )
    
    if mascara_cultivo is None:
        logger.warning("⚠️  No se pudo generar máscara de cultivo, usando análisis sin recorte")
    
    # ... continúa código existente ...
```

### Cambio 1.3: Pasar máscara al diagnóstico
```python
    # MODIFICAR llamada a ejecutar_diagnostico_unificado (línea ~2057)
    # ANTES:
    diagnostico_obj = ejecutar_diagnostico_unificado(
        datos_indices=arrays_indices,
        geo_transform=geo_transform,
        area_parcela_ha=parcela.area_hectareas or 10.0,
        output_dir=str(output_dir),
        tipo_informe='produccion',
        resolucion_m=10.0
    )
    
    # DESPUÉS:
    diagnostico_obj = ejecutar_diagnostico_unificado(
        datos_indices=arrays_indices,
        geo_transform=geo_transform,
        area_parcela_ha=parcela.area_hectareas or 10.0,
        output_dir=str(output_dir),
        tipo_informe='produccion',
        resolucion_m=10.0,
        mascara_cultivo=mascara_cultivo  # ✅ NUEVO parámetro
    )
```

### Cambio 1.4: Crear KPIs unificados
```python
    # ✅ AGREGAR DESPUÉS de verificar diagnostico_obj (línea ~2070)
    
    # Crear KPIs unificados y validar coherencia
    try:
        kpis = KPIsUnificados.desde_diagnostico(
            diagnostico=diagnostico_obj,
            area_total_ha=parcela.area_hectareas or 10.0
        )
        kpis.validar_coherencia(tolerancia=0.2)
        logger.info(f"✅ KPIs validados: {kpis.eficiencia:.1f}% eficiencia, {kpis.area_afectada_ha:.1f} ha afectadas")
    except AssertionError as e:
        logger.error(f"❌ Error de coherencia en KPIs: {str(e)}")
        # Continuar pero alertar
        kpis = None
    
    # Convertir objeto DiagnosticoUnificado a dict para uso en PDF
    resultado = {
        'eficiencia_lote': diagnostico_obj.eficiencia_lote,
        'area_afectada_total': diagnostico_obj.area_afectada_total,
        'mapa_diagnostico_path': diagnostico_obj.mapa_diagnostico_path,
        'resumen_ejecutivo': diagnostico_obj.resumen_ejecutivo,
        'diagnostico_detallado': diagnostico_obj.diagnostico_detallado,
        'desglose_severidad': diagnostico_obj.desglose_severidad,
        'zona_prioritaria': None,
        'kpis': kpis  # ✅ AGREGAR KPIs al resultado
    }
```

---

## 🔧 PASO 2: Modificar `_crear_resumen_ejecutivo()`

**Ubicación:** `informes/generador_pdf.py`, línea ~920

### Cambio 2.1: Usar KPIs en lugar de cálculos ad-hoc
```python
def _crear_resumen_ejecutivo(self, analisis: Dict, parcela: Parcela, datos: List[Dict], diagnostico_unificado: Optional[Dict] = None) -> List:
    # ... código existente ...
    
    if diagnostico_unificado:
        # ✅ USAR KPIs UNIFICADOS si están disponibles
        if 'kpis' in diagnostico_unificado and diagnostico_unificado['kpis']:
            kpis = diagnostico_unificado['kpis']
            eficiencia = kpis.eficiencia
            area_afectada = kpis.area_afectada_ha
            area_total = kpis.area_total_ha
            
            # Texto formateado consistente
            eficiencia_fmt = kpis.formatear_eficiencia()  # "45.0%"
            area_afectada_fmt = kpis.formatear_area_afectada()  # "5.5 ha"
        else:
            # Fallback al método antiguo
            eficiencia = diagnostico_unificado.get('eficiencia_lote', 0)
            area_afectada = diagnostico_unificado.get('area_afectada_total', 0)
            area_total = parcela.area_hectareas
            eficiencia_fmt = f"{eficiencia:.1f}%"
            area_afectada_fmt = f"{area_afectada:.1f} ha"
        
        # ... resto del código usando eficiencia_fmt y area_afectada_fmt ...
```

---

## 🔧 PASO 3: Modificar `_crear_seccion_guia_intervencion()`

**Ubicación:** `informes/generador_pdf.py`, línea ~2100

### Cambio 3.1: Usar KPIs en lugar de cálculos
```python
def _crear_seccion_guia_intervencion(self, diagnostico: Dict, parcela: Parcela) -> List:
    # ... código existente ...
    
    # ✅ USAR KPIs UNIFICADOS
    if 'kpis' in diagnostico and diagnostico['kpis']:
        kpis = diagnostico['kpis']
        eficiencia = kpis.eficiencia
        area_afectada = kpis.area_afectada_ha
        area_total = kpis.area_total_ha
        porcentaje_afectado = kpis.porcentaje_afectado
        
        # Texto formateado
        eficiencia_fmt = kpis.formatear_eficiencia()
        area_afectada_fmt = kpis.formatear_area_afectada()
        porcentaje_fmt = kpis.formatear_porcentaje_afectado()
    else:
        # Fallback
        eficiencia = diagnostico.get('eficiencia_lote', 0)
        area_afectada = diagnostico.get('area_afectada_total', 0)
        area_total = parcela.area_hectareas
        porcentaje_afectado = (area_afectada / area_total * 100) if area_total > 0 else 0
        
        eficiencia_fmt = f"{eficiencia:.1f}%"
        area_afectada_fmt = f"{area_afectada:.1f} ha"
        porcentaje_fmt = f"{porcentaje_afectado:.1f}%"
    
    # Resumen ejecutivo del diagnóstico
    resumen_texto = Paragraph(
        f'<b>Resumen del Análisis:</b> De las {area_total:.1f} hectáreas evaluadas, '
        f'se detectaron {area_afectada_fmt} ({porcentaje_fmt}) '  # ✅ Usar formato consistente
        f'con oportunidades de mejora. La eficiencia productiva actual del lote es del '
        f'<b>{eficiencia_fmt}</b>. ...',
        estilo_resumen
    )
```

---

## 🔧 PASO 4: Actualizar Tablas de Severidad

**Ubicación:** Donde sea que se generen tablas con desglose de áreas

### Cambio 4.1: Usar KPIs para tabla
```python
# Si generas tabla de severidad en alguna sección
if 'kpis' in diagnostico and diagnostico['kpis']:
    kpis = diagnostico['kpis']
    
    data_tabla = [
        ['Nivel', 'Área', 'Porcentaje', 'Zonas'],
        [
            '🔴 Crítica',
            kpis.formatear_area_critica(),      # "3.5 ha"
            kpis.formatear_porcentaje_critico(),  # "35.0%"
            str(kpis.num_zonas_criticas)
        ],
        [
            '🟠 Moderada',
            kpis.formatear_area_moderada(),
            kpis.formatear_porcentaje_moderado(),
            str(kpis.num_zonas_moderadas)
        ],
        [
            '🟡 Leve',
            kpis.formatear_area_leve(),
            kpis.formatear_porcentaje_leve(),
            str(kpis.num_zonas_leves)
        ],
        [
            '<b>TOTAL</b>',
            kpis.formatear_area_afectada(),     # Suma exacta
            kpis.formatear_porcentaje_afectado(),
            str(kpis.num_zonas_totales)
        ]
    ]
```

---

## 🧪 PASO 5: Validar Integración

### 5.1: Ejecutar tests
```bash
cd "/Users/sebasflorez16/Documents/AgroTech Historico"
python test_validacion_completa_correcciones.py
```

**Salida esperada:**
```
🎯 Tasa de éxito: 100.0%
🎉 ¡TODOS LOS TESTS PASARON! Sistema validado correctamente.
```

### 5.2: Generar PDF de prueba
```bash
python manage.py runserver
# Ir a http://localhost:8000/informes/generar/2/
```

### 5.3: Validar visualmente el PDF

**Checklist de verificación:**
- [ ] Resumen Ejecutivo: `Eficiencia: X.X%` (1 decimal)
- [ ] Resumen Ejecutivo: `X.X hectáreas` (1 decimal)
- [ ] Tabla de Severidad: Áreas con formato `X.X ha`
- [ ] Tabla de Severidad: Total suma exactamente
- [ ] Diagnóstico Detallado: Porcentajes coinciden con resumen
- [ ] No hay valores con 2 decimales (`8.23 ha` ❌)
- [ ] Eficiencia + Porcentaje Afectado = 100%

---

## 🔍 BÚSQUEDA Y REEMPLAZO GLOBAL

Para asegurar consistencia en TODO el archivo, buscar y reemplazar:

### Patrón 1: Formateo de hectáreas
```python
# BUSCAR (regex):
f"{\w+:.2f} ha"

# REEMPLAZAR POR:
kpis.formatear_area_XXX()  # Usar método apropiado
```

### Patrón 2: Formateo de porcentajes
```python
# BUSCAR (regex):
f"{\w+:.2f}%"

# REEMPLAZAR POR:
kpis.formatear_porcentaje_XXX()  # Usar método apropiado
```

### Patrón 3: Cálculos de eficiencia
```python
# BUSCAR:
eficiencia = (area_sana / area_total) * 100

# REEMPLAZAR POR:
eficiencia = kpis.eficiencia  # Ya calculado y validado
```

### Patrón 4: Cálculos de porcentaje afectado
```python
# BUSCAR:
porcentaje_afectado = (area_afectada / area_total) * 100

# REEMPLAZAR POR:
porcentaje_afectado = kpis.porcentaje_afectado  # Ya calculado
```

---

## 📝 EJEMPLO COMPLETO DE INTEGRACIÓN

```python
# ============================================
# EJEMPLO: Sección de Resumen con KPIs
# ============================================

def _crear_resumen_ejecutivo_nuevo(self, diagnostico_unificado: Dict, parcela: Parcela):
    """Ejemplo completo de uso de KPIs unificados"""
    elements = []
    
    # 1. Extraer KPIs
    kpis = diagnostico_unificado.get('kpis')
    if not kpis:
        logger.error("KPIs no disponibles, usando valores por defecto")
        return elements
    
    # 2. Validar coherencia (opcional, ya se validó en _ejecutar_diagnostico_cerebro)
    try:
        kpis.validar_coherencia()
    except AssertionError as e:
        logger.error(f"⚠️  Advertencia: {str(e)}")
    
    # 3. Obtener valores formateados
    estado = kpis.obtener_estado_lote()  # 'EXCELENTE' | 'BUENO' | 'REQUIERE ATENCIÓN' | 'CRÍTICO'
    color = kpis.obtener_color_estado()  # Código hex del color
    
    # 4. Crear banner profesional
    banner_texto = Paragraph(
        f'<para alignment="center" backColor="{color}">'
        f'<font size="14" color="white"><b>ESTADO DEL CULTIVO: {estado}</b></font><br/>'
        f'<font size="11" color="white">Eficiencia Productiva: {kpis.formatear_eficiencia()}</font>'
        f'</para>',
        self.estilos['TituloSeccion']
    )
    elements.append(banner_texto)
    
    # 5. Tabla de resumen
    data_resumen = [
        ['Métrica', 'Valor'],
        ['Área Total', kpis.formatear_area_total()],
        ['Área Afectada', kpis.formatear_area_afectada()],
        ['Área Sana', kpis.formatear_area_sana()],
        ['Porcentaje Afectado', kpis.formatear_porcentaje_afectado()],
        ['Eficiencia', kpis.formatear_eficiencia()]
    ]
    
    tabla = Table(data_resumen, colWidths=[8*cm, 6*cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(tabla)
    
    # 6. Desglose por severidad (si hay zonas afectadas)
    if kpis.area_afectada_ha > 0:
        elements.append(Spacer(1, 0.5*cm))
        
        desglose_titulo = Paragraph(
            '<b>Desglose por Nivel de Severidad</b>',
            self.estilos['TextoNormal']
        )
        elements.append(desglose_titulo)
        
        data_desglose = [
            ['Nivel', 'Área', '% del Total', '% del Afectado', 'Zonas'],
            [
                '🔴 Crítica',
                kpis.formatear_area_critica(),
                kpis.formatear_porcentaje_critico(),
                f"{(kpis.area_critica_ha / kpis.area_afectada_ha * 100):.1f}%",
                str(kpis.num_zonas_criticas)
            ],
            [
                '🟠 Moderada',
                kpis.formatear_area_moderada(),
                kpis.formatear_porcentaje_moderado(),
                f"{(kpis.area_moderada_ha / kpis.area_afectada_ha * 100):.1f}%",
                str(kpis.num_zonas_moderadas)
            ],
            [
                '🟡 Leve',
                kpis.formatear_area_leve(),
                kpis.formatear_porcentaje_leve(),
                f"{(kpis.area_leve_ha / kpis.area_afectada_ha * 100):.1f}%",
                str(kpis.num_zonas_leves)
            ]
        ]
        
        tabla_desglose = Table(data_desglose)
        # ... aplicar estilos ...
        elements.append(tabla_desglose)
    
    return elements
```

---

## ⚠️ ERRORES COMUNES A EVITAR

### Error 1: No validar KPIs antes de usar
```python
# ❌ INCORRECTO (puede lanzar excepción)
kpis = KPIsUnificados.desde_diagnostico(diagnostico, area_total)
eficiencia = kpis.eficiencia  # Puede fallar si hay error matemático

# ✅ CORRECTO
try:
    kpis = KPIsUnificados.desde_diagnostico(diagnostico, area_total)
    kpis.validar_coherencia()
    eficiencia = kpis.eficiencia
except AssertionError as e:
    logger.error(f"Error en KPIs: {str(e)}")
    # Usar valores por defecto o abortar
```

### Error 2: Mezclar formatos antiguos y nuevos
```python
# ❌ INCORRECTO (formato inconsistente)
area_1 = f"{kpis.area_afectada_ha:.2f} ha"  # 8.23 ha
area_2 = kpis.formatear_area_afectada()     # 8.2 ha

# ✅ CORRECTO (siempre usar métodos de formateo)
area_1 = kpis.formatear_area_afectada()  # 8.2 ha
area_2 = kpis.formatear_area_total()     # 10.0 ha
```

### Error 3: No pasar máscara de cultivo
```python
# ❌ INCORRECTO (puede sobreestimar áreas)
diagnostico = ejecutar_diagnostico_unificado(
    datos_indices=indices,
    geo_transform=geo_transform,
    area_parcela_ha=area
    # ... falta mascara_cultivo
)

# ✅ CORRECTO
mascara = obtener_mascara_cultivo_para_diagnostico(parcela, geo_transform, shape)
diagnostico = ejecutar_diagnostico_unificado(
    datos_indices=indices,
    geo_transform=geo_transform,
    area_parcela_ha=area,
    mascara_cultivo=mascara  # ✅
)
```

---

## 📚 REFERENCIAS RÁPIDAS

### Métodos de KPIsUnificados
```python
# Valores numéricos
kpis.area_total_ha: float
kpis.area_afectada_ha: float
kpis.porcentaje_afectado: float  # 0.0 a 100.0
kpis.eficiencia: float  # 0.0 a 100.0
kpis.area_critica_ha: float
kpis.area_moderada_ha: float
kpis.area_leve_ha: float

# Métodos de formateo (retornan strings con unidades)
kpis.formatear_area_total()  # "10.0 ha"
kpis.formatear_area_afectada()  # "8.2 ha"
kpis.formatear_porcentaje_afectado()  # "82.3%"
kpis.formatear_eficiencia()  # "17.7%"
kpis.formatear_area_critica()  # "3.5 ha"
kpis.formatear_area_moderada()  # "2.3 ha"
kpis.formatear_area_leve()  # "2.4 ha"

# Métodos auxiliares
kpis.obtener_area_sana()  # float
kpis.formatear_area_sana()  # "1.8 ha"
kpis.obtener_estado_lote()  # "EXCELENTE" | "BUENO" | "REQUIERE ATENCIÓN" | "CRÍTICO"
kpis.obtener_color_estado()  # "#27AE60" | "#F39C12" | "#E67E22" | "#E74C3C"
kpis.validar_coherencia()  # Lanza AssertionError si hay error
kpis.to_dict()  # Dict con todos los valores
```

---

## ✅ CHECKLIST FINAL

Antes de hacer commit:
- [ ] Imports agregados en generador_pdf.py
- [ ] Máscara de cultivo generada y pasada a diagnóstico
- [ ] KPIs unificados creados y validados
- [ ] Resumen Ejecutivo usa KPIs (no cálculos ad-hoc)
- [ ] Sección de Diagnóstico usa KPIs
- [ ] Tablas usan métodos de formateo consistentes
- [ ] Tests ejecutados: `python test_validacion_completa_correcciones.py`
- [ ] PDF de prueba generado y validado visualmente
- [ ] Todos los valores usan 1 decimal (X.X ha, X.X%)
- [ ] No hay errores de coherencia matemática

---

**Tiempo estimado de integración:** 30-45 minutos  
**Próximo paso:** Generar PDF real y validar visualmente  
**Soporte:** Ver `CORRECCIONES_FINALES_COMPLETADAS.md` para más detalles
