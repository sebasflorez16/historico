# 📸 Flujo de Imágenes Satelitales - Sistema Optimizado

## 🎯 Estrategia de Optimización de Requests

### ❌ Flujo Incorrecto (Consumo excesivo)
```
Descargar imagen directamente
  ↓
Buscar escenas disponibles (10-15 requests)
  ↓
Generar imagen (7 requests)
  ↓
TOTAL: ~17-22 requests por imagen
```

### ✅ Flujo Correcto (Optimizado)
```
1. Obtener Datos Históricos (Statistics API)
   - 1 POST + polling → obtiene índices NDVI/NDMI/SAVI
   - Caché guarda metadatos de escenas disponibles
   - TOTAL: ~8-12 requests (para TODOS los meses)

2. Descargar imágenes específicas (Field Imagery API)
   - Usa metadatos del caché (view_id ya conocido)
   - 1 POST + ~6 GET polling
   - TOTAL: ~7 requests por imagen ✅
```

---

## 📊 Comparación de Consumo

| Escenario | Requests | Notas |
|-----------|----------|-------|
| **Obtener datos históricos** | 8-12 | Una vez por parcela |
| **Descargar imagen (con caché)** | 7 | Por cada imagen |
| **Descargar imagen (sin caché)** | ❌ RECHAZADO | Obliga flujo correcto |
| **Imagen ya descargada** | 0 | Reutiliza archivo local |

---

## 🔄 Flujo Completo Paso a Paso

### Paso 1: Sincronizar Parcela con EOSDA
```
Parcelas → Detalle Parcela → Sincronizar con EOSDA
```
- Crea campo en EOSDA Field Management
- Obtiene `field_id` único
- **Requests:** 1-2

### Paso 2: Obtener Datos Históricos
```
Parcelas → Detalle Parcela → Obtener Datos Históricos
```
**Qué hace:**
- Solicita índices NDVI, NDMI, SAVI para rango de fechas
- Obtiene también temperatura y precipitación
- **Guarda en caché:** metadatos de escenas (view_id, fecha, nubosidad)
- Crea registros mensuales en `IndiceMensual`

**Requests:** ~8-12 (para 6-12 meses de datos)

**Resultado:**
```python
# Caché de Statistics API
{
  'resultados': [
    {
      'id': 'S2L2A/18/N/YL/2025/10/26/0',  # ← view_id para Field Imagery
      'date': '2025-10-26',
      'cloud': 17.14,
      'indexes': {
        'NDVI': {'average': 0.724, 'max': 0.85, 'min': 0.65},
        'NDMI': {'average': 0.456, ...},
        'SAVI': {'average': 0.612, ...}
      }
    },
    # ... más escenas
  ]
}
```

### Paso 3: Ver Datos Guardados
```
Parcelas → Detalle Parcela → Ver Datos Guardados
```
- Muestra tabla con registros mensuales
- Indicadores de estado: ✅ imagen descargada / 📥 pendiente

### Paso 4: Descargar Imágenes Específicas
```
En tabla de datos → Seleccionar índice (NDVI/NDMI/SAVI) → Click 📷
```

**Proceso optimizado:**

1. **Sistema verifica campo `imagen_ndvi`**
   - Si existe → retorna URL (0 requests)
   - Si NO existe → continúa

2. **Sistema busca en caché de Statistics**
   - Extrae `view_id` para ese mes
   - Si NO hay caché → rechaza con mensaje:
     ```
     ⚠️ Sin datos de Statistics API para 2025-10.
     
     📋 Flujo correcto:
     1️⃣ Obtener Datos Históricos (Statistics API)
     2️⃣ Descargar imágenes específicas
     
     💡 Esto ahorra ~10-15 requests por imagen.
     ```

3. **Descarga imagen usando view_id del caché**
   ```python
   POST /field-imagery/indicies/{field_id}
   {
     "view_id": "S2L2A/18/N/YL/2025/10/26/0",  # Del caché
     "index": "ndvi",
     "format": "png"
   }
   → {"request_id": "abc123"}
   
   # Polling (6 intentos, 10s cada uno)
   GET /field-imagery/{field_id}/abc123
   → 202... 202... 200 OK (bytes de PNG)
   ```
   **Requests:** 1 POST + ~6 GET = **7 requests**

