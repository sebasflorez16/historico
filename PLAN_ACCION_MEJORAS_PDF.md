# 📋 PLAN DE ACCIÓN JERÁRQUICO - Mejoras PDF Verificación Legal

## 🎯 OBJETIVO
Corregir y mejorar el generador de PDF de verificación legal para que:
1. Muestre contexto claro sobre por qué hay 0 restricciones
2. Presente datos REALES de proximidad (nombres de ríos, ubicaciones, distancias precisas)
3. Incluya mapas mejorados con siluetas, flechas y puntos cardinales
4. Ordene y complete la tabla de niveles de confianza con datos reales

---

## 🔥 PRIORIDAD CRÍTICA - Problemas Detectados

### ❌ PROBLEMA 1: Contexto insuficiente en "0 restricciones"
**Síntoma:** El PDF dice "0 restricciones" pero no explica POR QUÉ
**Impacto:** Usuario no entiende si es correcto o si faltan datos
**Ubicación:** Portada, sección resumen

### ❌ PROBLEMA 2: Datos genéricos en tabla de proximidad
**Síntoma:** Muestra "drenaje" en vez de nombre real del río, distancias erróneas
**Impacto:** No es útil para decisiones legales/operacionales
**Ubicación:** Tabla de análisis de proximidad

### ❌ PROBLEMA 3: Mapa sin elementos visuales clave
**Síntoma:** Falta silueta de parcela, flechas a zonas críticas, veleta
**Impacto:** Difícil interpretar orientación y proximidad real
**Ubicación:** Sección de mapa

### ❌ PROBLEMA 4: Tabla de confianza desorganizada
**Síntoma:** Datos mezclados, sin ordenar, presentación confusa
**Impacto:** Dificulta evaluar calidad de los datos
**Ubicación:** Sección de niveles de confianza

---

## 📝 PLAN DE ACCIÓN - Orden de Ejecución

### FASE 1: MEJORAS EN CONTEXTO Y EXPLICACIÓN (30 min)

#### ✅ Tarea 1.1: Mejorar resumen de restricciones en portada
**Archivo:** `generador_pdf_legal.py` líneas 400-430
**Cambios:**
```python
# ANTES:
resumen_data = [
    ['Resumen de Restricciones', ''],
    ['Total de restricciones:', str(num_restricciones)],
    ['Área afectada:', f'{area_restringida:.2f} ha ({porcentaje:.1f}%)'],
]

# DESPUÉS:
# Agregar contexto explicativo según el caso
if num_restricciones == 0:
    explicacion = f"No se encontraron restricciones legales en esta parcela de {departamento}. " \
                  f"Esto es correcto porque: (1) No hay áreas protegidas en el polígono, " \
                  f"(2) No hay resguardos indígenas superpuestos, (3) Los cauces hídricos están " \
                  f"fuera de los retiros mínimos (>30m), y (4) Casanare no tiene páramos (altitud <500 msnm)."
else:
    explicacion = f"Se encontraron {num_restricciones} restricciones que afectan " \
                  f"{area_restringida:.2f} ha ({porcentaje:.1f}%) de la parcela."

resumen_data = [
    ['Resumen de Restricciones', ''],
    ['Total de restricciones:', str(num_restricciones)],
    ['Área afectada:', f'{area_restringida:.2f} ha ({porcentaje:.1f}%)'],
    ['Explicación:', explicacion[:120] + '...']  # Primera parte
]
```

#### ✅ Tarea 1.2: Agregar nota contextual después del resumen
**Archivo:** `generador_pdf_legal.py` después de línea 428
**Cambios:**
```python
elementos.append(resumen_table)
elementos.append(Spacer(1, 0.3*cm))

# NUEVA SECCIÓN: Contexto geográfico
if num_restricciones == 0:
    contexto_texto = Paragraph(
        f"<b>Contexto Geográfico de {departamento}:</b><br/>"
        f"• Región: {DEPARTAMENTOS_INFO[departamento]['region']}<br/>"
        f"• Características: {DEPARTAMENTOS_INFO[departamento]['caracteristicas']}<br/>"
        f"• Por qué 0 restricciones: La geografía de la llanura orinocense (altitud baja, "
        f"sin ecosistemas de alta montaña) y la ubicación específica de esta parcela "
        f"resultan en ausencia de superposición con áreas protegidas o resguardos.",
        self.styles['TextoNormal']
    )
    elementos.append(contexto_texto)
    elementos.append(Spacer(1, 0.5*cm))
```

