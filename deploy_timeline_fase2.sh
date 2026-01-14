#!/bin/bash

# 🚀 Deploy Script para Timeline Player Fase 2
# Ejecuta este script después de actualizar el código

echo "================================================"
echo "🚀 DEPLOY DE TIMELINE PLAYER - FASE 2"
echo "================================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

echo "1️⃣ Verificando archivos de Fase 2..."
python verificar_timeline_fase2.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Verificación fallida. Revisa los errores antes de continuar."
    exit 1
fi

echo ""
echo "2️⃣ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo ""
echo "3️⃣ Verificando permisos de archivos..."
chmod 644 static/js/timeline/modules/*.js
chmod 644 static/css/timeline_modules.css

echo ""
echo "4️⃣ Limpiando caché del navegador (opcional)..."
echo "   👉 Los usuarios deben refrescar con Ctrl+F5 o Cmd+Shift+R"

echo ""
echo "================================================"
echo "✅ DEPLOY COMPLETADO"
echo "================================================"
echo ""
echo "📝 Próximos pasos:"
echo ""
echo "1. Reiniciar servidor de desarrollo:"
echo "   python manage.py runserver"
echo ""
echo "2. Abrir el timeline en el navegador:"
echo "   http://localhost:8000/parcelas/<ID>/timeline/"
echo ""
echo "3. Verificar en la consola del navegador (F12):"
echo "   - No debe haber errores JavaScript"
echo "   - Deben aparecer mensajes de inicialización de módulos"
echo ""
echo "4. Probar funcionalidades:"
echo "   ✓ Control de velocidad (dropdown)"
echo "   ✓ Transiciones (panel de configuración)"
echo "   ✓ Filtros (panel de configuración)"
echo ""
echo "================================================"
echo "🎉 ¡Fase 2 lista para usar!"
echo "================================================"
