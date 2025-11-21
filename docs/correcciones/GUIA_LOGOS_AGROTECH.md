# 🖼️ Guía de Integración de Logos AgroTech

## 📁 Estructura de Archivos

```
historical/
└── static/
    └── img/
        ├── agrotech-logo.png          (Logo completo horizontal)
        ├── agrotech-icon.png          (Ícono/isotipo circular)
        └── agrotech-logo-white.png    (Logo blanco para fondos oscuros)
```

---

## 🎨 Logos Proporcionados

Has enviado 2 imágenes:

### 1. **Logo Isotipo (Ícono circular)**
- 📍 Ubicación icónica con satélite
- 🌾 Elementos agrícolas (terreno, cultivos)
- 🛰️ Satélite en órbita
- 🎨 Colores: Verde, naranja, negro

**Uso recomendado:**
- Favicon
- Ícono en modales
- Avatar de aplicación
- Versión compacta en móvil

### 2. **Logo Completo Horizontal**
- 📍 Isotipo + texto "agrotech."
- 🎨 Tipografía bold moderna
- ⚡ Punto final en naranja

**Uso recomendado:**
- Navbar principal
- Header de documentos
- Footer
- Pantallas de inicio

---

## 🚀 Pasos de Instalación

### 1. Guardar los Logos

Copia las imágenes que te proporcioné en:

```bash
historical/static/img/
```

**Nombres sugeridos:**
- `agrotech-logo.png` → Logo completo horizontal (segunda imagen)
- `agrotech-icon.png` → Isotipo circular (primera imagen)

### 2. Optimización de Imágenes (Opcional)

Para mejor rendimiento, optimiza las imágenes:

```bash
# Redimensionar logo completo
convert agrotech-logo.png -resize 400x agrotech-logo.png

# Redimensionar ícono
convert agrotech-icon.png -resize 200x200 agrotech-icon.png
```

