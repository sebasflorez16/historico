# 🗺️ UBICACIONES EXACTAS PARA DESCARGA MANUAL DE DATOS

## ✅ OPCIÓN MÁS FÁCIL: Descargas Directas

### 1️⃣ RED HÍDRICA - DRENAJES (CRÍTICO) 🔴

**Opción A - datos.gov.co (MÁS FÁCIL)**
1. Ir a: https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Red-H-drica-de-Colombia/rft4-7cca
2. Click en **"Exportar"** (botón azul arriba a la derecha)
3. Seleccionar: **"Shapefile"**
4. Click **"Descargar"**
5. Guardar archivo ZIP
6. Extraer y copiar TODO el contenido a: `datos_geograficos/red_hidrica/`

**Opción B - IGAC GeoPortal (MÁS COMPLETO)**
1. Ir a: https://geoportal.igac.gov.co/contenido/datos-abiertos-cartografia-y-geografia
2. Buscar: **"Drenajes Sencillos"** o **"Cartografía Básica"**
3. Descargar **Shapefile**
4. Guardar en: `datos_geograficos/red_hidrica/`

**⚠️ VERIFICAR QUE SEA CORRECTO:**
- Debe tener archivos: `.shp`, `.shx`, `.dbf`, `.prj`
- Al abrirlo debe mostrar **LÍNEAS** (ríos/quebradas), NO polígonos

---

### 2️⃣ ÁREAS PROTEGIDAS - RUNAP 🟡

**Descarga Directa API (AUTOMÁTICA)**

Copia y pega esto en el terminal:

```bash
cd /Users/sebastianflorez/Documents/Historico\ Agrotech/historico

python3 -c "
import geopandas as gpd
from pathlib import Path

Path('datos_geograficos/runap').mkdir(parents=True, exist_ok=True)

url = 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=json'

print('Descargando RUNAP...')
gdf = gpd.read_file(url)
gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shp')
print(f'✅ Descargado: {len(gdf)} áreas protegidas')
"
```

**O Manual:**
1. Ir a: http://runap.parquesnacionales.gov.co/descargas
2. Descargar shapefile de áreas protegidas
3. Guardar en: `datos_geograficos/runap/`

---

### 3️⃣ RESGUARDOS INDÍGENAS 🟡

**Opción A - datos.gov.co**
1. Ir a: https://www.datos.gov.co/Mapas-Nacionales/Resguardos-Ind-genas/mqfn-ttqs
2. Click **"Exportar"** → **"Shapefile"**
3. Descargar
4. Guardar en: `datos_geograficos/resguardos/`

**Opción B - ANT**
1. Ir a: https://www.ant.gov.co/transparencia-y-acceso-a-la-informacion-publica/datos-abiertos
2. Buscar: "Resguardos Indígenas"
3. Descargar shapefile
4. Guardar en: `datos_geograficos/resguardos/`

---

### 4️⃣ PÁRAMOS (OPCIONAL) 🟢

**Opción A - datos.gov.co**
1. Ir a: https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Delimitaci-n-de-P-ramos/qfpw-ga2x
2. Click **"Exportar"** → **"Shapefile"**
3. Descargar
4. Guardar en: `datos_geograficos/paramos/`

**Opción B - SIAC**
1. Ir a: http://www.siac.gov.co/catalogo-de-mapas
2. Buscar: "Páramos"
3. Descargar shapefile
4. Guardar en: `datos_geograficos/paramos/`

---

## 📁 ESTRUCTURA FINAL ESPERADA

Después de descargar, tu carpeta debe verse así:

```
historico/
  datos_geograficos/
    red_hidrica/
      drenajes_igac.shp           ← CRÍTICO
      drenajes_igac.shx
      drenajes_igac.dbf
      drenajes_igac.prj
    
    runap/
      areas_protegidas_runap.shp  ← IMPORTANTE
      areas_protegidas_runap.shx
      areas_protegidas_runap.dbf
      areas_protegidas_runap.prj
    
    resguardos/
      resguardos_indigenas.shp    ← IMPORTANTE
      resguardos_indigenas.shx
      resguardos_indigenas.dbf
      resguardos_indigenas.prj
    
    paramos/
      delimitacion_paramos.shp    ← OPCIONAL
      delimitacion_paramos.shx
      delimitacion_paramos.dbf
      delimitacion_paramos.prj
```

