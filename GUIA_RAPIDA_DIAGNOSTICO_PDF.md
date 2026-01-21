# Cerebro de Diagnóstico - Guía Rápida de Integración PDF
## ✅ COMPLETADO - Enero 2026

---

## 🎯 ¿Qué hace?

Agrega al PDF de AgroTech:
- **Mapa consolidado** de zonas críticas (Rojo/Naranja/Amarillo)
- **Tabla profesional** con desglose de áreas
- **Zona prioritaria** con coordenadas GPS
- **Narrativas comerciales** adaptadas

---

## 🚀 Uso Rápido

```python
from informes.services.generador_pdf import generador_pdf
from informes.models import Parcela

# Generar PDF (diagnóstico incluido automáticamente)
parcela = Parcela.objects.get(eosda_field_id='abc123')
resultado = generador_pdf.generar_informe_completo(
    parcela=parcela,
    periodo_meses=12,
    tipo_informe='produccion'
)

print(f"PDF: {resultado['archivo_pdf']}")
print(f"Eficiencia: {resultado['diagnostico_unificado']['eficiencia_lote']}%")
```

---

## 🧪 Testing

```bash
# Test completo de PDF con diagnóstico
python test_pdf_diagnostico_final.py

# Test solo del motor de diagnóstico
python test_cerebro_diagnostico.py
```

---

## 📋 Requisitos

1. **Parcela sincronizada con EOSDA** (`eosda_field_id != null`)
2. **Índices recientes** (al menos 1 mes de datos)
3. **API Key EOSDA** configurada en `.env`

---

## 🗺️ Output en el PDF

### Página: "DIAGNÓSTICO UNIFICADO - ZONAS CRÍTICAS"

1. **Tabla de Desglose:**
   ```
   Crítica (Roja):    12.5 ha  (25.0%)
   Moderada (Naranja): 3.2 ha   (6.4%)
   Leve (Amarilla):    1.1 ha   (2.2%)
   Sin Problemas:     33.2 ha  (66.4%)
   ```

2. **Mapa Consolidado:**
   - Zonas coloreadas por severidad
   - Centroides marcados
   - Leyenda profesional

3. **Zona Prioritaria:**
   ```
   Diagnóstico: Déficit Hídrico Severo
   Área: 2.30 ha
   Coordenadas: 4.567890, -74.123456
   Severidad: 85%
   NDVI: 0.25 | NDMI: 0.18 | SAVI: 0.22
   ```

---

## ⚙️ Clasificación de Severidad

| Color | Severidad | Acción |
|-------|-----------|--------|
| 🔴 Rojo | > 70% | Intervención inmediata |
| 🟠 Naranja | 40-70% | Plan correctivo |
| 🟡 Amarillo | < 40% | Monitoreo |

**Fórmula:**
```
severidad = (1-NDVI)*0.4 + (1-NDMI)*0.3 + (1-SAVI)*0.3
```

---

## 🔧 Archivos Clave

```
informes/motor_analisis/cerebro_diagnostico.py  # Motor principal
informes/helpers/diagnostico_pdf_helper.py      # Helpers PDF
informes/services/generador_pdf.py              # Integración
informes/services/eosda_api.py                  # Descarga de datos
```

---

## 📊 Flujo de Integración

```
1. Parcela con EOSDA Field ID
         ↓
2. Obtener imágenes satelitales (NDVI, NDMI, SAVI)
         ↓
3. Descargar arrays NumPy
         ↓
4. Ejecutar Cerebro de Diagnóstico
         ↓
5. Generar mapa consolidado + tabla
         ↓
6. Insertar en PDF automáticamente
```

---

## 🚨 Troubleshooting

**Error: "No se pudieron obtener todos los índices"**
- ✅ Verifica que `parcela.eosda_field_id` no sea null
- ✅ Revisa que EOSDA_API_KEY esté en `.env`
- ✅ Confirma que hay escenas recientes (< 30 días)

**Error: "Parcela sin geometría"**
- ✅ Agrega coordenadas a la parcela
- ✅ O asegúrate de que `centro_parcela` esté definido

**El PDF no incluye el diagnóstico**
- ✅ Revisa logs: `grep "Diagnóstico" agrotech.log`
- ✅ Verifica que `IndiceMensual` tenga datos recientes
- ✅ Confirma que no hay errores en EOSDA API

---

## 📞 Más Información

- **Documentación completa:** `docs/INTEGRACION_DIAGNOSTICO_PDF.md`
- **Arquitectura del motor:** `docs/CEREBRO_DIAGNOSTICO_V3_FINAL.md`
- **Ejemplos de código:** `docs/ejemplos/ejemplo_integracion_diagnostico_pdf.py`

---

## ✅ Validación Final

- [x] Mapa consolidado con leyenda
- [x] Tabla de desglose por área
- [x] Zona prioritaria con coordenadas
- [x] Narrativa menciona zona roja
- [x] No rompe flujo existente
- [x] Tests pasando
- [x] Documentación completa

**Estado: LISTO PARA PRODUCCIÓN** 🚀
