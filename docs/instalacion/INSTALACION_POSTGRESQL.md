# Instalación PostgreSQL + PostGIS para AgroTech Histórico

Esta guía te ayudará a configurar PostgreSQL con la extensión PostGIS para un rendimiento óptimo con datos geoespaciales.

## 🗄️ ¿Por qué PostgreSQL + PostGIS?

### **Ventajas sobre SQLite:**
- 🚀 **Rendimiento:** Índices espaciales para consultas ultra-rápidas
- 📐 **Funciones GIS:** Cálculos de área, distancia, intersecciones nativas
- 🔍 **Consultas Avanzadas:** Búsquedas por proximidad, análisis espacial
- 📊 **Escalabilidad:** Manejo eficiente de grandes volúmenes de datos

## 🔧 Instalación

### **macOS (con Homebrew):**

```bash
# 1. Instalar PostgreSQL
brew install postgresql@15

# 2. Instalar PostGIS
brew install postgis

# 3. Iniciar PostgreSQL
brew services start postgresql@15

# 4. Crear usuario y base de datos
psql postgres

-- En la consola de PostgreSQL:
CREATE USER agrotech_user WITH PASSWORD 'agrotech_password';
CREATE DATABASE agrotech_historico OWNER agrotech_user;

-- Conectar a la nueva base de datos
\c agrotech_historico

-- Habilitar extensión PostGIS
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

-- Verificar instalación
SELECT PostGIS_version();

-- Dar permisos al usuario
GRANT ALL PRIVILEGES ON DATABASE agrotech_historico TO agrotech_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO agrotech_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO agrotech_user;

\q
```

### **Ubuntu/Debian:**

```bash
# 1. Actualizar sistema
sudo apt update

# 2. Instalar PostgreSQL y PostGIS
sudo apt install postgresql postgresql-contrib postgis postgresql-15-postgis-3

# 3. Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 4. Configurar usuario y base de datos
sudo -u postgres psql

-- En PostgreSQL:
CREATE USER agrotech_user WITH PASSWORD 'agrotech_password';
CREATE DATABASE agrotech_historico OWNER agrotech_user;
\c agrotech_historico
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
GRANT ALL PRIVILEGES ON DATABASE agrotech_historico TO agrotech_user;
\q
```

### **Windows:**

1. **Descargar PostgreSQL:** https://www.postgresql.org/download/windows/
2. **Incluir PostGIS** en la instalación usando Stack Builder
3. **Configurar:**
   ```sql
   -- En pgAdmin o psql:
   CREATE USER agrotech_user WITH PASSWORD 'agrotech_password';
   CREATE DATABASE agrotech_historico OWNER agrotech_user;
   \c agrotech_historico
   CREATE EXTENSION postgis;
   ```

## 🚀 Configuración del Proyecto

### **1. Instalar dependencias Python:**
```bash
# En el entorno virtual del proyecto
pip install psycopg2-binary django-environ

# O desde requirements.txt actualizado
pip install -r requirements.txt
```

### **2. Configurar variables de entorno (.env):**
```env
# Cambiar de SQLite a PostgreSQL
DATABASE_ENGINE=postgresql
DATABASE_NAME=agrotech_historico
DATABASE_USER=agrotech_user
DATABASE_PASSWORD=agrotech_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

### **3. Migrar a PostgreSQL:**
```bash
# 1. Hacer backup de datos existentes (si los hay)
python manage.py dumpdata --natural-foreign --natural-primary > backup_data.json

# 2. Crear nuevas migraciones para PostGIS
python manage.py makemigrations

# 3. Aplicar migraciones
python manage.py migrate

# 4. Restaurar datos (opcional)
python manage.py loaddata backup_data.json

# 5. Crear superusuario
python manage.py createsuperuser
```

## 📊 Beneficios Inmediatos

### **Consultas Espaciales Optimizadas:**
```python
# Ejemplos de lo que ahora puedes hacer:

