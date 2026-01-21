# 🧠 Cerebro de Diagnóstico Unificado - Integración PDF
## AgroTech Histórico | Sistema de Análisis Satelital Agrícola

[![Estado](https://img.shields.io/badge/Estado-Production%20Ready-brightgreen)]()
[![Versión](https://img.shields.io/badge/Versi%C3%B3n-1.0.0-blue)]()
[![Tests](https://img.shields.io/badge/Tests-Passing-success)]()

---

## 🎯 ¿Qué es esto?

El **Cerebro de Diagnóstico Unificado** es un sistema avanzado de análisis multi-índice que detecta automáticamente **zonas críticas** en lotes agrícolas mediante triangulación de datos satelitales (NDVI, NDMI, SAVI).

### Características Principales

- 🗺️ **Mapa consolidado** con zonas clasificadas por severidad (Rojo/Naranja/Amarillo)
- 📊 **Desglose preciso** de áreas afectadas por hectárea
- 🎯 **Zona prioritaria** identificada con coordenadas GPS exactas
- 📝 **Narrativas comerciales** adaptadas para agricultores
- 🤖 **Integración automática** en informes PDF

---

## 🚀 Uso Rápido

### Generar Informe con Diagnóstico

```python
from informes.services.generador_pdf import generador_pdf
from informes.models import Parcela

# Obtener parcela sincronizada con EOSDA
parcela = Parcela.objects.get(eosda_field_id='abc123')

# Generar informe (diagnóstico incluido automáticamente)
resultado = generador_pdf.generar_informe_completo(
    parcela=parcela,
    periodo_meses=12,
    tipo_informe='produccion'  # Lenguaje comercial
)

# Verificar resultado
if resultado['success']:
    print(f"✅ PDF generado: {resultado['archivo_pdf']}")
    print(f"📊 Eficiencia del lote: {resultado['diagnostico_unificado']['eficiencia_lote']:.1f}%")
    print(f"📍 Área afectada: {resultado['diagnostico_unificado']['area_afectada_total']:.2f} ha")
```

### Ejecutar Tests

```bash
# Test completo de integración PDF
python test_pdf_diagnostico_final.py

# Test solo del motor de diagnóstico
python test_cerebro_diagnostico.py
```

---

## 📋 Requisitos

1. **Parcela sincronizada con EOSDA**
   - Campo `eosda_field_id` configurado
   - Geometría o centro_parcela definidos

2. **Datos satelitales recientes**
   - Al menos 1 mes de índices calculados
   - Nubosidad < 30% (recomendado)

3. **API Key EOSDA**
   ```bash
   # .env
   EOSDA_API_KEY=your_api_key_here
   EOSDA_BASE_URL=https://api.eos.com
   ```

---

## 🗺️ Output en el PDF

El informe incluye una nueva sección: **"DIAGNÓSTICO UNIFICADO - ZONAS CRÍTICAS"**

### 1. Tabla de Desglose

```
┌─────────────────────┬──────────┬─────────┐
│ Nivel de Severidad  │ Área (ha)│ % Lote  │
├─────────────────────┼──────────┼─────────┤
│ 🔴 Crítica          │   12.50  │  25.0%  │
│ 🟠 Moderada         │    3.20  │   6.4%  │
│ 🟡 Leve             │    1.10  │   2.2%  │
│ ✅ Sin Problemas    │   33.20  │  66.4%  │
├─────────────────────┼──────────┼─────────┤
│ TOTAL               │   50.00  │ 100.0%  │
└─────────────────────┴──────────┴─────────┘
```

### 2. Mapa Consolidado

- Imagen PNG de 6x4.3 pulgadas
- Zonas coloreadas por severidad
- Centroides marcados con círculos
- Leyenda profesional en esquina

### 3. Zona Prioritaria

```
🎯 ZONA PRIORITARIA DE INTERVENCIÓN

Diagnóstico: Déficit Hídrico Severo
Área: 2.30 hectáreas
Severidad: 85%
Coordenadas: 4.567890, -74.123456
Confianza: 92%

Valores de Índices:
• NDVI (Vigor): 0.25
• NDMI (Humedad): 0.18
• SAVI (Cobertura): 0.22
```

---

## 📊 Clasificación de Severidad

| Color | Severidad | Criterio | Acción |
|-------|-----------|----------|--------|
| 🔴 **Rojo** | > 70% | Crítica | Intervención **inmediata** |
| 🟠 **Naranja** | 40-70% | Moderada | Plan correctivo en 7-14 días |
| 🟡 **Amarillo** | < 40% | Leve | Monitoreo quincenal |
| ✅ **Verde** | Saludable | Sin problemas | Mantenimiento normal |

**Fórmula de Severidad:**
```python
severidad = (1 - NDVI) * 0.4 + (1 - NDMI) * 0.3 + (1 - SAVI) * 0.3
```

---

## 🧪 Validación

### Suite de Tests Completa

| Test | Archivo | Estado |
|------|---------|--------|
| Motor de diagnóstico | `test_cerebro_diagnostico.py` | ✅ Pasando |
| Integración PDF | `test_pdf_diagnostico_final.py` | ✅ Pasando |
| Compilación | Linting de archivos | ✅ Sin errores |

### Checklist de Validación

- [x] Mapa consolidado con leyenda
- [x] Tabla de desglose con cálculos correctos
- [x] Zona prioritaria con coordenadas GPS
- [x] Narrativa menciona zona roja explícitamente
- [x] No rompe flujo existente de PDF
- [x] Manejo robusto de errores
- [x] Logging detallado

---

## 🔧 Arquitectura

### Componentes del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    GENERADOR PDF                            │
│  (informes/services/generador_pdf.py)                       │
│                                                              │
│  generar_informe_completo()                                 │
│         ↓                                                    │
│  _ejecutar_diagnostico_cerebro()                            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    SERVICIO EOSDA                           │
│  (informes/services/eosda_api.py)                           │
│                                                              │
│  obtener_imagenes_indice() → Metadata de escenas            │
│  descargar_array_desde_url() → Arrays NumPy                 │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│              CEREBRO DE DIAGNÓSTICO                         │
│  (informes/motor_analisis/cerebro_diagnostico.py)           │
│                                                              │
│  ejecutar_diagnostico_unificado()                           │
│    ├─ Triangulación multi-índice                            │
│    ├─ Detección de clusters (OpenCV)                        │
│    ├─ Clasificación por severidad                           │
│    ├─ Generación de mapa consolidado                        │
│    └─ Narrativas comerciales                                │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                   HELPERS PDF                               │
│  (informes/helpers/diagnostico_pdf_helper.py)               │
│                                                              │
│  generar_tabla_desglose_severidad()                         │
│  agregar_seccion_diagnostico_unificado()                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 Troubleshooting

### Error: "No se pudieron obtener todos los índices"

**Causas posibles:**
- Parcela no sincronizada con EOSDA
- API Key inválida o sin permisos
- No hay escenas recientes (< 30 días)

**Solución:**
```python
# Verificar sincronización
parcela = Parcela.objects.get(id=123)
print(f"EOSDA Field ID: {parcela.eosda_field_id}")  # Debe tener valor

# Verificar API Key
from django.conf import settings
print(f"API Key: {settings.EOSDA_API_KEY[:10]}...")  # Primeros 10 chars

# Verificar datos recientes
from informes.models import IndiceMensual
ultimo = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes').first()
print(f"Último índice: {ultimo.año}-{ultimo.mes}")
```

### Error: "Parcela sin geometría"

**Solución:**
```python
# Opción 1: Agregar geometría en admin Django
parcela.geometria = GEOSGeometry('POLYGON((...)))')
parcela.save()

# Opción 2: Definir centro aproximado
if not parcela.centro_parcela:
    parcela.latitud = 4.5678
    parcela.longitud = -74.1234
    parcela.save()
```

### El PDF no incluye el diagnóstico

**Verificación:**
```bash
# Ver logs de ejecución
grep "Diagnóstico" agrotech.log

# Ver detalles de EOSDA
grep "NDVI\|NDMI\|SAVI" agrotech.log | tail -20

# Ver errores críticos
grep "ERROR\|❌" agrotech.log | tail -10
```

---

## 📚 Documentación Completa

- 📄 **Integración PDF:** [`docs/INTEGRACION_DIAGNOSTICO_PDF.md`](docs/INTEGRACION_DIAGNOSTICO_PDF.md)
- ⚡ **Guía Rápida:** [`GUIA_RAPIDA_DIAGNOSTICO_PDF.md`](GUIA_RAPIDA_DIAGNOSTICO_PDF.md)
- 📝 **Resumen Ejecutivo:** [`INTEGRACION_COMPLETA_DIAGNOSTICO_FINAL.md`](INTEGRACION_COMPLETA_DIAGNOSTICO_FINAL.md)
- ✅ **Checklist:** [`CHECKLIST_FINAL_DIAGNOSTICO.txt`](CHECKLIST_FINAL_DIAGNOSTICO.txt)
- 💻 **Ejemplo de Código:** [`docs/ejemplos/ejemplo_integracion_diagnostico_pdf.py`](docs/ejemplos/ejemplo_integracion_diagnostico_pdf.py)

---

## 🎓 Próximos Pasos (Opcional)

1. **VRA Export** - Generar KML para maquinaria agrícola
2. **Dashboard Web** - Visualización interactiva de diagnósticos
3. **Alertas Automáticas** - Email/SMS cuando se detecten zonas críticas
4. **Machine Learning** - Predicción de tendencias con LSTM
5. **Integración Drones** - Fusión datos satelitales + dron

---

## 📞 Soporte

**Logs útiles:**
```bash
# Ver ejecución completa
tail -f agrotech.log

# Buscar errores específicos
grep "ERROR.*diagnostico" agrotech.log
```

**Tests de validación:**
```bash
python test_cerebro_diagnostico.py      # Motor standalone
python test_pdf_diagnostico_final.py    # Integración completa
```

---

## ✅ Estado del Proyecto

- ✅ **Motor de diagnóstico:** Completado y validado
- ✅ **Integración PDF:** Completado y validado
- ✅ **Tests:** Pasando sin errores
- ✅ **Documentación:** Completa con ejemplos
- ✅ **Producción:** Listo para despliegue

**Última actualización:** Enero 2026  
**Versión:** 1.0.0  
**Autor:** AgroTech Engineering Team

---

## 📜 Licencia

Este módulo es parte del sistema AgroTech Histórico.  
Para uso interno y clientes autorizados.

---

<div align="center">
  
**🚀 Sistema Listo para Producción 🚀**

</div>
