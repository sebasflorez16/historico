# 🧪 Tests - AgroTech Histórico

Esta carpeta contiene todos los scripts de prueba del sistema.

## 📋 Índice de Tests

### Tests de APIs y Servicios
- `test_eosda_febrero_2025.py` - Test de API EOSDA con datos reales
- `test_eosda_verano.py` - Test de datos de verano
- `test_weather_api.py` - Test de API meteorológica
- `test_weather_directo.py` - Test directo de clima
- `test_openmeteo.py` - Test de integración Open-Meteo
- `test_field_analytics.py` - Test de análisis de campos
- `test_field_imagery_api.py` - Test de API de imágenes satelitales

### Tests de Funcionalidades
- `test_generacion_informe.py` - Test completo de generación de informes PDF
- `test_informe_simple.py` - Test simplificado de generación de informes
- `test_auth_dual.py` - Test de sistema de autenticación dual
- `test_cache_optimizado.py` - Test de sistema de caché
- `test_descarga_imagen.py` - Test de descarga de imágenes satelitales
- `test_procesamiento_datos.py` - Test de procesamiento de datos
- `test_views_completo.py` - Test completo de vistas Django

### Tests de Utilidades
- `test_endpoints.py` - Test de endpoints de API
- `test_formatos_indices.py` - Test de formatos de índices
- `test_rangos_fechas.py` - Test de selector de rangos de fechas
- `test_calculo_meses.py` - Test de cálculos de períodos mensuales

## 🚀 Cómo Ejecutar los Tests

### Test Individual
```bash
cd /Users/sebasflorez16/Documents/AgroTech\ Historico/historical
python tests/test_informe_simple.py
```

### Test con Django Shell
```bash
python manage.py shell < tests/test_eosda_febrero_2025.py
```

## 📝 Notas

- Los tests están configurados para Django y requieren que el proyecto esté correctamente configurado
- Algunos tests requieren credenciales de API (EOSDA, Open-Meteo)
- Los tests de generación de informes crean archivos PDF en `media/informes/`

## 🔧 Mantenimiento

- Mantener los tests actualizados con los cambios del sistema
- Agregar nuevos tests para nuevas funcionalidades
- Documentar dependencias específicas de cada test