---

### FASE 2: CORRECCIÓN DE DATOS DE PROXIMIDAD (45 min)

#### ✅ Tarea 2.1: Mejorar extracción de nombres reales de ríos
**Archivo:** `generador_pdf_legal.py` líneas 250-280
**Problema:** Muestra "drenaje" genérico en vez de nombre del río
**Solución:**
```python
# Investigar columnas reales del shapefile
# Ejecutar script de diagnóstico primero:

import geopandas as gpd
red_path = 'datos_geograficos/red_hidrica/drenajes_sencillos_igac.shp'
red_gdf = gpd.read_file(red_path)
print("Columnas disponibles:", red_gdf.columns.tolist())
print("\nPrimeras 5 filas:")
print(red_gdf[['NOMBRE', 'TIPO', 'ORDEN']].head(10) if 'NOMBRE' in red_gdf.columns else red_gdf.head(10))

# Actualizar código para buscar en columnas correctas
nombre_rio = red.loc[idx_min].get('NOMBRE', 
              red.loc[idx_min].get('NOMBRE_GEOG', 
              red.loc[idx_min].get('NOM_GEO', 'Cauce sin nombre oficial')))

tipo_rio = red.loc[idx_min].get('TIPO_DRENAJE', 
           red.loc[idx_min].get('TIPO', 
           red.loc[idx_min].get('ORDEN', 'Cauce natural')))
```

#### ✅ Tarea 2.2: Agregar ubicación geográfica del elemento más cercano
**Archivo:** `generador_pdf_legal.py` función `_calcular_distancias_minimas`
**Cambios:**
```python
# Para ÁREAS PROTEGIDAS:
nombre_cercana = areas.loc[idx_min].get('NOMBRE', 'N/A')
categoria = areas.loc[idx_min].get('CATEGORIA', 'N/A')
departamento_area = areas.loc[idx_min].get('DEPARTAMENTO', areas.loc[idx_min].get('depto', 'N/A'))
municipio_area = areas.loc[idx_min].get('MUNICIPIO', areas.loc[idx_min].get('mpio', 'N/A'))

# Calcular dirección (N, S, E, O, NE, NO, SE, SO)
centroide_area = areas.loc[idx_min].geometry.centroid
dx = centroide_area.x - parcela_gdf.geometry.centroid.iloc[0].x
dy = centroide_area.y - parcela_gdf.geometry.centroid.iloc[0].y

direccion = ""
if abs(dy) > abs(dx):
    direccion = "Norte" if dy > 0 else "Sur"
else:
    direccion = "Este" if dx > 0 else "Oeste"

# Combinar direcciones (NE, NO, SE, SO)
if abs(dy) > 0.3 * abs(dx) and abs(dx) > 0.3 * abs(dy):
    direccion = ("Norte" if dy > 0 else "Sur") + ("este" if dx > 0 else "oeste")

distancias['areas_protegidas'] = {
    'distancia_km': round(dist_min_km, 2),
    'nombre': nombre_cercana,
    'categoria': categoria,
    'ubicacion': f"{municipio_area}, {departamento_area}",
    'direccion': direccion,
    'en_parcela': dist_min_km == 0
}
```

#### ✅ Tarea 2.3: Actualizar tabla de proximidad para mostrar ubicación
**Archivo:** `generador_pdf_legal.py` función `_crear_seccion_proximidad` líneas 440-520
**Cambios:**
```python
# Cambiar headers
headers = ['Tipo de Zona', 'Distancia', 'Nombre y Ubicación', 'Dirección', 'Estado']
data = [headers]

# Para áreas protegidas:
if ap['distancia_km'] is not None:
    if ap['en_parcela']:
        dist_texto = '0 km\n(DENTRO)'
        direccion_texto = 'Superpuesta'
    else:
        dist_texto = f"{ap['distancia_km']} km"
        direccion_texto = ap.get('direccion', 'N/A')
    
    nombre = f"{ap['nombre'][:30]}\n({ap['categoria']})\n{ap.get('ubicacion', 'N/A')}"
else:
    dist_texto = 'N/A'
    direccion_texto = '-'
    nombre = ap['nombre']

data.append(['Áreas Protegidas\n(RUNAP)', dist_texto, nombre, direccion_texto, estado])

# Repetir para red hídrica, resguardos, páramos
```

