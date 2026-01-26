# Verificación Legal de Restricciones Ambientales (Opcional)

## 📋 Descripción

Sistema opcional de verificación de restricciones legales y ambientales para parcelas agrícolas en Colombia, basado en datos geográficos oficiales del gobierno colombiano.

### ✨ Características

- ✅ **Verificación con datos oficiales 2026**
- 🗺️ **Mapa visual** de restricciones (como el mapa de intervención)
- 📄 **Sección completa en PDF** (4-6 páginas adicionales)
- 🔍 **4 tipos de restricciones verificadas**:
  - Retiros hídricos (Decreto 1541/1978)
  - Áreas protegidas RUNAP
  - Resguardos indígenas
  - Páramos

---

## 🚀 Uso Rápido

### 1. Activar verificación legal en una parcela

```python
from informes.models import Parcela

parcela = Parcela.objects.get(id=1)
parcela.incluir_verificacion_legal = True  # Activar opción
parcela.save()
```

### 2. Generar informe con verificación legal

El sistema **detecta automáticamente** si la parcela tiene `incluir_verificacion_legal=True` y agrega la sección al PDF sin modificar nada del código actual.

```python
from informes.generador_pdf import GeneradorPDFProfesional

generador = GeneradorPDFProfesional()
pdf_path = generador.generar_informe_completo(
    parcela_id=1,
    meses_atras=14
)
# Si incluir_verificacion_legal=True, el PDF tendrá 4-6 páginas adicionales
```

### 3. Test de verificación en terminal

```bash
# Listar parcelas disponibles
python test_verificacion_legal_terminal.py --listar

# Verificar una parcela
python test_verificacion_legal_terminal.py --parcela 1

# Verificar múltiples parcelas
python test_verificacion_legal_terminal.py --parcela 1 --parcela 2
```

---

## 🗺️ Mapa de Restricciones Legales

El sistema genera un mapa visual similar al mapa de intervención, mostrando:

- **Polígono de la parcela** (verde claro)
- **Retiros hídricos** (rojo/naranja/amarillo según severidad)
- **Áreas protegidas** (púrpura)
- **Resguardos indígenas** (naranja tierra)
- **Páramos** (azul claro)
- **Coordenadas GPS** en las 4 esquinas para navegación en campo

### Ejemplo de uso del generador de mapas:

```python
from generador_mapa_restricciones_legales import generar_mapa_restricciones_legales
from informes.models import Parcela
from pathlib import Path

parcela = Parcela.objects.get(id=1)

# Ejecutar verificación (resultado tiene restricciones encontradas)
from verificador_legal import VerificadorRestriccionesLegales
verificador = VerificadorRestriccionesLegales()
resultado = verificador.verificar_parcela(
    parcela_id=parcela.id,
    geometria_parcela=parcela.geometria,
    nombre_parcela=parcela.nombre
)

# Generar mapa
mapa_path = generar_mapa_restricciones_legales(
    geometria_parcela=parcela.geometria,
    restricciones=resultado.restricciones_encontradas,
    verificacion_completa={
        'area_total_ha': resultado.area_total_ha,
        'area_cultivable_ha': resultado.area_cultivable_ha,
        'cumple_normativa': resultado.cumple_normativa
    },
    output_dir=Path('media/temp'),
    parcela_nombre=parcela.nombre
)

print(f"Mapa generado: {mapa_path}")
```

---

## 📊 Datos Oficiales Utilizados

El sistema utiliza **SOLO fuentes oficiales** del gobierno colombiano:

| Fuente | Organización | Dataset |
|--------|--------------|---------|
| **RUNAP** | Parques Nacionales | 1,829 áreas protegidas |
| **Red Hídrica** | IGAC/IDEAM | 316 elementos zonificación |
| **Resguardos** | ANT | Resguardos indígenas formalizados |
| **Páramos** | MinAmbiente | Delimitación oficial páramos |

### URLs de datos:

