# 🚨 PROBLEMA CRÍTICO: Shapefile de Red Hídrica NO Cubre Tauramena, Casanare

## Diagnóstico Completo

### 1. Problema Inicial
- **Síntoma:** Distancias de 200+ km a fuentes de agua en pleno Llano (imposible)
- **Parcela afectada:** Parcela #6 (Tauramena, Casanare)
  - Ubicación: -72.236°, 5.222°
  - Río cercano conocido: **Río Cravo Sur** (~1-2 km)

### 2. Causa Raíz Identificada

Se están usando **DOS shapefiles INCORRECTOS**:

#### A. `geo_export_f2706386...shp` (11.7 MB)
- ❌ **Tipo:** ZONIFICACIÓN HIDROGRÁFICA (polígonos de cuencas)
- ❌ **Geometría:** Polygon/MultiPolygon (NO líneas de cauces)
- ❌ **Uso incorrecto:** Mide distancia a CUENCAS, no a ríos
- ⚠️  **Resultado:** "0 km" porque la parcela está DENTRO del polígono de la subcuenca "Río Cravo Sur"
- **Nivel de confianza:** BAJO (zonificación, no red real)

#### B. `drenajes_sencillos_igac.shp` (1.4 MB)
- ✅ **Tipo:** DRENAJE REAL (líneas de cauces)
- ✅ **Geometría:** LineString (correcta)
- ❌ **Cobertura:** Solo zona ORIENTAL de Casanare (lon: -69.7 a -68.9)
- ❌ **Problema:** NO cubre Tauramena (lon: -72.2)
- ⚠️  **Resultado:** "280 km" al cauce más cercano (fuera de cobertura)
- **Nivel de confianza:** ALTO (geometría correcta) pero **SIN COBERTURA**

### 3. Verificación de Cobertura

```
Parcela 6:
  Ubicación: -72.236°, 5.222° (Tauramena, noroccidente de Casanare)
  
Shapefile drenajes_sencillos_igac.shp:
  Cobertura: -69.7 a -68.9° (zona oriental)
  Distancia a parcela: ~273 km
  Cauces en bbox Tauramena [-72.5, -72.0, 5.0, 5.5]: 0 ❌
```

## Soluciones

### Opción 1: Descargar Shapefile Completo IGAC (RECOMENDADO)
Descargar el shapefile de **Drenaje Sencillo** completo del IGAC que cubra TODO Casanare:

**Fuente oficial:**
- IGAC: https://geoportal.igac.gov.co/
- Capa: "Drenaje Sencillo 1:100.000" o "Drenaje Sencillo 1:25.000"
- Formato: Shapefile (.shp) con geometría LineString
- Cobertura: Nacional o departamental (Casanare completo)

**Verificar que tenga:**
- ✅ Geometría: LineString (líneas de cauces)
- ✅ Cobertura: Longitud -73.0 a -69.0 (todo Casanare)
- ✅ Campo NOMBRE_GEO (nombres de ríos/quebradas)

### Opción 2: OpenStreetMap API (TEMPORAL)
Mientras consigues el shapefile correcto, usar API de OpenStreetMap:

```python
import requests

def obtener_rios_osm(lon, lat, radio_km=10):
    """
    Obtener ríos cercanos de OpenStreetMap (Overpass API)
    GRATIS pero con límites de rate
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    radio_m = radio_km * 1000
    
    query = f"""
    [out:json];
    (
      way["waterway"="river"](around:{radio_m},{lat},{lon});
      way["waterway"="stream"](around:{radio_m},{lat},{lon});
    );
    out geom;
    """
    
    response = requests.post(overpass_url, data={'data': query})
    return response.json()
```

### Opción 3: Datos Hidrográficos IDEAM (ALTERNATIVA)
IDEAM también publica capas de red hídrica:
- Portal: http://dhime.ideam.gov.co/
- Capa: "Sistema Hidrográfico Nacional"
- Ventaja: Más actualizado que IGAC
- Desventaja: Puede ser más pesado

## Próximos Pasos

1. **URGENTE:** Descargar shapefile de Drenaje Sencillo COMPLETO que cubra Tauramena
   - Verificar que `len(red.cx[-72.5:-72.0, 5.0:5.5]) > 0`
   - Confirmar que geometría es LineString

2. **Actualizar código** para priorizar archivo correcto:
   ```python
   # En verificador_legal.py, línea ~165
   archivos_prioritarios = [
       'drenaje_sencillo_casanare_completo.shp',  # NUEVO
       'drenajes_sencillos_igac.shp',
       'red_hidrica.shp'
   ]
   ```

3. **Documentar nivel de confianza** en PDF:
   - Si usa shapefile correcto con cobertura: "ALTA ✅"
   - Si usa shapefile parcial (sin cobertura): "SIN DATOS ⚠️"
   - Si usa zonificación (polígonos): "BAJA ❌"

4. **Agregar validación** en tiempo de carga:
   ```python
   if len(red_filtrada_zona) == 0:
       print(f"⚠️  Sin cobertura en zona de {departamento}")
       self.niveles_confianza['red_hidrica']['confianza'] = 'Sin datos'
   ```

## Archivos Afectados

- `/datos_geograficos/red_hidrica/geo_export_f2706386...shp` ❌ REMOVER (zonificación)
- `/datos_geograficos/red_hidrica/drenajes_sencillos_igac.shp` ⚠️  REEMPLAZAR (cobertura parcial)
- `/verificador_legal.py` línea 165 - Priorización de archivos
- `/generador_pdf_legal.py` línea 291 - Cálculo de distancias
- `/generar_pdf_verificacion_casanare.py` - Script de prueba

## Referencias
- Río Cravo Sur (realidad): ~1-2 km de Tauramena
- Coordenadas Tauramena: -72.236°, 5.222°
- Bbox Casanare completo: [-73.0, 5.0, -69.0, 6.5]
