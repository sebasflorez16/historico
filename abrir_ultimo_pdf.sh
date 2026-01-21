#!/bin/bash

# Script para abrir el PDF generado más reciente
# Uso: ./abrir_ultimo_pdf.sh

echo "🔍 Buscando PDF más reciente..."

# Encontrar el PDF más reciente en la carpeta de informes
PDF_PATH=$(ls -t /Users/sebasflorez16/Documents/AgroTech\ Historico/media/informes/*.pdf 2>/dev/null | head -1)

if [ -z "$PDF_PATH" ]; then
    echo "❌ No se encontró ningún PDF en media/informes/"
    exit 1
fi

echo "✅ PDF encontrado: $PDF_PATH"
echo ""
echo "📊 Abriendo PDF para validación visual..."
echo ""
echo "📋 CHECKLIST DE VALIDACIÓN:"
echo "  1. Resumen ejecutivo muestra eficiencia coherente"
echo "  2. Área afectada con 1 decimal (ej: 8.2 ha)"
echo "  3. Tabla de severidad usa 1 decimal"
echo "  4. No hay áreas afectadas > área total"
echo "  5. Eficiencia + % afectado = 100%"
echo ""

# Abrir PDF con aplicación predeterminada
open "$PDF_PATH"

echo "✅ PDF abierto. Revisa el checklist en CHECKLIST_VALIDACION_PDF.md"