# 1. Encontrar parcelas cercanas (radio de 10km)
parcelas_cercanas = Parcela.objects.filter(
    geometria__distance_lte=(punto_referencia, D(km=10))
)

# 2. Calcular área exacta automáticamente
parcela.save()  # El área se calcula automáticamente en hectáreas

# 3. Verificar intersecciones
parcelas_superpuestas = Parcela.objects.filter(
    geometria__intersects=nueva_geometria
)

# 4. Búsquedas por contención
parcelas_dentro_zona = Parcela.objects.filter(
    geometria__within=zona_estudio
)
```

### **Rendimiento Comparativo:**
- **SQLite:** Consultas geográficas básicas, sin índices espaciales
- **PostGIS:** Consultas 10-100x más rápidas con índices R-tree automáticos

## 🔄 Migración Gradual

Si prefieres migrar gradualmente:

### **Paso 1: Mantener compatibilidad dual**
```python
# En settings.py - configuración híbrida
if DATABASE_ENGINE == 'postgresql':
    # Usar campos PostGIS nativos
    from informes.models_postgis import *
else:
    # Usar campos text para GeoJSON (actual)
    from informes.models import *
```

### **Paso 2: Script de migración de datos**
```bash
# Script para migrar geometrías de GeoJSON a PostGIS
python manage.py shell

# En el shell de Django:
from django.contrib.gis.geos import GEOSGeometry
import json

for parcela in Parcela.objects.all():
    if parcela.poligono_geojson:
        geojson = json.loads(parcela.poligono_geojson)
        parcela.geometria = GEOSGeometry(json.dumps(geojson))
        parcela.save()
```

## 🛠️ Herramientas Adicionales

### **pgAdmin** (Interfaz gráfica):
```bash
# macOS
brew install --cask pgadmin4

# Ubuntu
sudo apt install pgadmin4
```

### **QGIS** (Visualización GIS):
- Descargar desde: https://qgis.org/
- Conectar a PostgreSQL para visualizar las parcelas

## 🔍 Verificación de Instalación

```bash
# Verificar que PostGIS funciona correctamente
python manage.py shell

>>> from django.contrib.gis.geos import Point, Polygon
>>> from informes.models import Parcela
>>> 
>>> # Crear geometría de prueba
>>> coords = [(-74.3, 4.6), (-74.2, 4.6), (-74.2, 4.5), (-74.3, 4.5), (-74.3, 4.6)]
>>> poly = Polygon(coords)
>>> print(f"Área: {poly.area} unidades cuadradas")
>>> print("✅ PostGIS funcionando correctamente!")
```

## 🚨 Resolución de Problemas

### **Error: "GDAL library not found"**
```bash
# macOS
brew install gdal

# Ubuntu
sudo apt install gdal-bin libgdal-dev

# Agregar a .zshrc o .bashrc
export GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib
```

### **Error de conexión PostgreSQL:**
```bash
# Verificar que PostgreSQL está corriendo
pg_isready

# Verificar puerto
netstat -an | grep 5432

# Reiniciar servicio
brew services restart postgresql@15  # macOS
sudo systemctl restart postgresql    # Ubuntu
```

### **Error de permisos:**
```sql
-- En psql como superusuario:
GRANT ALL PRIVILEGES ON DATABASE agrotech_historico TO agrotech_user;
GRANT ALL ON SCHEMA public TO agrotech_user;
```

## 📈 Siguiente Paso

Una vez configurado PostgreSQL + PostGIS:

```bash
# Ejecutar demo con PostGIS
python demo.py --auto

# El sistema ahora usará:
# ✅ Cálculos de área precisos
# ✅ Índices espaciales para consultas rápidas  
# ✅ Funciones GIS nativas
# ✅ Mejor rendimiento general
```

---

**¡Con PostgreSQL + PostGIS tendrás un sistema de análisis satelital agrícola de nivel profesional!** 🌱🛰️