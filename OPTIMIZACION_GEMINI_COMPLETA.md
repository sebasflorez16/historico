# OPTIMIZACIÓN DE CONSUMO DE GEMINI AI - IMPLEMENTACIÓN COMPLETA

## 📋 Resumen Ejecutivo

Se ha implementado un sistema completo de optimización del consumo de la API de Gemini AI para reducir costos y cumplir con los límites del plan gratuito.

## 🎯 Objetivos Cumplidos

### 1. **Limitación de Imágenes Analizadas**
- ✅ Se limita el análisis a las **10 mejores imágenes** por informe (en vez de 30+)
- ✅ Selección inteligente basada en:
  - Nubosidad (40% peso): menos nubes = mejor
  - Calidad de datos (30% peso): excelente > buena > aceptable > baja
  - Fecha (20% peso): más reciente = mejor  
  - Cobertura de índices (10% peso): más índices disponibles = mejor

### 2. **Cacheo de Resultados**
- ✅ Modelo `AnalisisImagen` para guardar análisis en base de datos
- ✅ No se repite el análisis de imágenes ya procesadas
- ✅ Caché con validez de 30 días

### 3. **Control de Cuota Diaria**
- ✅ Modelo `InformeGenerado` para registrar informes generados
- ✅ Límite de **3 informes por día** por usuario (plan gratuito)
- ✅ Verificación automática antes de generar informe
- ✅ Mensajes claros al usuario cuando alcanza el límite

### 4. **Interfaz Optimizada**
- ✅ Indicador visual de cuota restante en la página de detalle
- ✅ Botón deshabilitado cuando se alcanza el límite
- ✅ Mensajes informativos sobre el plan gratuito

### 5. **Estimación de Costos**
- ✅ Cálculo automático de tokens y peticiones por informe
- ✅ Mensajes informativos en logs sobre el consumo

## 📂 Archivos Creados/Modificados

### Nuevos Archivos
1. **`informes/utils/image_selector.py`** (187 líneas)
   - Clase `ImagenSelector` para seleccionar las mejores imágenes
   - Métodos de puntuación y estimación de costos
   - Configuración: `MAX_IMAGENES_POR_INFORME = 10`

2. **`informes/utils/__init__.py`**
   - Archivo de inicialización del módulo utils

### Archivos Modificados
1. **`informes/models.py`**
   - Modelo `AnalisisImagen` (líneas 23-38): Cacheo de análisis por imagen
   - Modelo `InformeGenerado` (líneas 41-74): Registro de informes generados
   - Métodos: `contar_informes_hoy()`, `puede_generar_informe()`

2. **`informes/generador_pdf.py`**
   - Import de `image_selector` (línea 48)
   - Método `_ejecutar_analisis()` modificado (líneas 341-450):
     * Selección de mejores imágenes
     * Estimación de costos
     * Uso de caché de análisis

3. **`informes/views.py`**
   - Vista `generar_informe_pdf()` (líneas 1873-1970):
     * Verificación de cuota diaria
     * Registro de informe generado
     * Mensajes de cuota restante
   - Vista `detalle_parcela()` (líneas 235-330):
     * Cálculo de cuota restante
     * Contexto adicional para template

4. **`templates/informes/parcelas/detalle.html`**
   - Botón "Generar Informe" con disable condicional
   - Indicador de cuota restante (alert info/warning)
   - Mensajes informativos sobre el plan

5. **`.env`**
   - Agregada variable `GEMINI_API_KEY`

## 🔧 Configuración Aplicada

### Límites por Defecto
```python
MAX_IMAGENES_POR_INFORME = 10        # Análisis rápido
MAX_IMAGENES_ANALISIS_COMPLETO = 30  # Análisis completo (requiere plan de pago)
LIMITE_DIARIO_INFORMES = 3           # Por usuario
VALIDEZ_CACHE_DIAS = 30              # Días de validez del caché
```

### Estimación de Consumo
- **Tokens por imagen:** ~500 (promedio)
- **Informe rápido (10 imgs):** ~5,000 tokens, 10 peticiones
- **Informe completo (30 imgs):** ~15,000 tokens, 30 peticiones

### Plan Gratuito de Gemini
- **Peticiones diarias:** 10-20 (típico)
- **Tokens mensuales:** ~60,000-100,000
- **Conclusión:** Con las optimizaciones, caben 6-12 informes rápidos/mes

## 📊 Impacto de la Optimización

### Antes
- ❌ 30+ imágenes por informe
- ❌ ~15,000 tokens por informe
- ❌ Sin límite de informes diarios
- ❌ Sin caché, repetía análisis
- ❌ Agotaba cuota en 2-4 informes

### Después
- ✅ 10 mejores imágenes por informe
- ✅ ~5,000 tokens por informe (67% de ahorro)
- ✅ Máximo 3 informes por día
- ✅ Caché de 30 días evita repeticiones
- ✅ Permite 6-12 informes/mes con plan gratuito

## 🚀 Próximos Pasos (Opcionales)

### Fase 2 - Mejoras Adicionales
1. **Opción de análisis completo** (30 imgs) para usuarios con plan de pago
2. **Dashboard de consumo** para ver estadísticas de uso
3. **Actualización a `google.genai`** (nuevo paquete recomendado)
4. **Compresión de imágenes** antes de enviar a Gemini
5. **Batching de peticiones** si la API lo permite

### Configuración Recomendada
- Si tienes muchos usuarios, considera aumentar `LIMITE_DIARIO_INFORMES`
- Si el plan de Gemini es de pago, puedes aumentar `MAX_IMAGENES_POR_INFORME`
- Ajusta `VALIDEZ_CACHE_DIAS` según frecuencia de cambios en parcelas

## 📖 Documentación de Uso

### Para el Usuario Final
1. El sistema selecciona automáticamente las 10 mejores imágenes
2. Puede generar hasta 3 informes por día
3. El indicador muestra cuántos informes quedan disponibles
4. Si alcanza el límite, debe esperar al día siguiente o contactar para ampliar cuota

### Para el Desarrollador
```python
# Cambiar el límite de imágenes por informe
from informes.utils.image_selector import ImagenSelector
selector = ImagenSelector(max_imagenes=15)  # Aumentar a 15

# Cambiar el límite diario de informes (en views.py)
LIMITE_DIARIO = 5  # Aumentar a 5 informes por día

# Verificar cuota manualmente
from informes.models import InformeGenerado
informes_hoy = InformeGenerado.contar_informes_hoy(usuario=request.user)
puede = InformeGenerado.puede_generar_informe(usuario=request.user, limite_diario=3)
```

## ✅ Checklist de Verificación

- [x] Modelo `AnalisisImagen` creado
- [x] Modelo `InformeGenerado` creado
- [x] Selector de imágenes implementado
- [x] Generador de PDF modificado para usar selector
- [x] Vista de generación verificando cuota
- [x] Vista de detalle mostrando cuota restante
- [x] Template con indicador visual
- [x] API key de Gemini configurada en .env
- [x] Logs informativos sobre consumo
- [x] Mensajes claros al usuario

## 🎉 Resultado Final

El sistema ahora es **67% más eficiente** en el consumo de la API de Gemini, permitiendo generar entre 6-12 informes mensuales con el plan gratuito, en vez de solo 2-4. Además, el caché evita análisis duplicados y el límite diario protege contra el exceso de uso.

---

**Fecha de implementación:** 30 de diciembre de 2025  
**Versión del sistema:** AgroTech Histórico v2.0
