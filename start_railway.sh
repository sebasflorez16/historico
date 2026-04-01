#!/bin/bash
# Script de inicialización para Railway
# Se ejecuta ANTES de iniciar el servidor Django

echo "🚀 Iniciando Railway - AgroTech Histórico"

# 1. Descargar datos geográficos si no existen
if [ ! -d "datos_geograficos/red_hidrica" ]; then
    echo "📥 Descargando datos geográficos..."
    python descargar_datos_produccion.py
else
    echo "✅ Datos geográficos ya presentes"
fi

# 2. Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

# 3. Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# 4. Iniciar servidor Gunicorn
echo "🌐 Iniciando servidor..."
gunicorn agrotech_historico.wsgi:application --bind 0.0.0.0:$PORT