- Zonificación hidrográfica: https://www.datos.gov.co/api/geospatial/5kjg-nuda
- RUNAP API: http://mapas.parquesnacionales.gov.co/services/pnn/ows
- Resguardos: ANT ArcGIS Open Data
- Páramos: MinAmbiente SIAC/Geonetwork

---

## 📁 Archivos del Sistema

```
historico/
├── verificador_legal.py                        # Motor de verificación (650 líneas)
├── acceso_datos_hibrido.py                     # Acceso a APIs y archivos (400 líneas)
├── pdf_verificacion_legal.py                   # Generación de sección PDF (380 líneas)
├── generador_mapa_restricciones_legales.py     # Mapa visual con matplotlib (550 líneas)
├── test_verificacion_legal_terminal.py         # Test en terminal (260 líneas)
├── test_pdf_verificacion_con_mapa.py           # Test de PDF completo
├── descargar_necesarios.py                     # Descarga de datos oficiales
│
├── datos_geograficos/                          # Datos oficiales descargados
│   ├── red_hidrica/                            # Zonificación hidrográfica (12MB)
│   │   └── geo_export_*.shp                    # 316 elementos
│   ├── runap/                                  # Áreas protegidas (si se descarga)
│   ├── ant/                                    # Resguardos indígenas (si se descarga)
│   └── ideam/                                  # Páramos (si se descarga)
│
└── informes/migrations/
    └── 0029_parcela_verificacion_legal.py      # Migración DB (5 campos nuevos)
```

---

## 🔧 Instalación

### 1. Instalar dependencias

```bash
# Activar entorno conda
conda activate agro-rest

# Instalar GeoPandas (ya instalado)
pip install geopandas matplotlib
```

### 2. Aplicar migración de base de datos

```bash
python manage.py migrate informes
```

Esto agrega 5 campos nuevos al modelo `Parcela`:

- `incluir_verificacion_legal` (Boolean, default=False)
- `verificacion_legal_fecha` (DateTime)
- `verificacion_legal_resultado` (JSON)
- `cumple_normativa` (Boolean)
- `area_cultivable_legal_ha` (Float)

### 3. Descargar datos geográficos oficiales

```bash
# Descargar datos necesarios
python descargar_necesarios.py
```

Esto descarga:
- ✅ Zonificación hidrográfica (~12MB)
- ⚠️ Resguardos y páramos requieren descarga manual (URLs en el script)

---

## 🎯 Resultados de Verificación

### Ejemplo de salida JSON:

```json
{
    "parcela_id": 1,
    "area_total_ha": 69.82,
    "area_cultivable_ha": 0.00,
    "area_restringida_ha": 69.82,
    "porcentaje_restringido": 100.0,
    "cumple_normativa": false,
    "restricciones_encontradas": [
        {
            "tipo": "retiro_hidrico",
            "subtipo": "quebrada",
            "retiro_minimo_m": 30,
            "area_afectada_ha": 69.82,
            "nombre": "Sin nombre",
            "normativa": "Decreto 1541/1978 Art. 83",
            "severidad": "ALTA"
        }
    ],
    "fecha_verificacion": "2026-01-26T09:43:25",
    "advertencias": [
        "Áreas protegidas no cargadas - verificación incompleta"
    ]
}
```

---

## 📄 Integración con PDF Actual

### ✅ **SIN MODIFICAR NADA DEL FLUJO ACTUAL**

El sistema de verificación legal es **100% opcional** y **no afecta** el PDF existente:

1. Si `parcela.incluir_verificacion_legal = False` (default):
   - PDF se genera normal (sin cambios)
   - Sin verificación legal
   - Sin mapa de restricciones

2. Si `parcela.incluir_verificacion_legal = True`:
   - PDF se genera con 4-6 páginas adicionales al final
   - Incluye mapa visual de restricciones
   - Incluye tabla de restricciones
   - Incluye marco legal y recomendaciones

### Código de integración (en `generador_pdf.py`):