---

## ✅ SCRIPT DE VALIDACIÓN

Después de descargar, ejecuta esto para validar:

```bash
cd /Users/sebastianflorez/Documents/Historico\ Agrotech/historico

python3 -c "
import geopandas as gpd
from pathlib import Path

print('='*80)
print('VALIDACIÓN DE DATOS DESCARGADOS')
print('='*80 + '\n')

base = Path('datos_geograficos')

# Red hídrica
red_dir = base / 'red_hidrica'
if red_dir.exists() and list(red_dir.glob('*.shp')):
    shp = list(red_dir.glob('*.shp'))[0]
    gdf = gpd.read_file(str(shp))
    tipos = gdf.geometry.geom_type.unique()
    if any(t in ['LineString', 'MultiLineString'] for t in tipos):
        print(f'✅ Red Hídrica: CORRECTO ({len(gdf)} drenajes)')
    else:
        print(f'❌ Red Hídrica: INCORRECTO (polígonos, no líneas)')
        print(f'   ELIMINA Y DESCARGA DE NUEVO')
else:
    print('❌ Red Hídrica: NO ENCONTRADA')

# RUNAP
runap_dir = base / 'runap'
if runap_dir.exists() and list(runap_dir.glob('*.shp')):
    gdf = gpd.read_file(str(list(runap_dir.glob('*.shp'))[0]))
    print(f'✅ RUNAP: ENCONTRADO ({len(gdf)} áreas)')
else:
    print('❌ RUNAP: NO ENCONTRADO')

# Resguardos
resg_dir = base / 'resguardos'
if resg_dir.exists() and list(resg_dir.glob('*.shp')):
    gdf = gpd.read_file(str(list(resg_dir.glob('*.shp'))[0]))
    print(f'✅ Resguardos: ENCONTRADO ({len(gdf)} resguardos)')
else:
    print('⚠️  Resguardos: NO ENCONTRADO')

# Páramos
par_dir = base / 'paramos'
if par_dir.exists() and list(par_dir.glob('*.shp')):
    gdf = gpd.read_file(str(list(par_dir.glob('*.shp'))[0]))
    print(f'✅ Páramos: ENCONTRADO ({len(gdf)} páramos)')
else:
    print('⚠️  Páramos: NO ENCONTRADO')

print('\n' + '='*80)
"
```

---

## 🚀 DESPUÉS DE DESCARGAR

1. **Eliminar datos viejos incorrectos:**
```bash
rm datos_geograficos/red_hidrica/geo_export_*.shp
rm datos_geograficos/red_hidrica/geo_export_*.shx
rm datos_geograficos/red_hidrica/geo_export_*.dbf
rm datos_geograficos/red_hidrica/geo_export_*.prj
```

2. **Ejecutar test:**
```bash
conda run -n agro-rest python test_pdf_verificacion_con_mapa.py
```

3. **Verificar resultado:**
   - Red hídrica: confianza ALTA ✅
   - Área cultivable: DETERMINABLE ✅
   - Restricciones realistas (NO 100%) ✅

---

## 💡 SI TIENES PROBLEMAS

1. **No puedes acceder a datos.gov.co:**
   - Prueba con VPN o proxy
   - Intenta desde otro navegador
   - Contacta: datos@funcionpublica.gov.co

2. **Los archivos no se abren:**
   - Asegúrate de extraer el ZIP completo
   - Verifica que tengas los 4 archivos (.shp, .shx, .dbf, .prj)

3. **Sigue dando 100% de restricción:**
   - Verifica que NO sean polígonos (ejecuta script de validación)
   - Deben ser LineString/MultiLineString

---

**Fecha:** 26 de enero de 2026  
**Prioridad:** Red Hídrica > RUNAP > Resguardos > Páramos
