# ⚠️ HALLAZGO CRÍTICO: Filtrado de Nubosidad en Imágenes Satelitales

**Fecha:** 2025-01-21  
**Estado:** 🔴 Requiere Atención  
**Prioridad:** Alta  
**Documentación Completa:** [docs/sistema/FILTRADO_NUBOSIDAD_EOSDA.md](docs/sistema/FILTRADO_NUBOSIDAD_EOSDA.md)

---

## 🎯 Problema Identificado

El sistema AgroTech Histórico actualmente acepta imágenes satelitales con **hasta 80% de nubosidad**, lo cual es **4 veces más permisivo** que lo documentado internamente (20%) y **infinitamente más permisivo** que la recomendación oficial de EOSDA (0% por defecto).

### Ubicación del Código

**Archivo:** `historical/informes/services/eosda_api.py`

```python
# Línea ~450 - obtener_imagenes_indice()
params = {
    'max_cloud_cover_in_aoi': 80,  # ❌ MUY PERMISIVO
    # ...
}
```

### Impacto Real

Una imagen con **80% de nubosidad** significa que:
- ❌ Solo el **20% de la parcela es visible**
- ❌ Los cálculos de NDVI/NDMI/SAVI son **poco confiables**
- ❌ Gemini AI analiza nubes en vez de cultivos
- ❌ Las recomendaciones pueden ser **erróneas**

**Ejemplo:**
```
Parcela de 10 hectáreas con imagen al 75% de nubosidad
→ Solo 2.5 hectáreas son analizables
→ El 75% restante son nubes o sombras
→ Análisis basado en 1/4 de la parcela ❌
```

---

## 📚 ¿Qué Dice la Documentación Oficial EOSDA?

### Statistics API (Recomendación Principal)

**Fuente:** https://doc.eos.com/docs/statistics/

| Parámetro | Valor por Defecto | Descripción |
|-----------|-------------------|-------------|
| `max_cloud_cover_in_aoi` | **0%** | Filtrar escenas por umbral superior de nubosidad |
| `exclude_cover_pixels` | `true` | Enmascarar píxeles nublados en cálculo de estadísticas |
| `cloud_masking_level` | Nivel 2 (recomendado) | Enmascaramiento avanzado S2 (nubes media + alta probabilidad) |

**Conclusión oficial de EOSDA:**
> "The best results are achieved when combining both SCL and GML cloud masks during statistics calculation."

Traducción: **NO aceptar imágenes nubladas sin enmascarar**.

---

## ✅ Solución Propuesta: Sistema de Umbrales Escalonados

En lugar de un umbral único rígido, implementar **tres niveles de calidad** con advertencias transparentes:

```python
UMBRAL_CONFIABLE = 20    # ✅ Alta calidad (análisis precisos)
UMBRAL_ACEPTABLE = 50    # ⚠️ Calidad media (advertir al usuario)
UMBRAL_MAXIMO = 80       # 🚫 Baja calidad (advertencia fuerte)
```

### Lógica de Selección

1. **Priorizar imágenes confiables (≤ 20%):** Sin advertencias
2. **Si no hay, buscar aceptables (21-50%):** Advertencia ⚠️
3. **Si no hay, buscar cualquiera (51-80%):** Advertencia fuerte 🚫
4. **Si no hay ninguna (> 80%):** Explicar claramente por qué no hay datos

### Ventajas

✅ **Maximiza disponibilidad de datos** (no deja meses vacíos sin razón)  
✅ **Transparencia total** (el usuario sabe la calidad de lo que ve)  
✅ **Cumple mejores prácticas** (alineado con EOSDA)  
✅ **Flexible** (permite análisis científicos estrictos o monitoreo general)

---

## 🧪 Cómo Probar el Sistema Actual

Ejecutar el script de prueba comparativa:

```bash
# Comparar umbrales 20%, 50% y 80% en una parcela específica
python tests/test_umbrales_nubosidad.py --parcela-id 1 --mes 2025-01

# Probar un umbral específico
python tests/test_umbrales_nubosidad.py --parcela-id 1 --mes 2025-01 --umbral 20
```

**Salida esperada:**

