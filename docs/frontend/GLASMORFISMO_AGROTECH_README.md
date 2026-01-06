# 🌿 Sistema de Diseño: Glasmorfismo Luminoso AgroTech

## 📋 Resumen de Implementación

Se ha implementado un sistema de diseño completo basado en **Glasmorfismo Luminoso** para toda la interfaz de AgroTech Histórico, creando una experiencia visual moderna, limpia y profesional enfocada en agricultura de precisión.

---

## 🎨 Paleta de Colores

```css
--agrotech-orange: #FF7A00   /* Naranja vibrante - Acción y energía */
--agrotech-green: #2E8B57    /* Verde natural - Agricultura y vida */
--agrotech-white: #FFFFFF    /* Blanco puro - Claridad y limpieza */
--agrotech-light: #F8F9FA    /* Gris muy claro - Fondos sutiles */
```

### Uso de Colores:
- **Verde (#2E8B57)**: Elementos principales, títulos, iconos de estado positivo
- **Naranja (#FF7A00)**: Botones de acción, alertas, elementos destacados
- **Blanco**: Fondos de tarjetas (con transparencia), texto en botones
- **Degradados**: Combinación verde-naranja para efectos visuales premium

---

## ✨ Características del Diseño

### 1. **Glassmorphism (Efecto Cristal)**
```css
background: rgba(255, 255, 255, 0.85);
backdrop-filter: blur(20px);
-webkit-backdrop-filter: blur(20px);
border: 1px solid rgba(255, 255, 255, 0.3);
box-shadow: 0 8px 32px 0 rgba(46, 139, 87, 0.12);
```

**Características:**
- Fondos semitransparentes
- Efecto de desenfoque (blur)
- Bordes con opacidad
- Sombras suaves y difuminadas
- Sensación de profundidad y elegancia

### 2. **Fondo con Degradado Suave**
```css
background: linear-gradient(135deg, 
    #F8F9FA 0%,   /* Gris muy claro */
    #E8F5E9 50%,  /* Verde pastel */
    #FFF3E0 100%  /* Naranja pastel */
);
background-attachment: fixed;
```

### 3. **Animaciones y Transiciones**
- **Hover en tarjetas**: `translateY(-8px) scale(1.02)`
- **Botones**: Efecto de onda al hacer clic
- **Spinners**: Animación de órbita satelital temática
- **Modales**: Entrada suave con `slideUp` y `fadeIn`

---

## 🏗️ Componentes Implementados

### 📦 **Tarjetas (Cards)**
```css
.datos-card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    box-shadow: var(--shadow-soft);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
```

**Efectos:**
- Borde superior que aparece en hover (degradado verde-naranja)
- Elevación suave al pasar el cursor
- Transformación sutil con escala

### 🔘 **Botones**
```css
.btn-success {
    background: linear-gradient(135deg, #2E8B57 0%, #34A853 100%);
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(46, 139, 87, 0.3);
}
```

**Variantes:**
- `.btn-success`: Verde (acción principal)
- `.btn-info`: Azul-verde (información)
- `.btn-secondary`: Gris (acción secundaria)
- `.btn-primary` / `.descargar-imagen`: Degradado naranja-verde (destacado)

### 🏷️ **Badges (Etiquetas)**
```css
.indice-badge {
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(color, 0.3);
}
```

**Tipos:**
- `.fuente-eosda`: Verde brillante con sombra
- `.fuente-simulado`: Amarillo-naranja con sombra

### 📊 **Tablas**
```css
.datos-tabla thead {
    background: linear-gradient(135deg, 
        rgba(46, 139, 87, 0.12), 
        rgba(255, 122, 0, 0.12));
}

.datos-tabla tbody tr:hover {
    background: rgba(255, 122, 0, 0.08);
    transform: scale(1.01);
}
```

---

## 🎭 Elementos Temáticos

### 🛰️ **Spinner Satelital**
Animación orbital con satélite emoji y anillo pulsante:
```css
.satellite-spinner::before {
    content: '🛰️';
    animation: satellite-orbit 3s linear infinite;
    filter: drop-shadow(0 0 10px rgba(46, 139, 87, 0.5));
}
```

### 📡 **Barra de Progreso Satelital**
```css
.satellite-progress {
    background: linear-gradient(90deg, 
        rgba(46, 139, 87, 0.2) 0%, 
        rgba(255, 122, 0, 0.2) 100%);
    backdrop-filter: blur(10px);
}
```

### 🪟 **Modal Glassmorphism**
```css
.download-modal {
    background: rgba(46, 139, 87, 0.15);
    backdrop-filter: blur(12px);
}

.download-modal-content {
    background: var(--glass-bg);
    backdrop-filter: blur(30px);
    border-radius: 32px;
    border: 2px solid rgba(255, 255, 255, 0.3);
}
```

**Características:**
- Fondo desenfocado
- Borde superior con degradado verde-naranja
- Pasos de progreso con animación
- Logo AgroTech integrado

---

## 🖼️ Integración de Logos

### Logo Principal (Header Flotante)
```html
<div class="agrotech-logo-header">
    <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech">
    <span class="agrotech-brand-text">agrotech.</span>
</div>
```

**Ubicación:**
- Esquina superior izquierda (fixed)
- Efecto glassmorphism
- Hover con elevación sutil

### Logo en Modal
```html
<img src="{% static 'img/agrotech-icon.png' %}" 
     alt="AgroTech" 
     style="height: 50px; filter: drop-shadow(0 0 10px rgba(46, 139, 87, 0.3));">
```

---

## 📱 Diseño Responsive

### Desktop (> 768px)
- Tarjetas de 4 columnas en estadísticas
- Logo completo en header
- Espaciado generoso
- Animaciones completas

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
    
    .datos-card {
        border-radius: 16px;
        margin-bottom: 16px;
    }
}
```

---

## 🎯 Guía de Uso para Desarrolladores

### Crear una Tarjeta Glassmorphism
```html
<div class="datos-card" style="padding: 24px;">
    <div style="font-size: 2.5rem; margin-bottom: 8px;">🌾</div>
    <h3 style="color: var(--agrotech-green); font-weight: 800;">
        Valor
    </h3>
    <p class="text-muted" style="font-weight: 600;">
        Descripción
    </p>
</div>
```

### Crear un Botón AgroTech
```html
<button class="btn btn-success">
    <i class="fas fa-icon"></i> Texto
</button>
```

### Crear un Badge
```html
<span class="indice-badge fuente-eosda">
    EOSDA
</span>
```

### Mensaje Toast
```javascript
showToast('✅ Operación exitosa', 'success');
showToast('❌ Error encontrado', 'error');
showToast('⚠️ Advertencia', 'warning');
```

---

## 🎨 Variables CSS Globales

Todas las variables están definidas en `:root` y son accesibles en cualquier parte:

```css
:root {
    --agrotech-orange: #FF7A00;
    --agrotech-green: #2E8B57;
    --agrotech-white: #FFFFFF;
    --agrotech-light: #F8F9FA;
    --glass-bg: rgba(255, 255, 255, 0.85);
    --glass-border: rgba(255, 255, 255, 0.3);
    --shadow-soft: 0 8px 32px 0 rgba(46, 139, 87, 0.12);
    --shadow-hover: 0 12px 48px 0 rgba(255, 122, 0, 0.18);
}
```

**Uso:**
```css
color: var(--agrotech-green);
background: var(--glass-bg);
box-shadow: var(--shadow-soft);
```

---

## 📝 Archivos Modificados

1. ✅ `/templates/informes/parcelas/datos_guardados.html`
   - Sistema completo de glassmorphism
   - Logo integrado
   - Modal mejorado
   - Animaciones satelitales

2. ✅ `/templates/informes/base.html`
   - Variables CSS globales
   - Navbar glassmorphism
   - Botones y cards base
   - Sistema responsive

---

## 🚀 Próximos Pasos

Para aplicar el diseño a otras páginas:

1. **Dashboard Principal**: Aplicar tarjetas glassmorphism
2. **Galería de Imágenes**: Lightbox con efecto glassmorphism
3. **Formularios**: Inputs con efecto cristal
4. **Mapas**: Controles con glassmorphism
5. **Informes PDF**: Mantener colores de marca

---

## 🎓 Principios de Diseño AgroTech

1. **Claridad Visual**: Información legible y jerarquía clara
2. **Profesionalismo**: Estética moderna sin sacrificar funcionalidad
3. **Temática Agrícola**: Colores naturales (verde) + tecnología (naranja)
4. **Experiencia Fluida**: Animaciones suaves, transiciones elegantes
5. **Accesibilidad**: Contraste adecuado, tamaños de fuente legibles

---

## 📧 Soporte

Para dudas sobre el sistema de diseño:
- Consultar este documento
- Revisar `datos_guardados.html` como referencia
- Mantener consistencia con la paleta de colores

---

**Última actualización**: 19 de noviembre de 2025  
**Versión**: 1.0  
**Diseñador**: Sistema Glasmorfismo Luminoso AgroTech
