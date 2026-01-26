# GUÍA COMPLETA: DESCARGA DE DATOS GEOGRÁFICOS OFICIALES
## Para Sistema de Verificación Legal - AgroTech Histórico

Fecha: 26 de enero de 2026

---

## 🎯 RESUMEN: ¿QUÉ DATOS NECESITAS?

| Capa | Estado Actual | Criticidad | Tiempo Estimado |
|------|---------------|------------|-----------------|
| **Red Hídrica (drenajes)** | ❌ Datos incorrectos (polígonos) | 🔴 CRÍTICO | 2-4 horas |
| **Áreas Protegidas RUNAP** | ❌ No descargado | 🟡 IMPORTANTE | 30 minutos |
| **Resguardos Indígenas** | ❌ No descargado | 🟡 IMPORTANTE | 1-2 horas |
| **Páramos** | ❌ No descargado | 🟢 OPCIONAL | 1-2 horas |

---

## 1️⃣ RED HÍDRICA - DRENAJES SENCILLOS (CRÍTICO)

### ❌ Problema Actual
Tienes descargada la "Zonificación Hidrográfica" que son POLÍGONOS de cuencas completas.
Por eso marca 100% del predio - la parcela está dentro de una cuenca, no cerca de un río.

### ✅ Lo que Necesitas
**Drenajes Sencillos** del IGAC: líneas (LineStrings) que representan ríos y quebradas reales.

### 📥 OPCIÓN 1: Portal Datos Abiertos Colombia (MÁS FÁCIL)

**URL**: https://www.datos.gov.co/

**Pasos**:
1. Ir a https://www.datos.gov.co/
2. Buscar: **"Drenajes Sencillos"** o **"Red Hídrica IGAC"**
3. Filtrar por:
   - Formato: **Shapefile** o **GeoJSON**
   - Escala: **1:100.000** (cobertura nacional)
   - Fuente: **IGAC**

**Datasets recomendados**:
- "Drenajes Sencillos Escala 1:100.000" (nacional)
- "Red Hídrica Colombia" (IGAC)

**Nota**: Si no encuentras "drenajes", busca:
- "hidrografia lineal"
- "corrientes de agua"
- "red hidrica nacional"

### 📥 OPCIÓN 2: GeoPortal IGAC (MÁS COMPLETO)

**URL**: https://geoportal.igac.gov.co/

**Pasos**:
1. Crear cuenta gratuita en el GeoPortal IGAC
2. Ir a "Servicios de Descarga"
3. Buscar: **"Cartografía Básica"** → **"Hidrografía"**
4. Seleccionar: **"Drenajes Sencillos"** o **"Corrientes de Agua"**
5. Filtrar por departamento (opcional): **Cesar** (tu parcela está ahí)
6. Formato: **Shapefile (.shp)**
7. Descargar

**Tamaño estimado**: 50-500 MB (según cobertura)

### 📥 OPCIÓN 3: API IGAC (PARA PROGRAMADORES)

```bash
# WFS Service del IGAC
wget "https://geoservicios.igac.gov.co/geoserver/cartografia_basica/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=cartografia_basica:drenaje_sencillo&outputFormat=shape-zip" -O drenajes_igac.zip
```

### 🔍 VALIDACIÓN: ¿Descargaste los datos correctos?

Después de descargar, ejecuta este script de validación:

```python
import geopandas as gpd

# Cargar shapefile descargado
gdf = gpd.read_file('ruta/al/archivo.shp')

# Verificar geometrías
tipos = gdf.geometry.geom_type.unique()
print(f"Tipos de geometría: {tipos}")

# ✅ CORRECTO si ves:
# ['LineString'] o ['MultiLineString', 'LineString']

# ❌ INCORRECTO si ves:
# ['Polygon'] o ['MultiPolygon']

# Ver cuántos elementos
print(f"Total elementos: {len(gdf)}")
# Esperable: 50,000 - 500,000 (red nacional completa)

# Ver columnas
print(f"Columnas: {gdf.columns.tolist()}")
# Busca columnas como: NOMBRE, ORDEN, TIPO, PERMANENCIA
```