4. **Sistema guarda imagen**
   ```
   media/imagenes_satelitales/2025/10/ndvi/lote1_2025_10_NDVI.png
   ```
   - Actualiza campo `imagen_ndvi` en modelo
   - Guarda metadatos: `view_id_imagen`, `fecha_imagen`, `nubosidad_imagen`

5. **Frontend abre imagen en nueva pestaña**

---

## 💾 Estructura de Caché

### Caché de Statistics API (`CacheDatosEOSDA`)
**Guarda:**
- `field_id`: ID de la parcela en EOSDA
- `fecha_inicio` / `fecha_fin`: Rango temporal
- `indices`: Lista de índices solicitados
- `datos_json`: Escenas con metadatos
- `valido_hasta`: Fecha de expiración (24h)

**NO guarda imágenes**, solo metadatos.

### "Caché" de Imágenes (`IndiceMensual.imagen_*`)
**Guarda:**
- Archivo físico en `media/imagenes_satelitales/`
- Campos del modelo: `imagen_ndvi`, `imagen_ndmi`, `imagen_savi`
- Metadatos: `view_id_imagen`, `fecha_imagen`, `nubosidad_imagen`

**La imagen se descarga UNA SOLA VEZ**, después se reutiliza.

---

## 🎨 Uso en Reportes PDF

### Estrategia Recomendada
```
Para cada informe mensual:
  1. Verificar si hay imagen NDVI del mes
  2. Si NO existe → descargar (7 requests)
  3. Si existe → usar archivo local (0 requests)
  4. Incluir en PDF con análisis
```

### Ejemplo de Consumo Total
```
Informe de 6 meses para 1 parcela:
  - Statistics API: 10 requests (una vez)
  - Imagen NDVI por mes: 7 × 6 = 42 requests
  - TOTAL: 52 requests

Reportes futuros de la misma parcela:
  - Reutilizan imágenes existentes
  - Solo nuevos meses: 7 requests por imagen nueva
```

---

## 🛠️ Comandos Útiles

### Verificar caché sin consumir requests
```bash
python verificar_cache_imagenes.py
```
Muestra:
- Parcelas sincronizadas
- Registros mensuales disponibles
- Escenas en caché por mes
- Estado de imágenes descargadas

### Limpiar imágenes antiguas (opcional)
```python
# Eliminar imágenes de meses con > 90 días
from informes.models import IndiceMensual
from datetime import datetime, timedelta

fecha_limite = datetime.now() - timedelta(days=90)
registros_antiguos = IndiceMensual.objects.filter(
    fecha_consulta_api__lt=fecha_limite
)

for registro in registros_antiguos:
    if registro.imagen_ndvi:
        registro.imagen_ndvi.delete()
    if registro.imagen_ndmi:
        registro.imagen_ndmi.delete()
    if registro.imagen_savi:
        registro.imagen_savi.delete()
    registro.save()
```

---

## 🚀 Resumen para Desarrolladores

### Principios de Optimización
1. **Statistics primero, imágenes después**
2. **Caché es tu amigo** - reutiliza metadatos
3. **Descarga bajo demanda** - solo lo necesario
4. **Reutiliza archivos locales** - verifica antes de descargar

### Prevención de Desperdicio
- ❌ NO buscar escenas si no hay caché Statistics
- ❌ NO descargar imagen si archivo ya existe
- ✅ SÍ obligar flujo correcto con mensajes claros
- ✅ SÍ reutilizar imágenes en múltiples reportes

### Monitoreo
```python
# Ver consumo de requests por usuario
from informes.models_configuracion import EstadisticaUsoEOSDA

EstadisticaUsoEOSDA.objects.filter(
    tipo_operacion='field_imagery'
).aggregate(
    total_requests=Sum('requests_consumidos')
)
```

---

## 📞 Soporte

Si una descarga falla:
1. Verificar que hay caché de Statistics (`verificar_cache_imagenes.py`)
2. Revisar logs: `INFO: Descargando imagen NDVI...`
3. Verificar nubosidad de escenas disponibles (<50%)
4. Confirmar que `field_id` es válido en EOSDA

**Flujo correcto siempre: Statistics → Imágenes → PDFs**
