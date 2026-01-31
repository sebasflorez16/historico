# 🗺️ MAPA 1 - VERSIÓN FINAL 100% DINÁMICA

## ✅ LOGROS ACTUALES

1. **Detección automática funciona perfectamente:**
   - ✅ Detecta Casanare (departamento) automáticamente
   - ✅ Detecta Yopal (municipio) automáticamente
   - ✅ Carga 317 ríos del municipio (49 con nombres)
   - ✅ Dibuja silueta del municipio
   - ✅ Ubica la parcela dentro del municipio con punto rojo

## ❌ PROBLEMA PENDIENTE

**Los ríos NO se están dibujando en el mapa**

### Causa raíz:
El método `_generar_mapa_parcela` en `generador_pdf_legal.py` tiene código antiguo que busca ríos en:
```python
if verificador.red_hidrica is not None and len(verificador.red_hidrica) > 0:
    red = verificador.red_hidrica.copy()
    # ... código que nunca se ejecuta porque red_hidrica está vacía
```

Pero el `DetectorGeografico` ya cargó los ríos correctamente en:
```python
red_hidrica_municipal = ubicacion.get('red_hidrica', None)  # 317 ríos ✅
```

## 🔧 SOLUCIÓN

Reemplazar la sección de red hídrica en `_generar_mapa_parcela` (líneas ~1727-1850) con:

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🌊 PASO 3: RED HÍDRICA MUNICIPAL (ya cargada por el detector)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rios_dibujados = 0
rios_etiquetados = 0

if red_hidrica_municipal is not None and len(red_hidrica_municipal) > 0:
    # Dibujar TODOS los ríos del municipio
    red_hidrica_municipal.plot(
        ax=ax,
        color='#1565C0',      # Azul intenso
        linewidth=2,
        alpha=0.85,
        zorder=5
    )
    rios_dibujados = len(red_hidrica_municipal)
    
    # Etiquetar los 5 ríos más importantes CON NOMBRE
    red_con_longitud = red_hidrica_municipal.copy()
    red_con_longitud['longitud_calc'] = red_con_longitud.geometry.length
    red_ordenada = red_con_longitud.sort_values('longitud_calc', ascending=False)
    
    for idx, rio in red_ordenada.iterrows():
        if rios_etiquetados >= 5:
            break
        
        # Buscar nombre en múltiples campos posibles
        nombre_rio = None
        for campo in ['NOMBRE', 'nombre', 'name', 'NOMBRE_GEO']:
            if campo in rio.index:
                nombre = rio.get(campo)
                if nombre and str(nombre).strip() and str(nombre).lower() not in ['none', 'nan', '']:
                    nombre_rio = nombre
                    break
        
        if nombre_rio:
            try:
                # Calcular punto medio del río para etiqueta
                if rio.geometry.geom_type == 'LineString':
                    punto = rio.geometry.interpolate(0.5, normalized=True)
                elif rio.geometry.geom_type == 'MultiLineString':
                    lineas = list(rio.geometry.geoms)
                    linea_mas_larga = max(lineas, key=lambda l: l.length)
                    punto = linea_mas_larga.interpolate(0.5, normalized=True)
                else:
                    continue
                
                # Dibujar etiqueta
                ax.text(
                    punto.x, punto.y,
                    str(nombre_rio)[:30],
                    fontsize=8,
                    fontweight='bold',
                    color='#0D47A1',
                    bbox=dict(
                        boxstyle='round,pad=0.3',
                        facecolor='white',
                        edgecolor='#1565C0',
                        linewidth=1.2,
                        alpha=0.9
                    ),
                    ha='center',
                    va='center',
                    zorder=20
                )
                rios_etiquetados += 1
            except:
                continue
    
    print(f"✅ Mapa: {rios_dibujados} ríos dibujados, {rios_etiquetados} etiquetados")
else:
    print(f"⚠️  No hay red hídrica municipal para dibujar")
```

## 📍 ARCHIVOS A MODIFICAR

1. **generador_pdf_legal.py** (líneas 1727-1850 aproximadamente)
   - Buscar: `# 2️⃣ RED HÍDRICA MUNICIPAL CON NOMBRES (elemento crítico)`
   - Reemplazar: Toda la sección `try/except` con el código simplificado de arriba

## 🎯 RESULTADO ESPERADO

Mapa final que muestre:
1. ✅ Silueta del municipio de Yopal (gris claro)
2. ✅ Punto rojo ubicando la parcela dentro del municipio
3. ✅ **317 ríos del municipio dibujados en azul**
4. ✅ **5 ríos principales etiquetados con sus nombres**
5. ✅ Norte, escala gráfica, título
6. ✅ Leyenda con municipio y cantidad de ríos

## 🚀 SIGUIENTE PASO

Aplicar el reemplazo en `generador_pdf_legal.py` y regenerar el PDF de prueba.
