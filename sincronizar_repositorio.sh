#!/bin/bash
# Script para sincronizar completamente el repositorio con el remoto

echo "===================================="
echo "🔄 SINCRONIZACIÓN DE REPOSITORIO"
echo "===================================="

# 1. Obtener todos los cambios del remoto
echo ""
echo "📥 Paso 1: Obteniendo cambios del remoto..."
git fetch --all --prune

# 2. Mostrar el estado actual
echo ""
echo "📊 Paso 2: Estado actual del repositorio..."
git status

# 3. Mostrar las ramas disponibles
echo ""
echo "🌿 Paso 3: Ramas disponibles..."
git branch -a

# 4. Opciones de sincronización
echo ""
echo "===================================="
echo "OPCIONES DE SINCRONIZACIÓN:"
echo "===================================="
echo ""
echo "1️⃣  Para actualizar tu rama actual con origin/main:"
echo "    git pull origin main"
echo ""
echo "2️⃣  Para resetear completamente a origin/main (⚠️ PERDERÁS cambios locales):"
echo "    git reset --hard origin/main"
echo ""
echo "3️⃣  Para cambiar a la rama master:"
echo "    git checkout master"
echo "    git pull origin master"
echo ""
echo "4️⃣  Para ver diferencias con el remoto:"
echo "    git diff origin/main"
echo ""
echo "===================================="

# 5. Mostrar últimos commits
echo ""
echo "📝 Últimos 5 commits en origin/main:"
git log origin/main --oneline -5

echo ""
echo "📝 Últimos 5 commits en origin/master:"
git log origin/master --oneline -5

echo ""
echo "===================================="
echo "✅ Sincronización completada"
echo "===================================="