O usa herramientas online:
- [TinyPNG](https://tinypng.com/)
- [Squoosh](https://squoosh.app/)

### 3. Configurar Django Static Files

Ya está configurado en `settings.py`, pero verifica:

```python
# settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
```

### 4. Recolectar Static Files (Producción)

```bash
python manage.py collectstatic
```

---

## 🔧 Implementación en Templates

### Navbar (base.html)

```html
<nav class="navbar navbar-expand-lg">
    <div class="container-fluid">
        <a class="navbar-brand" href="{% url 'informes:dashboard' %}">
            <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech" />
            <span>agrotech.</span>
        </a>
        <!-- ...resto del navbar... -->
    </div>
</nav>
```

### Logo Flotante (datos_guardados.html)

```html
{% load static %}

<div class="agrotech-logo-header">
    <img src="{% static 'img/agrotech-logo.png' %}" 
         alt="AgroTech"
         onerror="this.style.display='none'">
    <span class="agrotech-brand-text">agrotech.</span>
</div>
```

### Logo en Modal

```html
<div class="download-modal-content">
    <img src="{% static 'img/agrotech-icon.png' %}" 
         alt="AgroTech" 
         style="height: 50px; width: auto; 
                filter: drop-shadow(0 0 10px rgba(46, 139, 87, 0.3));"
         onerror="this.style.display='none'">
    <!-- ...resto del modal... -->
</div>
```

### Favicon

```html
<!-- base.html <head> -->
<link rel="icon" type="image/png" href="{% static 'img/agrotech-icon.png' %}">
<link rel="apple-touch-icon" href="{% static 'img/agrotech-icon.png' %}">
```

---

## 🎨 Estilos CSS para Logos

### Logo en Navbar

```css
.navbar-brand img {
    height: 40px;
    width: auto;
    filter: drop-shadow(0 2px 8px rgba(46, 139, 87, 0.3));
    transition: transform 0.3s ease;
}

.navbar-brand:hover img {
    transform: scale(1.05);
}
```

### Logo Flotante

```css
.agrotech-logo-header {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 1000;
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 12px 20px;
    border: 1px solid var(--glass-border);
    box-shadow: var(--shadow-soft);
    transition: all 0.3s ease;
}

.agrotech-logo-header:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

.agrotech-logo-header img {
    height: 45px;
    width: auto;
}
```

### Logo en Modal

```css
.download-modal-content img {
    height: 50px;
    width: auto;
    filter: drop-shadow(0 0 10px rgba(46, 139, 87, 0.3));
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}
```

---

## 📱 Responsive Design

### Desktop (> 768px)
```css
.agrotech-logo-header img {
    height: 45px;
}

.navbar-brand img {
    height: 40px;
}
```

### Móvil (≤ 768px)
```css
@media (max-width: 768px) {
    .agrotech-logo-header {
        left: 10px;
        top: 10px;
        padding: 8px 12px;
    }
    
    .agrotech-logo-header img {
        height: 35px;
    }
    
    .navbar-brand img {
        height: 32px;
    }
    
    .agrotech-brand-text {
        font-size: 1rem;
    }
}
```

---

## 🔍 Fallback para Imágenes Faltantes

Si la imagen no carga, ocultar automáticamente:

```html
<img src="{% static 'img/agrotech-logo.png' %}" 
     alt="AgroTech"
     onerror="this.style.display='none'">
```

O mostrar texto alternativo:

```html
<img src="{% static 'img/agrotech-logo.png' %}" 
     alt="AgroTech"
     onerror="this.onerror=null; this.src='{% static 'img/placeholder.png' %}'">
```

---

## 🎯 Ubicaciones de Logos en la Interfaz

### ✅ Ya Implementado:
1. **Header flotante** (`datos_guardados.html`)
   - Esquina superior izquierda
   - Efecto glassmorphism
   - Logo + texto "agrotech."

2. **Modal de descarga** (`datos_guardados.html`)
   - Ícono circular
   - Animación float sutil
   - Drop shadow verde

### 📝 Por Implementar:
3. **Navbar principal** (`base.html`)
   - Logo completo horizontal
   - Link al dashboard
   - Responsive

4. **Footer**
   - Logo pequeño
   - Copyright
   - Links importantes

5. **Página de login**
   - Logo grande centrado
   - Formulario glassmorphism debajo

6. **Dashboard**
   - Logo en encabezado
   - Marca de agua sutil en fondo

7. **Informes PDF**
   - Logo en header
   - Colores de marca (verde + naranja)

---

## 🖼️ Características de los Logos

### Isotipo (agrotech-icon.png)
- **Dimensiones**: 800x800px (aproximado)
- **Formato**: PNG con transparencia
- **Elementos**:
  - Pin de ubicación negro
  - Satélite verde en órbita
  - Terreno naranja y verde
  - Círculo de órbita verde

### Logotipo Completo (agrotech-logo.png)
- **Dimensiones**: ~1600x400px (aproximado)
- **Formato**: PNG con transparencia
- **Elementos**:
  - Isotipo a la izquierda
  - Texto "agrotech." en negro bold
  - Punto final en verde
  - Espaciado profesional

---

## 🎨 Variaciones de Color

Si necesitas crear versiones alternativas:

### Logo Blanco (para fondos oscuros)
```css
.logo-white {
    filter: brightness(0) invert(1);
}
```

### Logo Verde Monocromático
```css
.logo-green {
    filter: hue-rotate(120deg) saturate(1.5);
}
```

### Logo con Efecto Brillante
```css
.logo-glow {
    filter: drop-shadow(0 0 20px rgba(46, 139, 87, 0.6));
}
```

---

## ✅ Checklist de Integración

- [ ] Guardar `agrotech-logo.png` en `/static/img/`
- [ ] Guardar `agrotech-icon.png` en `/static/img/`
- [ ] Optimizar imágenes (< 100KB cada una)
- [ ] Configurar favicon en `base.html`
- [ ] Actualizar navbar con logo
- [ ] Verificar responsive en móvil
- [ ] Probar fallback si imagen falta
- [ ] Ejecutar `collectstatic` en producción

---

## 🚨 Solución de Problemas

### Logo no se muestra
1. Verificar ruta: `static/img/agrotech-logo.png`
2. Ejecutar `collectstatic`
3. Limpiar caché del navegador (Ctrl+Shift+R)
4. Verificar permisos de archivo (chmod 644)

### Logo se ve pixelado
1. Usar imágenes de alta resolución (2x)
2. Agregar `@media` para Retina displays
3. Considerar usar SVG en su lugar

### Logo no carga en producción
1. Verificar `STATIC_ROOT` en `settings.py`
2. Ejecutar `python manage.py collectstatic`
3. Configurar servidor web (Nginx/Apache) para servir static files

---

## 📚 Recursos Adicionales

- [Django Static Files Documentation](https://docs.djangoproject.com/en/4.2/howto/static-files/)
- [Optimización de Imágenes Web](https://web.dev/optimize-images/)
- [Glassmorphism CSS Generator](https://hype4.academy/tools/glassmorphism-generator)

---

**¡Los logos están listos para ser integrados!** 🎉

Simplemente copia las dos imágenes proporcionadas en la carpeta `static/img/` y el sistema las detectará automáticamente.
