# 📂 Organización de Archivos - AgroTech Histórico

**Fecha:** 21 de noviembre de 2025
**Estado:** ✅ Completado

## 🎯 Objetivo

Organizar todos los archivos sueltos (tests, scripts, documentación) en una estructura clara y mantenible.

## 📊 Resumen de Cambios

### Antes
```
historical/
├── ❌ 18+ archivos test_*.py sueltos
├── ❌ 20+ scripts *.py sueltos
├── ❌ 15+ archivos *.md sueltos
└── ❌ Difícil de navegar y mantener
```

### Después
```
historical/
├── ✅ tests/              (18 archivos organizados)
├── ✅ scripts/            (20 archivos organizados)
├── ✅ docs/               (24 documentos organizados)
│   ├── sprints/
│   ├── sistema/
│   ├── frontend/
│   ├── correcciones/
│   └── instalacion/
└── ✅ README.md actualizado
```

## 📁 Estructura Detallada

### 🧪 tests/ (18 archivos)

**Tests de APIs y Servicios:**
- `test_eosda_febrero_2025.py` - Test de API EOSDA
- `test_weather_api.py` - Test de API meteorológica
- `test_openmeteo.py` - Test Open-Meteo
- `test_field_analytics.py` - Test análisis de campos
- `test_field_imagery_api.py` - Test imágenes satelitales

**Tests de Funcionalidades:**
- `test_generacion_informe.py` - Test generación informes
- `test_informe_simple.py` - Test simplificado
- `test_auth_dual.py` - Test autenticación
- `test_cache_optimizado.py` - Test caché
- `test_descarga_imagen.py` - Test descarga imágenes

**Tests de Utilidades:**
- `test_endpoints.py` - Test endpoints
- `test_formatos_indices.py` - Test formatos
- `test_rangos_fechas.py` - Test rangos
- `test_procesamiento_datos.py` - Test procesamiento
- `test_views_completo.py` - Test vistas

### 🔧 scripts/ (20 archivos)

**Scripts de Debug:**
- `debug_eosda.py`
- `debug_descarga_imagen.py`
- `debug_task_status.py`
- `check_task.py`
- `quick_check.py`

**Scripts de Actualización:**
- `actualizar_datos_clima_todas_parcelas.py`
- `actualizar_etiquetas_clima.py`
- `sincronizar_lote4.py`
- `fix_etiquetas_rapido.py`

**Scripts de Análisis:**
- `diagnostico_datos_mensuales.py`
- `ver_estructura_datos.py`
- `ver_respuesta_completa.py`
- `listar_campos_eosda.py`

**Scripts de Mantenimiento:**
- `configurar_db.py`
- `limpiar_datos.py`
- `demo.py`

### 📚 docs/ (24 documentos)

**docs/sprints/** (4 documentos)
- `SPRINT2_COMPLETADO.md`
- `SPRINT3_4_COMPLETADOS.md`
- `MEJORAS_COMPLETADAS.md`
- `CONFIGURACION_COMPLETADA.md`

**docs/sistema/** (6 documentos)
- `FLUJO_IMAGENES_SATELITALES.md`
- `SISTEMA_INFORMES_IMPLEMENTADO.md`
- `SISTEMA_RANGOS_FECHAS.md`
- `SISTEMA_INFORMES_COMPLETO_PROPUESTA.md`
- `RESUMEN_FINAL.md`
- `RESUMEN_TOTAL.md`

**docs/frontend/** (7 documentos)
- `GLASMORFISMO_AGROTECH_README.md`
- `NEUMORFISMO_AGROTECH_README.md`
- `NEUMORFISMO_LUMINOSO_COMPLETO.md`
- `INICIO_RAPIDO_GLASMORFISMO.md`
- `INICIO_RAPIDO_NEUMORFISMO.md`
- `RESUMEN_EJECUTIVO_GLASMORFISMO.md`
- `RESUMEN_EJECUTIVO_NEUMORFISMO.md`

**docs/correcciones/** (5 documentos)
- `CORRECCION_CDN_URGENTE.md`
- `CORRECCION_DASHBOARD_EOSDA.md`
- `GUIA_CORRECCION_ERRORES.md`
- `GUIA_LOGOS_AGROTECH.md`
- `VERIFICACION_FINAL_CDN.md`

**docs/instalacion/** (1 documento)
- `INSTALACION_POSTGRESQL.md`

## 📝 Documentación Agregada

Cada carpeta ahora incluye su propio README.md:

1. **tests/README.md** - Guía de tests
2. **scripts/README.md** - Guía de scripts
3. **docs/README.md** - Índice de documentación

## 🔍 Búsqueda Rápida

### Por Tipo de Archivo
```bash
# Ver todos los tests
ls tests/

# Ver todos los scripts
ls scripts/

# Ver documentación por categoría
ls docs/sistema/
ls docs/frontend/
ls docs/correcciones/
```

### Por Funcionalidad
```bash
# Tests de API EOSDA
ls tests/*eosda*.py

# Scripts de actualización
ls scripts/actualizar*.py

# Documentación de sprints
ls docs/sprints/
```

## ✅ Beneficios

1. **📍 Navegación Clara**: Fácil encontrar archivos por categoría
2. **🔧 Mantenimiento**: Mejor organización para updates
3. **📚 Documentación**: Cada carpeta tiene su README
4. **🔄 Escalabilidad**: Fácil agregar nuevos archivos
5. **👥 Colaboración**: Estructura clara para el equipo

## 🚀 Próximos Pasos

1. ✅ **Organización completada**
2. ✅ **READMEs creados**
3. ✅ **README.md principal actualizado**
4. 📋 Mantener estructura en futuros desarrollos
5. 📋 Agregar nuevos tests en `tests/`
6. 📋 Agregar nuevos scripts en `scripts/`
7. 📋 Documentar cambios en `docs/`

## 💡 Convenciones

### Nombrado de Archivos

**Tests:**
- `test_<funcionalidad>.py` → va en `tests/`
- Ejemplos: `test_eosda.py`, `test_informe.py`

**Scripts:**
- `<accion>_<objeto>.py` → va en `scripts/`
- Ejemplos: `actualizar_datos.py`, `debug_api.py`

**Documentación:**
- Sprints: `SPRINT<n>_*.md` → `docs/sprints/`
- Sistema: `SISTEMA_*.md` → `docs/sistema/`
- Frontend: `*MORFISMO*.md` → `docs/frontend/`
- Correcciones: `CORRECCION_*.md` → `docs/correcciones/`
- Guías: `GUIA_*.md` → `docs/correcciones/`

## 📞 Soporte

Para preguntas sobre la organización:
- Ver README de cada carpeta
- Consultar `docs/README.md` para índice completo
- Revisar este documento para convenciones

---

**Organizado por:** Sistema de Gestión de Archivos AgroTech
**Fecha de actualización:** 21/11/2025