```python
# Al final de generar_informe_completo()
if parcela.incluir_verificacion_legal:
    from pdf_verificacion_legal import agregar_seccion_verificacion_legal
    from verificador_legal import VerificadorRestriccionesLegales
    
    # Ejecutar verificación
    verificador = VerificadorRestriccionesLegales()
    verificador.cargar_red_hidrica()
    verificador.cargar_areas_protegidas()
    # ... cargar otras capas
    
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,
        nombre_parcela=parcela.nombre
    )
    
    # Agregar sección al PDF (incluye mapa automáticamente)
    agregar_seccion_verificacion_legal(
        story=story,
        resultado_verificacion=resultado,
        styles=styles,
        parcela=parcela  # Para generar mapa
    )
    
    # Guardar resultado en DB
    parcela.verificacion_legal_resultado = resultado.to_dict()
    parcela.cumple_normativa = resultado.cumple_normativa
    parcela.area_cultivable_legal_ha = resultado.area_cultivable_ha
    parcela.verificacion_legal_fecha = datetime.now()
    parcela.save()
```

---

## ⚖️ Marco Legal

El sistema verifica cumplimiento de:

- **Decreto 2811/1974**: Código de Recursos Naturales
- **Decreto 1541/1978 Art. 83**: Retiros hídricos (30-100m)
- **Ley 99/1993**: Sistema Nacional Ambiental (SINA)
- **Ley 1930/2018**: Protección de páramos
- **Decreto 2164/1995**: Resguardos indígenas

### ⚠️ Sanciones por incumplimiento:

- Multas hasta 5.000 SMMLV
- Cierre temporal o definitivo de actividad
- Responsabilidad penal según gravedad

---

## 🧪 Tests Disponibles

### 1. Test en terminal (con datos reales):

```bash
python test_verificacion_legal_terminal.py --parcela 1
```

Salida:
```
================================================================================
🌿 VERIFICADOR DE RESTRICCIONES LEGALES
================================================================================

📥 Cargando capas geográficas...
✅ Red hídrica cargada: 316 elementos
⚠️  Áreas protegidas no encontradas
...

📋 REPORTE DE VERIFICACIÓN:
📍 Parcela ID: 1
📊 Área total: 69.82 ha
✅ Área cultivable: 0.00 ha
⚠️  Área restringida: 69.82 ha (100.0%)
❌ NO CUMPLE - 1 RESTRICCIONES ENCONTRADAS
```

### 2. Test de PDF con mapa:

```bash
python test_pdf_verificacion_con_mapa.py
```

Genera: `test_verificacion_legal_mapa_parcela_1.pdf` (5 páginas, ~277KB)

---

## 🌟 Ventajas del Mapa Visual

Similar al mapa de intervención existente:

1. **Coordenadas GPS reales** en las 4 esquinas
2. **Navegación en campo** con aplicaciones móviles
3. **Identificación visual** de restricciones
4. **Profesional y claro** para clientes
5. **Geo-referenciado** para precisión

---

## 📞 Soporte

- Documentación completa: `/docs/sistema/verificacion_legal/`
- Ejemplos de uso: `test_*.py`
- Marco legal: `pdf_verificacion_legal.py` (líneas 220-260)

---

## ⚙️ Configuración Avanzada

### Cambiar retiros mínimos:

```python
# En verificador_legal.py, línea 80
RETIROS_MINIMOS = {
    'rio_principal': 100,      # metros
    'quebrada': 30,            # metros
    'nacimiento': 100,         # metros (radial)
}
```

### Personalizar mapa:

```python
# En generador_mapa_restricciones_legales.py
# Línea 65: Cambiar colores
color = '#E74C3C'  # Rojo para retiros hídricos
alpha = 0.4        # Transparencia

# Línea 45: Ajustar tamaño de figura
fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
```

---

**Última actualización:** 26 enero 2026  
**Versión del sistema:** 1.0  
**Estado:** Producción ✅
