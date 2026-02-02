#!/bin/bash
# Script para iniciar servidor y probar Informe Legal PDF

echo "════════════════════════════════════════════════════════════════════"
echo "🚀 INICIAR SERVIDOR DE DESARROLLO - TEST INFORME LEGAL PDF"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 INSTRUCCIONES:"
echo ""
echo "1️⃣  El servidor se iniciará en: http://localhost:8000"
echo ""
echo "2️⃣  Accede a la parcela #6 en tu navegador:"
echo "    👉 http://localhost:8000/informes/parcelas/6/"
echo ""
echo "3️⃣  Haz clic en el botón: ⚖️ Informe Legal"
echo ""
echo "4️⃣  El navegador descargará el PDF automáticamente"
echo ""
echo "5️⃣  Abre el PDF y verifica:"
echo "    ✅ 3 mapas profesionales (Departamental, Municipal, Influencia Legal)"
echo "    ✅ Tabla de restricciones"
echo "    ✅ Análisis de proximidad"
echo "    ✅ Recomendaciones legales"
echo ""
echo "═══════════════════════════════════════════════════════════════════="
echo ""
echo "⏳ Iniciando servidor Django..."
echo ""

# Iniciar servidor
python manage.py runserver
