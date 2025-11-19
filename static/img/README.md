# 📁 Carpeta de Imágenes AgroTech

## 🖼️ Logos a Colocar Aquí

Esta carpeta debe contener los logos de AgroTech proporcionados:

### 1. `agrotech-logo.png` (Logo Completo Horizontal)
```
┌─────────────────────────────────────────────┐
│  🛰️                                         │
│  📍  agrotech.                              │
│  🌾                                         │
└─────────────────────────────────────────────┘
```

**Descripción**:
- Logo isotipo (pin + satélite) + texto "agrotech."
- Punto final en verde/naranja
- Fondo transparente (PNG)
- Tamaño recomendado: ~1600x400px
- Peso: < 100KB

**Usos**:
- Navbar principal
- Header flotante
- Footer
- Documentos oficiales

---

### 2. `agrotech-icon.png` (Isotipo Circular)
```
┌─────────────┐
│     🛰️      │
│             │
│  📍         │
│    🌾       │
│   Círculo   │
│   orbital   │
└─────────────┘
```

**Descripción**:
- Solo el isotipo (pin de ubicación + satélite + terreno)
- Círculo de órbita verde
- Fondo transparente (PNG)
- Tamaño recomendado: 800x800px (cuadrado)
- Peso: < 50KB

**Usos**:
- Favicon
- Avatar de aplicación
- Modales
- Iconos pequeños
- Versión móvil compacta

---

## 📥 Cómo Agregar los Logos

### Paso 1: Obtener las Imágenes
Las imágenes fueron proporcionadas por el usuario:
- Primera imagen: Isotipo circular
- Segunda imagen: Logo completo horizontal

### Paso 2: Renombrar
Guarda las imágenes con estos nombres exactos:
```
agrotech-logo.png
agrotech-icon.png
```

### Paso 3: Copiar Aquí
Coloca ambos archivos en esta carpeta:
```
/Users/sebasflorez16/Documents/AgroTech Historico/historical/static/img/
```

### Paso 4: Verificar
Ejecuta en terminal:
```bash
ls -lh historical/static/img/
```

Deberías ver:
```
-rw-r--r--  1 user  staff   80K  agrotech-icon.png
-rw-r--r--  1 user  staff  120K  agrotech-logo.png
-rw-r--r--  1 user  staff   2K   README.md (este archivo)
```

---

## ✅ Verificación Rápida

Después de copiar los logos, verifica que funcionan:

### En el Código HTML:
```html
<img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech">
<img src="{% static 'img/agrotech-icon.png' %}" alt="AgroTech">
```

### En el Navegador:
```
http://127.0.0.1:8000/static/img/agrotech-logo.png
http://127.0.0.1:8000/static/img/agrotech-icon.png
```

Si ambas URLs muestran las imágenes, ¡está perfecto! ✅

---

## 🎨 Especificaciones Técnicas

### Formato
- **Tipo**: PNG con transparencia (alpha channel)
- **Color**: RGB (no CMYK)
- **Resolución**: 72-144 DPI para web

### Tamaños Óptimos
```
Logo Completo:
  - Desktop: 400px ancho (altura proporcional)
  - Móvil: 200px ancho (altura proporcional)

Isotipo:
  - Desktop: 200x200px
  - Móvil: 100x100px
  - Favicon: 32x32px, 64x64px, 128x128px
```

### Peso del Archivo
```
✅ Ideal: < 50KB por imagen
⚠️ Máximo: < 200KB por imagen
❌ Evitar: > 500KB
```

### Optimización (Opcional)
Si las imágenes son muy pesadas:

**Opción 1 - Online**:
- [TinyPNG](https://tinypng.com/)
- [Squoosh](https://squoosh.app/)

**Opción 2 - Terminal** (si tienes ImageMagick):
```bash
convert agrotech-logo.png -quality 85 -resize 400x agrotech-logo.png
convert agrotech-icon.png -quality 85 -resize 200x200 agrotech-icon.png
```

---

## 🚨 Solución de Problemas

### Logo no aparece en el navegador
```bash
# 1. Verificar que el archivo existe
ls -la historical/static/img/agrotech-logo.png

# 2. Ejecutar collectstatic
python manage.py collectstatic --noinput

# 3. Limpiar caché del navegador
# Chrome/Edge: Ctrl + Shift + R
# Safari: Cmd + Option + R
```

### Imagen se ve pixelada
- Subir una versión de mayor resolución (2x)
- Asegurar que el PNG tiene buena calidad
- Considerar usar SVG en su lugar

### Imagen tiene fondo blanco en lugar de transparente
- Abrir en editor de imágenes (Photoshop, GIMP, Figma)
- Eliminar la capa de fondo
- Exportar como PNG con transparencia

---

## 📱 Responsive

Los logos se ajustan automáticamente según el dispositivo:

### Desktop (> 768px)
```css
.navbar-brand img { height: 40px; }
.agrotech-logo-header img { height: 45px; }
```

### Móvil (≤ 768px)
```css
.navbar-brand img { height: 32px; }
.agrotech-logo-header img { height: 35px; }
```

---

## 🎯 Estado Actual

```
┌────────────────────────────────────┐
│ Estado de la Carpeta de Imágenes: │
│                                    │
│ 📁 Carpeta creada:        ✅       │
│ 🖼️  agrotech-logo.png:    ⏳       │
│ 🖼️  agrotech-icon.png:    ⏳       │
│ 📝 README.md:             ✅       │
│ 🔧 CSS preparado:         ✅       │
│ 📄 Templates listos:      ✅       │
│                                    │
│ ⚠️  Esperando logos...             │
└────────────────────────────────────┘
```

---

## 📞 Ayuda

Si tienes problemas:

1. **Documentación**: Lee `GUIA_LOGOS_AGROTECH.md`
2. **Inicio Rápido**: Lee `INICIO_RAPIDO_GLASMORFISMO.md`
3. **Código Referencia**: Ver `datos_guardados.html`

---

**¡Coloca los logos aquí y el diseño estará completo!** 🎉

Los logos serán detectados automáticamente por Django y aparecerán en todas las páginas donde estén integrados.
