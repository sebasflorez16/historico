# SISTEMA DE GENERACIÓN DE INFORMES PDF - AGROTECH

## ARCHIVO OFICIAL EN PRODUCCIÓN

### ✅ `generador_pdf.py` (30 KB)
**Clase:** `GeneradorInformeTecnico`  
**Estado:** ACTIVO EN PRODUCCIÓN  
**Usado por:** 
- `views.py` - Vista principal de generación de informes
- Todos los tests en `/tests/`
- Scripts de prueba en raíz del proyecto

**Características:**
- Diseño profesional sin emojis
- Sistema de estilos tipográficos jerárquico
- Paleta de colores corporativa AgroTech
- Motor de análisis agrícola integrado
- Visualizaciones científicas (matplotlib/seaborn)
- Header/Footer profesional con logos
- Documento técnico auditable y reproducible

**Secciones del informe:**
1. Portada corporativa
2. Índice de contenidos
3. Metodología y fuentes de datos
4. Resumen ejecutivo
5. Información de parcela
6. Análisis de índices (NDVI, NDMI, SAVI)
7. Análisis de tendencias temporales
8. Recomendaciones agronómicas
9. Datos tabulados completos
10. Anexo: Galería de imágenes satelitales

---

## ARCHIVOS ELIMINADOS (6 Enero 2026)

### ❌ `generador_pdf_backup.py` (1684 líneas)
**Razón:** Backup del archivo corrupto con código mezclado

### ❌ `generador_pdf_profesional.py` (915 líneas)
**Razón:** Intento incompleto de implementación profesional, nunca completado

### ❌ `INSTRUCCIONES_PDF_PROFESIONAL.md`
**Razón:** Archivo temporal de instrucciones

---

## ARCHIVOS RENOMBRADOS COMO OBSOLETOS

### ⚠️ `services/generador_pdf_OBSOLETO_EOSDA.py` (37 KB)
**Estado:** OBSOLETO - Solo para referencia histórica  
**Razón:** Sistema antiguo que consultaba EOSDA API directamente  
**Usado por:** Solo scripts/demo.py antiguos (no en producción)

**NOTA:** Este archivo se mantiene renombrado por si se necesita consultar
la lógica antigua de integración directa con EOSDA, pero NO se debe usar
en nuevos desarrollos.

---

## OTROS GENERADORES (NO RELACIONADOS CON PDF DE USUARIO)

### ℹ️ `motor_analisis/reporte_tecnico.py`
**Propósito:** Generación de reportes técnicos internos del motor de análisis  
**NO** es un generador de PDFs para usuarios finales  
**Estado:** MANTENER - Uso interno del motor

---

## GUÍA DE USO

### Generar informe PDF:

```python
from informes.generador_pdf import GeneradorInformeTecnico

# Instanciar generador
generador = GeneradorInformeTecnico()

# Generar informe para una parcela
ruta_pdf = generador.generar_informe_completo(
    parcela_id=5,
    meses_atras=12,  # Ventana temporal de análisis
    output_path=None  # Opcional, se auto-genera si es None
)

print(f"Informe generado en: {ruta_pdf}")
```

### Desde las vistas (views.py):

```python
from .generador_pdf import GeneradorInformeTecnico

def generar_informe_parcela(request, parcela_id):
    generador = GeneradorInformeTecnico()
    pdf_path = generador.generar_informe_completo(parcela_id=parcela_id)
    # ... resto de la lógica
```

---

## ESTRUCTURA DEL CÓDIGO

### Métodos principales:

```
GeneradorInformeTecnico
├── __init__()                              # Configuración inicial
├── generar_informe_completo()              # MÉTODO PRINCIPAL
│
├── PREPARACIÓN DE DATOS
│   ├── _calcular_fecha_inicio()
│   └── _preparar_datos_analisis()
│
├── MOTOR DE ANÁLISIS
│   └── _ejecutar_analisis_completo()
│       ├── Análisis NDVI
│       ├── Análisis NDMI
│       ├── Análisis SAVI
│       ├── Detección de tendencias
│       └── Generación de recomendaciones
│
├── VISUALIZACIONES
│   └── _generar_graficos_profesionales()
│       ├── _grafico_evolucion_temporal()
│       ├── _grafico_comparativo_medias()
│       ├── _grafico_dispersion_tendencia()
│       └── _grafico_mapa_calor()
│
├── SECCIONES DEL PDF
│   ├── _crear_portada_profesional()
│   ├── _crear_indice_contenidos()
│   ├── _crear_seccion_metodologia()
│   ├── _crear_resumen_ejecutivo_profesional()
│   ├── _crear_info_parcela_profesional()
│   ├── _crear_seccion_analisis_ndvi()
│   ├── _crear_seccion_analisis_ndmi()
│   ├── _crear_seccion_analisis_savi()
│   ├── _crear_seccion_tendencias_profesional()
│   ├── _crear_seccion_recomendaciones_profesional()
│   ├── _crear_tabla_datos_profesional()
│   └── _crear_galeria_imagenes_profesional()
│
└── DISEÑO
    ├── _crear_estilos_tipograficos()
    └── _crear_header_footer()
```

---

## ESTADO ACTUAL (6 Enero 2026)

- ✅ Archivo principal limpio y optimizado
- ✅ Archivos obsoletos eliminados
- ✅ Documentación actualizada
- ⚠️ **PENDIENTE:** Completar métodos faltantes en `generador_pdf.py`

### Métodos implementados (733 líneas):
- ✓ Configuración y estilos
- ✓ Header/Footer
- ✓ Método principal `generar_informe_completo()`
- ✓ Preparación de datos

### Métodos pendientes de implementación:
- ⏳ `_ejecutar_analisis_completo()`
- ⏳ `_generar_graficos_profesionales()` y sub-gráficos
- ⏳ Todas las secciones del PDF (_crear_portada_, _crear_seccion_*, etc.)

---

## PRÓXIMOS PASOS

1. **Completar implementación** de métodos faltantes en `generador_pdf.py`
2. **Adaptar funciones** del backup eliminado (sin emojis, estilo profesional)
3. **Testing completo** con parcela real
4. **Documentar** cada sección con comentarios técnicos
5. **Optimizar** generación de gráficos para mejor rendimiento

---

**Última actualización:** 6 de Enero de 2026  
**Mantenedor:** Equipo AgroTech