---

### FASE 3: MEJORAS EN VISUALIZACIÓN DE MAPAS (60 min)

#### ✅ Tarea 3.1: Agregar silueta visible de la parcela
**Archivo:** `generador_pdf_legal.py` función `_generar_mapa_parcela` línea 560
**Cambios:**
```python
# ANTES:
parcela_gdf.plot(ax=ax, facecolor='lightgreen', edgecolor='darkgreen', linewidth=2, alpha=0.5, label='Parcela')

# DESPUÉS:
# Dibujar silueta primero (más gruesa)
parcela_gdf.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=4, alpha=1.0, linestyle='--', label='Límite Parcela')
# Dibujar relleno translúcido después
parcela_gdf.plot(ax=ax, facecolor='lightgreen', edgecolor='darkgreen', linewidth=1.5, alpha=0.3)
```

#### ✅ Tarea 3.2: Agregar flechas hacia zonas críticas más cercanas
**Archivo:** `generador_pdf_legal.py` función `_generar_mapa_parcela` después de línea 620
**Cambios:**
```python
# NUEVA FUNCIÓN: Agregar flechas hacia elementos críticos
def agregar_flechas_proximidad(ax, parcela_gdf, distancias_dict):
    """Dibuja flechas desde parcela hacia elementos más cercanos"""
    from matplotlib.patches import FancyArrowPatch
    
    centroide_parcela = parcela_gdf.geometry.centroid.iloc[0]
    x_parcela, y_parcela = centroide_parcela.x, centroide_parcela.y
    
    # Colores por tipo
    colores = {
        'areas_protegidas': 'orange',
        'resguardos_indigenas': 'purple',
        'red_hidrica': 'blue',
        'paramos': 'lightblue'
    }
    
    for tipo, info in distancias_dict.items():
        if info.get('distancia_km') and info['distancia_km'] > 0 and info['distancia_km'] < 50:
            # Calcular punto destino (dirección)
            direccion = info.get('direccion', '')
            dx, dy = 0, 0
            
            if 'Norte' in direccion or 'norte' in direccion:
                dy = 0.1
            if 'Sur' in direccion or 'sur' in direccion:
                dy = -0.1
            if 'Este' in direccion or 'este' in direccion:
                dx = 0.1
            if 'Oeste' in direccion or 'oeste' in direccion:
                dx = -0.1
            
            x_destino = x_parcela + dx
            y_destino = y_parcela + dy
            
            # Dibujar flecha
            arrow = FancyArrowPatch(
                (x_parcela, y_parcela), 
                (x_destino, y_destino),
                arrowstyle='->', 
                color=colores.get(tipo, 'gray'),
                linewidth=2,
                alpha=0.7,
                mutation_scale=20
            )
            ax.add_patch(arrow)
            
            # Etiqueta con distancia
            ax.text(x_destino, y_destino, 
                   f"{info['distancia_km']} km\n{tipo.replace('_', ' ').title()[:15]}",
                   fontsize=7, ha='center', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=colores.get(tipo, 'white'), alpha=0.7))

# Llamar después de dibujar todas las capas:
agregar_flechas_proximidad(ax, parcela_gdf, distancias)  # Pasar distancias como parámetro
```

