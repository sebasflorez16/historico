#!/bin/bash

# Script para actualizar la API key de EOSDA en Railway
# Correo: agrotechdigitalcolombia@gmail.com
# API Key: apk.32451a8331eb39702e5ae49d3ff9488abf0c64314e620874843962e015ca6468

echo "🔑 Actualizando API Key de EOSDA en Railway..."
echo "================================================"
echo ""
echo "📧 Correo asociado: agrotechdigitalcolombia@gmail.com"
echo "🔐 Nueva API Key: apk.32451a8331eb39702e5ae49d3ff9488abf0c64314e620874843962e015ca6468"
echo ""
echo "Ejecutando comando Railway CLI..."
echo ""

# Actualizar la variable de entorno en Railway
railway variables set EOSDA_API_KEY="apk.32451a8331eb39702e5ae49d3ff9488abf0c64314e620874843962e015ca6468"

echo ""
echo "✅ Variable actualizada exitosamente"
echo ""
echo "⚠️  IMPORTANTE: Railway necesita redesplegar para aplicar los cambios"
echo ""
echo "Opciones para aplicar los cambios:"
echo "  1. Redeploy automático: railway up"
echo "  2. Redeploy manual: railway deploy"
echo "  3. Esperar al próximo deploy automático"
echo ""
echo "¿Deseas redesplegar ahora? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Redesplegando aplicación..."
    railway deploy
    echo ""
    echo "✅ Redepliegue completado"
else
    echo ""
    echo "⚠️  Recuerda redesplegar manualmente para aplicar los cambios"
fi

echo ""
echo "================================================"
echo "✅ Proceso completado"
echo ""
echo "Próximos pasos:"
echo "  1. Verificar que el servicio se haya redesplegado correctamente"
echo "  2. Probar la sincronización con EOSDA desde el admin"
echo "  3. Revisar logs: railway logs"
echo ""