```
================================================================================
RESUMEN COMPARATIVO
================================================================================

Umbral     Imágenes     Nubosidad Prom.    Calidad                  
--------------------------------------------------------------------------------
20%        0            N/A                N/A
50%        2            35.5%              ⚠️ ACEPTABLE
80%        5            62.3%              🚫 BAJA CALIDAD

================================================================================
ANÁLISIS Y RECOMENDACIONES
================================================================================

⚠️ RECOMENDACIÓN: Usar umbral de 50% (ACEPTABLE)
   Se encontraron 2 imágenes de calidad media.
   ADVERTIR al usuario sobre la nubosidad moderada.
```

---

## 📖 Documentación Relacionada

### Documentación Completa del Hallazgo
- **[FILTRADO_NUBOSIDAD_EOSDA.md](docs/sistema/FILTRADO_NUBOSIDAD_EOSDA.md)** ← **LEER PRIMERO**
  - Análisis detallado del código actual
  - Comparación con documentación oficial EOSDA
  - Plan de implementación paso a paso
  - Código propuesto completo

### Referencias EOSDA
- [Statistics API](https://doc.eos.com/docs/statistics/) - Parámetro `max_cloud_cover_in_aoi`
- [Search API](https://doc.eos.com/docs/search/simple-search/) - Parámetro `cloudCoverage`
- [Cloud Masking Options](https://doc.eos.com/docs/statistics/#cloud-masking-options) - Enmascaramiento avanzado

### Documentación Interna
- [CONEXION_EOSDA_GUIA_COMPLETA.md](CONEXION_EOSDA_GUIA_COMPLETA.md) - Guía de integración EOSDA
- [FLUJO_IMAGENES_SATELITALES.md](docs/sistema/FLUJO_IMAGENES_SATELITALES.md) - Flujo de datos satelitales

---

## 🛠️ Plan de Implementación (Estimado: 1 jornada)

- [ ] **Fase 1:** Actualizar `eosda_api.py` (1-2 horas)
- [ ] **Fase 2:** Agregar campos de calidad a modelo `IndiceMensual` (30 min)
- [ ] **Fase 3:** Actualizar `generador_pdf.py` con indicadores de calidad (1 hora)
- [ ] **Fase 4:** Testing exhaustivo (2 horas)
- [ ] **Fase 5:** Actualizar documentación (1 hora)

**Responsable:** Por asignar  
**Fecha objetivo:** Por definir  
**Bloqueantes:** Ninguno (mejora independiente)

---

## ❓ FAQ Rápido

### ¿Por qué 80% es demasiado permisivo?

Porque **solo el 20% de la imagen es útil**. Es como intentar diagnosticar a un paciente viendo solo su brazo izquierdo.

### ¿Por qué no usar 20% siempre?

Porque en regiones tropicales o invierno puede **no haber imágenes con ≤20% nubosidad** en meses enteros. El sistema escalonado evita meses vacíos.

### ¿Esto afecta los informes actuales?

**Sí**. Algunos informes pueden estar basados en imágenes con 60-70% de nubosidad sin que el usuario lo sepa. La solución propuesta **aumenta la transparencia**.

### ¿Qué pasa si implementamos esto?

1. ✅ Usuarios verán advertencias claras cuando una imagen sea poco confiable
2. ✅ Informes tendrán menos meses vacíos (usa 50% en vez de 20% cuando sea necesario)
3. ✅ Análisis científicos podrán filtrar solo imágenes "confiables"
4. ✅ Cumplimiento con mejores prácticas de EOSDA

---

## 📞 Contacto

**Preguntas o dudas sobre este hallazgo:**  
- Revisar documentación completa: `docs/sistema/FILTRADO_NUBOSIDAD_EOSDA.md`
- Ejecutar test comparativo: `python tests/test_umbrales_nubosidad.py --help`
- Consultar código fuente: `historical/informes/services/eosda_api.py` (líneas 240 y 450)

---

**Este hallazgo ha sido documentado completamente y está listo para revisión e implementación.**  
**Estado:** 🟡 Pendiente de Aprobación  
**Última actualización:** 2025-01-21