### 📂 Dónde guardar
```
historico/
  datos_geograficos/
    red_hidrica/
      drenajes_sencillos_igac.shp  ← AQUÍ
      drenajes_sencillos_igac.shx
      drenajes_sencillos_igac.dbf
      drenajes_sencillos_igac.prj
```

**¡IMPORTANTE!**: Elimina los archivos viejos de zonificación (geo_export_*.shp)

---

## 2️⃣ ÁREAS PROTEGIDAS - RUNAP (IMPORTANTE)

### ✅ Datos Oficiales
Registro Único Nacional de Áreas Protegidas - Parques Nacionales Naturales

### 📥 OPCIÓN 1: API WFS de Parques Nacionales (RECOMENDADO)

**Script automático** (ya lo tienes implementado):

```python
# En tu terminal:
cd /Users/sebastianflorez/Documents/Historico\ Agrotech/historico
conda run -n agro-rest python -c "
from verificador_legal import VerificadorRestriccionesLegales
import geopandas as gpd
import os

# Descargar de API WFS
url = 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=json'

gdf = gpd.read_file(url)
print(f'Descargado: {len(gdf)} áreas protegidas')

# Guardar
os.makedirs('datos_geograficos/runap', exist_ok=True)
gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shp')
print('Guardado en: datos_geograficos/runap/areas_protegidas_runap.shp')
"
```

### 📥 OPCIÓN 2: Portal RUNAP

**URL**: http://runap.parquesnacionales.gov.co/

**Pasos**:
1. Ir a "Descargas"
2. Seleccionar: **"Capas Geográficas"**
3. Formato: **Shapefile**
4. Descargar

### 📂 Dónde guardar
```
historico/
  datos_geograficos/
    runap/
      areas_protegidas_runap.shp  ← AQUÍ
      areas_protegidas_runap.shx
      areas_protegidas_runap.dbf
      areas_protegidas_runap.prj
```

---

## 3️⃣ RESGUARDOS INDÍGENAS - ANT (IMPORTANTE)

### ✅ Datos Oficiales
Agencia Nacional de Tierras - Límites de Resguardos Indígenas

### 📥 OPCIÓN 1: Portal ANT

**URL**: https://www.ant.gov.co/

**Pasos**:
1. Ir a "Sistemas de Información Geográfica"
2. Buscar: **"Resguardos Indígenas"**
3. Descargar shapefile

**⚠️ Nota**: Puede requerir registro o solicitud formal

### 📥 OPCIÓN 2: Datos Abiertos Colombia

**URL**: https://www.datos.gov.co/

**Buscar**: "Resguardos Indígenas ANT" o "Territorios Colectivos"

### 📥 OPCIÓN 3: IGAC (Alternativa)

El IGAC también tiene capas de resguardos en su GeoPortal:
- https://geoportal.igac.gov.co/
- Buscar: "Territorios Étnicos" o "Resguardos"

### 📂 Dónde guardar
```
historico/
  datos_geograficos/
    resguardos/
      resguardos_indigenas.shp  ← AQUÍ
      resguardos_indigenas.shx
      resguardos_indigenas.dbf
      resguardos_indigenas.prj
```

---

## 4️⃣ PÁRAMOS - IDEAM/MINAMBIENTE (OPCIONAL)

### ✅ Datos Oficiales
Delimitación de Páramos - MinAmbiente/IDEAM

### 📥 OPCIÓN 1: Portal SIAC (Sistema de Información Ambiental)

**URL**: http://www.siac.gov.co/

**Pasos**:
1. Ir a "Información Geográfica"
2. Buscar: **"Delimitación de Páramos"**
3. Formato: Shapefile
4. Descargar

