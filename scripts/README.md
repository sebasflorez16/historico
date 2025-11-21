# 🔧 Scripts - AgroTech Histórico

Esta carpeta contiene scripts de utilidad, mantenimiento y desarrollo.

## 📋 Categorías

### 🐛 Scripts de Debug
- `debug_eosda.py` - Depuración de API EOSDA
- `debug_descarga_imagen.py` - Debug de descarga de imágenes
- `debug_task_status.py` - Debug de estado de tareas
- `check_task.py` - Verificar estado de tareas
- `consultar_tarea.py` - Consultar tareas específicas
- `quick_check.py` - Verificación rápida del sistema

### 🔄 Scripts de Actualización
- `actualizar_datos_clima_todas_parcelas.py` - Actualizar clima de todas las parcelas
- `actualizar_etiquetas_clima.py` - Actualizar etiquetas de datos climáticos
- `sincronizar_lote4.py` - Sincronizar lote específico
- `fix_etiquetas_rapido.py` - Corrección rápida de etiquetas

### 🔍 Scripts de Análisis
- `diagnostico_datos_mensuales.py` - Diagnóstico de datos mensuales
- `ver_estructura_datos.py` - Ver estructura de datos
- `ver_respuesta_completa.py` - Ver respuestas completas de API
- `listar_campos_eosda.py` - Listar campos en EOSDA

### 🛠️ Scripts de Mantenimiento
- `configurar_db.py` - Configuración de base de datos
- `limpiar_datos.py` - Limpieza de datos
- `demo.py` - Script de demostración

### 📝 Scripts de Documentación
- `CORRECCION_SPINNER_CACHE.py` - Documentación de corrección de spinner
- `GALERIA_IMPLEMENTADA.py` - Documentación de galería
- `RESUMEN_CORRECCIONES.py` - Resumen de correcciones

## 🚀 Uso General

### Ejecutar un script
```bash
cd /Users/sebasflorez16/Documents/AgroTech\ Historico/historical
python scripts/nombre_script.py
```

### Con Django configurado
```bash
python manage.py shell < scripts/nombre_script.py
```

## ⚠️ Advertencias

- Algunos scripts modifican datos en la base de datos
- Hacer backup antes de ejecutar scripts de mantenimiento
- Revisar el código antes de ejecutar en producción
- Algunos scripts requieren permisos de superusuario

## 📚 Documentación

Cada script tiene documentación interna. Para ver:
```bash
head -20 scripts/nombre_script.py
```