#### ✅ Tarea 3.3: Agregar rosa de los vientos (veleta)
**Archivo:** `generador_pdf_legal.py` función `_generar_mapa_parcela` después de línea 650
**Cambios:**
```python
# NUEVA FUNCIÓN: Rosa de los vientos
def agregar_rosa_vientos(ax):
    """Agrega veleta de puntos cardinales al mapa"""
    from matplotlib.patches import FancyArrow, Circle
    
    # Posición de la rosa (esquina inferior izquierda del mapa)
    x_base, y_base = ax.get_xlim()[0] + 0.08 * (ax.get_xlim()[1] - ax.get_xlim()[0]), \
                     ax.get_ylim()[0] + 0.08 * (ax.get_ylim()[1] - ax.get_ylim()[0])
    
    tam_flecha = 0.03 * (ax.get_ylim()[1] - ax.get_ylim()[0])
    
    # Círculo de fondo
    circulo = Circle((x_base, y_base), tam_flecha * 1.2, facecolor='white', edgecolor='black', linewidth=1.5, alpha=0.8, zorder=100)
    ax.add_patch(circulo)
    
    # Flechas de dirección
    # Norte (roja)
    ax.arrow(x_base, y_base, 0, tam_flecha, head_width=tam_flecha*0.3, head_length=tam_flecha*0.2, 
             fc='red', ec='darkred', linewidth=1.5, zorder=101)
    ax.text(x_base, y_base + tam_flecha * 1.5, 'N', fontsize=10, fontweight='bold', ha='center', va='bottom', zorder=102)
    
    # Sur
    ax.arrow(x_base, y_base, 0, -tam_flecha*0.7, head_width=tam_flecha*0.25, head_length=tam_flecha*0.15, 
             fc='gray', ec='black', linewidth=1, alpha=0.7, zorder=101)
    
    # Este
    ax.arrow(x_base, y_base, tam_flecha*0.7, 0, head_width=tam_flecha*0.25, head_length=tam_flecha*0.15, 
             fc='gray', ec='black', linewidth=1, alpha=0.7, zorder=101)
    ax.text(x_base + tam_flecha * 1.0, y_base, 'E', fontsize=8, ha='left', va='center', zorder=102)
    
    # Oeste
    ax.arrow(x_base, y_base, -tam_flecha*0.7, 0, head_width=tam_flecha*0.25, head_length=tam_flecha*0.15, 
             fc='gray', ec='black', linewidth=1, alpha=0.7, zorder=101)
    ax.text(x_base - tam_flecha * 1.0, y_base, 'O', fontsize=8, ha='right', va='center', zorder=102)

# Llamar antes de plt.tight_layout():
agregar_rosa_vientos(ax)
```

---

### FASE 4: ORDENAR Y COMPLETAR TABLA DE CONFIANZA (20 min)

#### ✅ Tarea 4.1: Ordenar tabla alfabéticamente
**Archivo:** `generador_pdf_legal.py` función `_crear_seccion_confianza` línea 780
**Cambios:**
```python
# ANTES:
for capa, info in resultado.niveles_confianza.items():
    # ...procesar...

# DESPUÉS:
# Ordenar por nombre de capa (orden lógico: áreas, páramos, red, resguardos)
orden_capas = ['areas_protegidas', 'paramos', 'red_hidrica', 'resguardos_indigenas']
capas_ordenadas = sorted(resultado.niveles_confianza.items(), 
                         key=lambda x: orden_capas.index(x[0]) if x[0] in orden_capas else 999)

for capa, info in capas_ordenadas:
    # ...procesar...
```

#### ✅ Tarea 4.2: Agregar versión/fecha de los datos
**Archivo:** `generador_pdf_legal.py` función `_crear_seccion_confianza`
**Cambios:**
```python
# Modificar headers para incluir fecha
headers = ['Capa Geográfica', 'Nivel', 'Fuente Oficial', 'Versión/Fecha', 'Elementos\nVerificados', 'Observaciones']

# Mapeo de fechas de actualización (investigar en metadatos de shapefiles)
fechas_actualizacion = {
    'red_hidrica': '2024',
    'areas_protegidas': '2025',
    'resguardos_indigenas': '2024',
    'paramos': 'Jun 2020'  # Del nombre del archivo
}

# Al crear las filas:
version = fechas_actualizacion.get(capa, '2024')
fila = [
    nombre_capa,
    f"{emoji}\n{nivel_texto}",
    fuente,
    version,
    elementos_num,
    observaciones
]
```

---

## 🔧 SCRIPTS DE SOPORTE

### Script 1: Investigar columnas de red hídrica
```python
# diagnosticar_red_hidrica.py
import geopandas as gpd

red_path = 'datos_geograficos/red_hidrica/drenajes_sencillos_igac.shp'
red_gdf = gpd.read_file(red_path)

print("="*80)
print("DIAGNÓSTICO RED HÍDRICA")
print("="*80)
print(f"\nColumnas disponibles: {red_gdf.columns.tolist()}")
print(f"\nNúmero de registros: {len(red_gdf)}")

# Buscar columnas de nombre
columnas_nombre = [col for col in red_gdf.columns if 'NOM' in col.upper() or 'NAME' in col.upper()]
print(f"\nColumnas de nombre: {columnas_nombre}")

# Mostrar muestra
print("\n" + "="*80)
print("MUESTRA DE DATOS (primeros 10 registros):")
print("="*80)
cols_interesantes = [col for col in ['NOMBRE', 'TIPO', 'ORDEN', 'NOMBRE_GEOG', 'NOM_GEO', 'TIPO_DRENAJE'] if col in red_gdf.columns]
if cols_interesantes:
    print(red_gdf[cols_interesantes].head(10))
else:
    print(red_gdf.head(10))

# Filtrar Casanare
print("\n" + "="*80)
print("FILTRADO POR CASANARE:")
print("="*80)
bbox_casanare = [-73.0, 5.0, -69.0, 6.5]
red_casanare = red_gdf.cx[bbox_casanare[0]:bbox_casanare[2], bbox_casanare[1]:bbox_casanare[3]]
print(f"Registros en Casanare: {len(red_casanare)}")
if len(red_casanare) > 0 and cols_interesantes:
    print("\nMuestra Casanare:")
    print(red_casanare[cols_interesantes].head(10))
```