### 📥 OPCIÓN 2: IDEAM

**URL**: http://www.ideam.gov.co/

**Buscar**: "Ecosistemas" → "Páramos"

### 📥 OPCIÓN 3: MinAmbiente

**URL**: https://www.minambiente.gov.co/

**Sección**: Mapas y Datos Geográficos

### 📂 Dónde guardar
```
historico/
  datos_geograficos/
    paramos/
      delimitacion_paramos.shp  ← AQUÍ
      delimitacion_paramos.shx
      delimitacion_paramos.dbf
      delimitacion_paramos.prj
```

---

## 🚀 SCRIPT DE DESCARGA AUTOMÁTICA

Guarda esto como `descargar_datos_oficiales.py`:

```python
#!/usr/bin/env python
"""
Script para descargar automáticamente todas las capas geográficas oficiales
"""
import geopandas as gpd
import os
from pathlib import Path

def crear_directorios():
    """Crear estructura de directorios"""
    dirs = [
        'datos_geograficos/red_hidrica',
        'datos_geograficos/runap',
        'datos_geograficos/resguardos',
        'datos_geograficos/paramos'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("✅ Directorios creados")

def descargar_runap():
    """Descargar áreas protegidas RUNAP"""
    print("\n📥 Descargando RUNAP...")
    try:
        url = 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=json'
        gdf = gpd.read_file(url)
        output = 'datos_geograficos/runap/areas_protegidas_runap.shp'
        gdf.to_file(output)
        print(f"✅ RUNAP descargado: {len(gdf)} áreas protegidas → {output}")
        return True
    except Exception as e:
        print(f"❌ Error descargando RUNAP: {e}")
        return False

def validar_red_hidrica():
    """Validar que los drenajes sean LineString"""
    print("\n🔍 Validando red hídrica...")
    directorio = Path('datos_geograficos/red_hidrica')
    
    if not directorio.exists():
        print("❌ No existe directorio datos_geograficos/red_hidrica")
        return False
    
    shapefiles = list(directorio.glob('*.shp'))
    if not shapefiles:
        print("❌ No hay shapefiles en red_hidrica/")
        return False
    
    for shp in shapefiles:
        gdf = gpd.read_file(str(shp))
        tipos = gdf.geometry.geom_type.unique()
        
        if any(t in ['Polygon', 'MultiPolygon'] for t in tipos):
            print(f"❌ {shp.name} contiene POLÍGONOS (zonificación)")
            print(f"   Necesitas DRENAJES LINEALES, no zonificación")
            return False
        elif any(t in ['LineString', 'MultiLineString'] for t in tipos):
            print(f"✅ {shp.name} contiene LÍNEAS (correcto)")
            print(f"   Elementos: {len(gdf)}")
            return True
    
    return False

if __name__ == '__main__':
    print("=" * 80)
    print("DESCARGA AUTOMÁTICA DE DATOS GEOGRÁFICOS OFICIALES")
    print("=" * 80)
    
    crear_directorios()
    descargar_runap()
    validar_red_hidrica()
    
    print("\n" + "=" * 80)
    print("RESUMEN:")
    print("=" * 80)
    print("\n✅ Descarga automática: RUNAP")
    print("\n⚠️  DESCARGA MANUAL REQUERIDA:")
    print("   1. Red Hídrica (drenajes) - Ver GUIA_DESCARGA_DATOS_OFICIALES.md")
    print("   2. Resguardos Indígenas - https://www.ant.gov.co/")
    print("   3. Páramos (opcional) - http://www.siac.gov.co/")
    print("\n" + "=" * 80)
```

**Ejecutar**:
```bash
cd /Users/sebastianflorez/Documents/Historico\ Agrotech/historico
conda run -n agro-rest python descargar_datos_oficiales.py
```

---

## ✅ CHECKLIST: ¿Tengo todos los datos correctos?

Ejecuta este script de validación final:

