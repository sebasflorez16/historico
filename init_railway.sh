#!/bin/bash

# Aplicar migraciones de Django
echo "==> Aplicando migraciones de Django..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "==> Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Iniciar el servidor con Gunicorn
echo "==> Iniciando servidor Gunicorn..."
PORT="${PORT:-8000}"
exec gunicorn agrotech_historico.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --access-logfile - --error-logfile -