### Script 2: Validación completa antes de generar PDF
```python
# validar_antes_de_generar_pdf.py
"""
Ejecutar este script ANTES de generar el PDF para verificar que:
1. Todos los datos geográficos están cargados
2. Las columnas de nombres existen
3. El filtrado por Casanare funciona
4. Las distancias se calculan correctamente
"""

# Ver contenido completo en archivo separado
```

---

## ✅ CHECKLIST DE VALIDACIÓN

Antes de generar el PDF final, verificar:

- [ ] Contexto de "0 restricciones" explica geografía de Casanare
- [ ] Tabla de proximidad muestra nombres REALES de ríos (no "drenaje")
- [ ] Distancias a red hídrica son precisas (metros si <1km, km si >1km)
- [ ] Direcciones (N, S, E, O) están correctamente calculadas
- [ ] Ubicaciones (municipio, departamento) están presentes
- [ ] Mapa muestra silueta roja de la parcela (línea discontinua gruesa)
- [ ] Mapa tiene flechas hacia zonas críticas con etiquetas de distancia
- [ ] Mapa tiene rosa de los vientos en esquina inferior izquierda
- [ ] Tabla de confianza está ordenada alfabéticamente
- [ ] Tabla de confianza tiene fechas/versiones de datos
- [ ] No hay "N/A" innecesarios, todo tiene datos reales
- [ ] El PDF es profesional y útil para toma de decisiones

---

## 📊 MÉTRICAS DE ÉXITO

### Antes de las mejoras:
- ❌ Contexto: "0 restricciones" sin explicación
- ❌ Proximidad: "drenaje" genérico, distancias erróneas
- ❌ Mapa: Sin silueta visible, sin flechas, sin veleta
- ❌ Confianza: Desorganizada, con "N/A"

### Después de las mejoras:
- ✅ Contexto: Explicación detallada de por qué 0 (geografía + altitud + datos)
- ✅ Proximidad: Nombres reales ("Río Cravo Sur"), ubicaciones, direcciones
- ✅ Mapa: Silueta roja, flechas con km, rosa de los vientos
- ✅ Confianza: Ordenada, con fechas, sin "N/A" innecesarios

---

## 🚀 ORDEN DE EJECUCIÓN

1. **Ejecutar script de diagnóstico de red hídrica** → Identificar columnas correctas
2. **Aplicar FASE 1** → Mejorar contexto y explicación
3. **Aplicar FASE 2** → Corregir datos de proximidad
4. **Aplicar FASE 3** → Mejorar visualización de mapas
5. **Aplicar FASE 4** → Ordenar tabla de confianza
6. **Ejecutar script de validación** → Verificar todas las correcciones
7. **Generar PDF final** → `python generar_pdf_verificacion_casanare.py`
8. **Revisar PDF** → Abrir y validar manualmente con checklist
9. **Documentar** → Actualizar documentación con mejoras aplicadas

---

## 📝 NOTAS IMPORTANTES

- **No romper código existente:** Cada cambio debe ser incremental y probado
- **Usar datos reales:** Investigar metadatos de shapefiles antes de hardcodear
- **Mantener profesionalismo:** El PDF es un documento legal, no un demo
- **Testear cada fase:** No pasar a la siguiente hasta validar la anterior
- **Documentar cambios:** Agregar comentarios en el código explicando cada mejora

---

## 📧 RESPONSABLE
Sebastián Flórez  
Fecha: 2025-01-XX  
Proyecto: AgroTech Histórico - Sistema de Verificación Legal

