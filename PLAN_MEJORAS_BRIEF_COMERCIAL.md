# Plan de Mejoras PDF Legal - Brief Comercial
**Fecha:** 2025-01-XX
**Objetivo:** Optimizar informe PDF legal para venta a entidades de crédito agrícola

## 🎯 Requisitos del Brief Comercial

### 1. MAPAS (3 versiones requeridas)

#### Mapa 1: Contexto Regional
- ✅ **Qué es:** Vista amplia (departamento/región) con punto marcando ubicación de la parcela
- ✅ **Para qué:** Ubicación geográfica general para evaluación de riesgo
- ✅ **Implementar:** Nueva función `_generar_mapa_contexto_regional()`

#### Mapa 2: Mapa Técnico Principal
- ✅ **Flechas direccionales:** Desde límite más cercano del polígono (NO centroide) hacia elemento relevante
- ✅ **Texto visible:** Distancia en km/m y dirección cardinal (ej: "0.62 km NE")
- ✅ **Red hídrica obligatoria:** Mostrar SIEMPRE, aunque no intersecte (con buffer de 30m legal)
- ✅ **Escala gráfica:** Barra de escala en metros/kilómetros
- ✅ **Fuente de datos:** Pie de mapa "Fuente: IGAC, IDEAM, PNN - 2024"
- ✅ **Fecha de análisis:** Timestamp del análisis
- ✅ **Implementar:** Refactorizar `_generar_mapa_parcela()` completamente

#### Mapa 3: Mapa Limpio/Silueta
- ✅ **Qué es:** Polígono de la parcela sin capas, solo contexto limpio (imagen satelital o topográfico)
- ✅ **Para qué:** Visualización rápida del área total y forma
- ✅ **Implementar:** Nueva función `_generar_mapa_silueta()`

### 2. COPY Y LENGUAJE

#### Correcciones Terminológicas
- ❌ "Cumple normativa" → ✅ "Sin restricciones identificadas en análisis geoespacial"
- ❌ "Área cultivable" → ✅ "Área técnicamente disponible (sujeto a verificación de campo)"
- ❌ "Verificación legal definitiva" → ✅ "Análisis geoespacial preliminar"
- ✅ **Implementar:** Buscar y reemplazar en todo el código

#### Niveles de Confianza (Ajustados)
- **Red hídrica:** MEDIA–ALTA (si shapefile correcto) o BAJA (si sin cobertura)
- **Nota obligatoria:** "Escala 1:100.000 - Requiere validación en campo"
- ✅ **Implementar:** Ajustar en `_crear_seccion_confianza()`

### 3. METADATOS POR CAPA

#### Bloque de Información (Tabla)
Para cada capa geográfica incluir:
- **Nombre completo:** Red Hídrica Superficial de Colombia
- **Autoridad:** IGAC / IDEAM
- **Año de publicación:** 2024
- **Tipo de geometría:** LineString / Polygon
- **Escala / Limitación:** 1:100.000 / "Requiere complemento con levantamiento de campo"

✅ **Implementar:** Nueva función `_crear_tabla_metadatos_capas()`

### 4. ORDEN PSICOLÓGICO DE VENTA

#### Estructura Actual (Técnica)
1. Portada
2. Proximidad a zonas
3. Mapa técnico
4. Restricciones
5. Confianza
6. Advertencias
7. Recomendaciones

#### Nueva Estructura (Comercial) ✅
1. **Portada** (con resultado destacado)
2. **Conclusión ejecutiva** (1 párrafo, resultado + implicación comercial)
3. **Mapa limpio/silueta** (impacto visual)
4. **Mapa de contexto regional** (ubicación general)
5. **Mapa técnico principal** (análisis detallado con flechas)
6. **Análisis por capa** (metadatos + restricciones)
7. **Niveles de confianza** (transparencia técnica)
8. **Recomendaciones** (siguientes pasos)
9. **Limitaciones técnicas** (disclaimer legal final)

✅ **Implementar:** Refactorizar `generar()` para nuevo orden

### 5. DISCLAIMER LEGAL REFORZADO

#### Texto Obligatorio (Cada Página)
Pie de página en TODAS las páginas:
```
DISCLAIMER: Este análisis geoespacial es preliminar y se basa en cartografía oficial disponible. 
NO constituye concepto legal definitivo ni reemplaza verificación en campo por autoridad competente. 
Uso exclusivo para evaluación crediticia preliminar.
```

✅ **Implementar:** Agregar en `_header_footer()` (footer en cada página)

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Funciones de Mapas (PRIORIDAD 1)
- [ ] `_generar_mapa_contexto_regional()` - Mapa 1
- [ ] `_refactorizar_mapa_tecnico()` - Mapa 2 (flechas desde límite, escala, fuente)
- [ ] `_generar_mapa_silueta()` - Mapa 3

### Fase 2: Metadatos y Confianza (PRIORIDAD 2)
- [ ] `_crear_tabla_metadatos_capas()` - Bloque de metadatos por capa
- [ ] Ajustar niveles de confianza (red hídrica: MEDIA-ALTA con nota)
- [ ] Agregar nota de escala en cada mapa

### Fase 3: Copy y Lenguaje (PRIORIDAD 3)
- [ ] Buscar/reemplazar terminología (cumple → sin restricciones, etc.)
- [ ] Ajustar textos de portada y conclusiones
- [ ] Reforzar advertencias de limitaciones

### Fase 4: Reordenamiento (PRIORIDAD 4)
- [ ] Refactorizar método `generar()` con nuevo orden
- [ ] Agregar "Conclusión Ejecutiva" después de portada
- [ ] Mover "Limitaciones Técnicas" al final

### Fase 5: Disclaimer Legal (PRIORIDAD 5)
- [ ] Agregar footer legal en cada página
- [ ] Validar que aparezca en todas las páginas del PDF

---

## 🚀 PRÓXIMOS PASOS

1. **Backup del código actual**
   ```bash
   cp generador_pdf_legal.py generador_pdf_legal_BACKUP_$(date +%Y%m%d_%H%M%S).py
   ```

2. **Implementar Fase 1** (mapas) - 60% del impacto comercial

3. **Implementar Fase 2** (metadatos) - 20% del impacto

4. **Implementar Fases 3-5** (copy + orden + disclaimer) - 20% del impacto

5. **Testing exhaustivo**
   ```bash
   python generar_pdf_verificacion_casanare.py
   ```

6. **Validación visual y comercial** (¿convence a un oficial de crédito?)

7. **Commit y push** con documentación completa

---

## ⚠️ ADVERTENCIAS CRÍTICAS

- ❌ **NO tocar la lógica de `verificador_legal.py`** (ya está corregida)
- ❌ **NO inventar datos** (solo reorganizar presentación)
- ✅ **SÍ mejorar visualización** (flechas, escalas, mapas)
- ✅ **SÍ ajustar copy** (lenguaje técnico-legal correcto)
- ✅ **SÍ reforzar disclaimers** (protección legal)

---

**Estado:** PLANIFICACIÓN COMPLETA
**Listo para:** IMPLEMENTACIÓN
