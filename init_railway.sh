#!/bin/bash

# Aplicar migraciones de Django
echo "==> Aplicando migraciones de Django..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "==> Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar el servidor con Gunicorn
echo "==> Iniciando servidor Gunicorn..."
exec gunicorn agrotech_historico.wsgi:application --bind 0.0.0.0:8000 --timeout 120
