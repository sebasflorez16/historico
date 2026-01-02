# Dockerfile para AgroTech - Optimizado para Railway con GeoDjango
FROM python:3.10-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema para GeoDjango
# GDAL, GEOS, PROJ son necesarios para GeoDjango
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias geoespaciales
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-bin \
    proj-data \
    # PostgreSQL client
    postgresql-client \
    libpq-dev \
    # Utilidades de compilación
    gcc \
    g++ \
    binutils \
    libproj-dev \
    # Limpieza
    && rm -rf /var/lib/apt/lists/*

# Verificar instalación de librerías geoespaciales (debug)
RUN echo "🔍 Verificando instalación de librerías geoespaciales..." && \
    find /usr -name "libgdal.so*" 2>/dev/null | head -5 && \
    find /usr -name "libgeos_c.so*" 2>/dev/null | head -5 && \
    gdal-config --version || echo "⚠️ gdal-config no encontrado"

# Variables de entorno para GDAL
# Configurar rutas para que Python encuentre las librerías geoespaciales
# Nota: Las rutas pueden variar según la distribución, por eso agregamos múltiples
ENV GDAL_CONFIG=/usr/bin/gdal-config \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so \
    LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/lib:$LD_LIBRARY_PATH \
    GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para cachear instalación de dependencias)
COPY requirements.txt .

# Actualizar pip e instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles

# Verificar que Django puede cargar GDAL (diagnóstico)
RUN echo "🧪 Verificando que Django puede importar GDAL..." && \
    python -c "from django.contrib.gis import gdal; print('✅ GDAL cargado correctamente, versión:', gdal.gdal_version())" || \
    echo "⚠️ Warning: GDAL import falló, pero continuando..."

# Recopilar archivos estáticos (se ejecutará en build)
RUN python manage.py collectstatic --noinput || echo "Collectstatic fallido, continuando..."

# Exponer puerto (Railway usa variable $PORT)
EXPOSE ${PORT:-8000}

# Script de inicio
CMD ["sh", "-c", "python manage.py migrate && gunicorn agrotech_historico.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