```python
import geopandas as gpd
from pathlib import Path

def validar_datos():
    base = Path('datos_geograficos')
    
    print("=" * 80)
    print("VALIDACIÓN DE DATOS GEOGRÁFICOS")
    print("=" * 80 + "\n")
    
    # 1. Red hídrica
    red_dir = base / 'red_hidrica'
    if red_dir.exists() and list(red_dir.glob('*.shp')):
        shp = list(red_dir.glob('*.shp'))[0]
        gdf = gpd.read_file(str(shp))
        tipos = gdf.geometry.geom_type.unique()
        
        if any(t in ['LineString', 'MultiLineString'] for t in tipos):
            print(f"✅ Red Hídrica: CORRECTO ({len(gdf)} drenajes)")
        else:
            print(f"❌ Red Hídrica: INCORRECTO (polígonos de zonificación)")
    else:
        print("❌ Red Hídrica: NO ENCONTRADA")
    
    # 2. RUNAP
    runap_dir = base / 'runap'
    if runap_dir.exists() and list(runap_dir.glob('*.shp')):
        shp = list(runap_dir.glob('*.shp'))[0]
        gdf = gpd.read_file(str(shp))
        print(f"✅ RUNAP: ENCONTRADO ({len(gdf)} áreas protegidas)")
    else:
        print("❌ RUNAP: NO ENCONTRADO")
    
    # 3. Resguardos
    resg_dir = base / 'resguardos'
    if resg_dir.exists() and list(resg_dir.glob('*.shp')):
        shp = list(resg_dir.glob('*.shp'))[0]
        gdf = gpd.read_file(str(shp))
        print(f"✅ Resguardos: ENCONTRADO ({len(gdf)} resguardos)")
    else:
        print("⚠️  Resguardos: NO ENCONTRADO (importante)")
    
    # 4. Páramos
    par_dir = base / 'paramos'
    if par_dir.exists() and list(par_dir.glob('*.shp')):
        shp = list(par_dir.glob('*.shp'))[0]
        gdf = gpd.read_file(str(shp))
        print(f"✅ Páramos: ENCONTRADO ({len(gdf)} páramos)")
    else:
        print("⚠️  Páramos: NO ENCONTRADO (opcional)")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    validar_datos()
```

---

## 🎯 PRIORIDADES DE DESCARGA

### Descarga HOY (crítico para funcionar):
1. **Drenajes Sencillos IGAC** → Reemplaza los polígonos actuales
2. **RUNAP** → Ejecuta script automático arriba

### Descarga esta semana (importante):
3. **Resguardos Indígenas ANT**

### Descarga cuando puedas (opcional):
4. **Páramos** (solo si trabajas en zonas de alta montaña)

---

## 📞 AYUDA Y SOPORTE

**Si no puedes descargar**:
- IGAC: soporte@igac.gov.co
- ANT: atencionalciudadano@ant.gov.co
- Parques Nacionales: correspondencia@parquesnacionales.gov.co

**Foros útiles**:
- https://gis.stackexchange.com/questions/tagged/colombia
- Grupo Telegram: GIS Colombia

---

## 🔄 DESPUÉS DE DESCARGAR

1. **Eliminar datos viejos**:
```bash
rm datos_geograficos/red_hidrica/geo_export_*.shp
rm datos_geograficos/red_hidrica/geo_export_*.shx
rm datos_geograficos/red_hidrica/geo_export_*.dbf
```

2. **Copiar datos nuevos** a `datos_geograficos/`

3. **Ejecutar test**:
```bash
conda run -n agro-rest python test_pdf_verificacion_con_mapa.py
```

4. **Verificar resultado**:
   - ✅ Red hídrica: confianza ALTA
   - ✅ Áreas protegidas: confianza ALTA
   - ✅ Área cultivable: DETERMINABLE
   - ✅ Restricciones realistas (no 100%)

---

**Última actualización**: 26 de enero de 2026
