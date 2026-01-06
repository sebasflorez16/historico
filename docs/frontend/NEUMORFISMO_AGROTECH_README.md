# 🌿 Sistema de Diseño Neumorfismo Luminoso AgroTech

## 📋 Documentación Completa del Sistema Neumórfico

> **Versión**: 2.0  
> **Fecha**: Enero 2025  
> **Diseño**: Neumorfismo Luminoso 3D  
> **Paleta**: Verde #2E8B57 · Naranja #FF7A00 · Blanco  

---

## 🎨 Paleta de Colores

### Colores Principales
```css
--agrotech-orange: #FF7A00;     /* Naranja vibrante */
--agrotech-green: #2E8B57;      /* Verde bosque */
--agrotech-white: #FFFFFF;      /* Blanco puro */
--agrotech-light: #F0F4F8;      /* Fondo suave */
```

### Fondos Neumórficos
```css
--neuro-bg-primary: #E8F0F8;    /* Fondo principal */
--neuro-bg-secondary: #F5F7FA;  /* Fondo secundario */
```

### Sombras Neumórficas (Doble Sombra 3D)
```css
/* Sombras normales - efecto elevado */
--neuro-shadow-light: -8px -8px 16px rgba(255, 255, 255, 0.8);
--neuro-shadow-dark: 8px 8px 16px rgba(46, 139, 87, 0.15);

/* Sombras hover - efecto más elevado */
--neuro-shadow-hover-light: -12px -12px 24px rgba(255, 255, 255, 0.9);
--neuro-shadow-hover-dark: 12px 12px 24px rgba(255, 122, 0, 0.2);

/* Sombras inset - efecto hundido */
--neuro-shadow-inset-light: inset -4px -4px 8px rgba(255, 255, 255, 0.7);
--neuro-shadow-inset-dark: inset 4px 4px 8px rgba(46, 139, 87, 0.1);

/* Sombras activas - efecto presionado */
--neuro-shadow-active-light: inset -6px -6px 12px rgba(255, 255, 255, 0.6);
--neuro-shadow-active-dark: inset 6px 6px 12px rgba(46, 139, 87, 0.15);
```

---

## 🎯 Componentes Neumórficos

### 1. Cards (Tarjetas 3D)

#### Características:
- **Efecto**: Elevado suave con doble sombra
- **Border-radius**: 28-32px
- **Interacción**: Hover eleva más la tarjeta
- **Borde superior**: Gradiente verde-naranja que aparece al hover

```css
.card {
    background: var(--neuro-bg-secondary);
    border: none;
    border-radius: 28px;
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    transform: translateY(-8px);
    box-shadow: var(--neuro-shadow-hover-light), var(--neuro-shadow-hover-dark);
}
```

#### Uso:
```html
<div class="card datos-card">
    <div class="card-header">
        <h5>
            <i class="fas fa-chart-line"></i>
            Datos Satelitales
        </h5>
    </div>
    <div class="card-body">
        <!-- Contenido -->
    </div>
</div>
```

---

### 2. Botones Neumórficos

#### Características:
- **Estados**: Normal, Hover, Active (presionado)
- **Sombras**: Doble sombra que se intensifica en hover
- **Active**: Sombra inset para efecto de presión

```css
.btn {
    border-radius: 16px;
    padding: 14px 28px;
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
}

.btn-primary {
    background: linear-gradient(145deg, var(--agrotech-green), #34A853);
    color: white;
}

.btn:hover {
    box-shadow: var(--neuro-shadow-hover-light), var(--neuro-shadow-hover-dark);
    transform: translateY(-2px);
}

.btn:active {
    box-shadow: var(--neuro-shadow-active-light), var(--neuro-shadow-active-dark);
    transform: translateY(0);
}
```

---

### 3. Navbar Neumórfica

#### Características:
- **Posición**: Fija en la parte superior
- **Efecto**: Elevado con doble sombra
- **Nav-links**: Botones neumórficos individuales
- **Border-radius**: Inferior redondeado (0 0 24px 24px)

```css
.navbar {
    background: var(--neuro-bg-primary);
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    border-radius: 0 0 24px 24px;
}

.navbar-nav .nav-link {
    background: var(--neuro-bg-secondary);
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    border-radius: 14px;
    margin: 0 6px;
}
```

---

### 4. Formularios Neumórficos

#### Características:
- **Inputs**: Efecto hundido (inset shadows)
- **Focus**: Eleva el campo con sombras externas
- **Estilo**: Minimalista sin bordes

```css
.form-control, .form-select {
    background: var(--neuro-bg-secondary);
    border: none;
    border-radius: 14px;
    box-shadow: var(--neuro-shadow-inset-light), var(--neuro-shadow-inset-dark);
}

.form-control:focus {
    box-shadow: var(--neuro-shadow-hover-light), var(--neuro-shadow-hover-dark);
}
```

---

### 5. Tablas Neumórficas

#### Características:
- **Container**: Card neumórfico con border-radius
- **Header**: Fondo con gradiente suave
- **Rows hover**: Eleva y resalta la fila

```css
.datos-tabla {
    background: var(--neuro-bg-secondary);
    border-radius: 20px;
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
}

.datos-tabla tbody tr:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(255, 122, 0, 0.15);
}
```

---

### 6. Badges Neumórficos

#### Características:
- **Efecto**: Elevado con doble sombra
- **Hover**: Se eleva más
- **Gradientes**: Verde/Naranja según tipo

```css
.indice-badge {
    background: var(--neuro-bg-secondary);
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    border-radius: 20px;
    padding: 10px 20px;
}

.fuente-eosda {
    background: linear-gradient(145deg, var(--agrotech-green), #34A853);
    color: white;
}
```

---

## 🛰️ Spinners Satelitales Neumórficos

### Spinner Orbital
```css
.satellite-spinner {
    width: 70px;
    height: 70px;
    position: relative;
    animation: satellite-orbit 3s linear infinite;
}

.satellite-spinner::after {
    border: 4px dashed var(--agrotech-green);
    border-radius: 50%;
    box-shadow: 0 0 30px rgba(46, 139, 87, 0.4),
                inset 0 0 15px rgba(255, 122, 0, 0.2);
}
```

### Barra de Progreso
```css
.satellite-progress {
    background: var(--neuro-bg-secondary);
    box-shadow: inset -4px -4px 8px rgba(255, 255, 255, 0.7),
                inset 4px 4px 8px rgba(46, 139, 87, 0.15);
    border-radius: 30px;
}
```

---

## 📱 Responsive Design

### Desktop (> 768px)
- Cards: border-radius 32px
- Navbar: links horizontales con margen
- Botones: padding 14px 28px

### Tablet (768px)
- Cards: border-radius 20px
- Navbar: collapsed menu
- Font-size reducido

### Mobile (< 480px)
- Cards: border-radius 16px
- Navbar: border-radius 0 0 16px 16px
- Padding reducido en todos los elementos

```css
@media (max-width: 768px) {
    .card {
        margin-bottom: 24px;
        border-radius: 20px;
    }
    
    .navbar-nav .nav-link {
        margin: 6px 0;
        text-align: center;
    }
}

@media (max-width: 480px) {
    .card {
        border-radius: 16px;
    }
    
    .navbar {
        border-radius: 0 0 16px 16px;
    }
}
```

---

## ✨ Animaciones y Transiciones

### Fade In Up
```css
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(40px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in-up {
    animation: fadeInUp 0.6s ease-out;
}
```

### Pulse Glow
```css
@keyframes pulseGlow {
    0%, 100% {
        box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    }
    50% {
        box-shadow: var(--neuro-shadow-hover-light), var(--neuro-shadow-hover-dark);
    }
}

.pulse-glow {
    animation: pulseGlow 2s ease-in-out infinite;
}
```

### Float Effect
```css
@keyframes float {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-10px);
    }
}

.neuro-float {
    animation: float 3s ease-in-out infinite;
}
```

---

## 🖼️ Integración de Logos

### Ubicaciones:
1. **Navbar**: Logo horizontal + texto
2. **Footer**: Isotipo circular + info
3. **Header flotante**: Logo + brand text (datos_guardados.html)

### Implementación:
```html
<!-- Navbar -->
<a class="navbar-brand neuro-float" href="#">
    <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech Logo" class="logo-agrotech">
    <span>AgroTech Histórico</span>
</a>

<!-- Footer -->
<img src="{% static 'img/agrotech-icon.png' %}" alt="AgroTech Icon" class="logo-agrotech">

<!-- Header flotante (datos_guardados.html) -->
<div class="agrotech-logo-header">
    <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech">
    <div class="agrotech-brand-text">AgroTech</div>
</div>
```

### Estilos:
```css
.logo-agrotech {
    height: 45px;
    margin-right: 12px;
    filter: drop-shadow(0 2px 8px rgba(255, 122, 0, 0.3));
}

.agrotech-logo-header {
    position: fixed;
    top: 24px;
    left: 24px;
    z-index: 1000;
    background: var(--neuro-bg-secondary);
    border-radius: 24px;
    padding: 16px 24px;
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
}
```

---

## 🎯 Guía de Uso

### 1. Aplicar a una Nueva Página

```html
{% extends 'informes/base.html' %}

{% block extra_css %}
<style>
    /* Los estilos neumórficos ya están en base.html */
    /* Solo agregar estilos específicos de la página */
</style>
{% endblock %}

{% block content %}
<div class="card datos-card">
    <div class="card-header">
        <h5><i class="fas fa-icon"></i> Título</h5>
    </div>
    <div class="card-body">
        <!-- Contenido -->
    </div>
</div>
{% endblock %}
```

### 2. Crear un Componente Neumórfico

```html
<div class="component-name" style="
    background: var(--neuro-bg-secondary);
    border-radius: 20px;
    padding: 20px;
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    transition: all 0.3s ease;
">
    Contenido
</div>
```

---

## 🔧 Troubleshooting

### Problema: Sombras no se ven correctamente
**Solución**: Verificar que el fondo del body sea un color sólido claro (no transparente)

### Problema: Hover no funciona en móvil
**Solución**: Usar `:active` en lugar de `:hover` para dispositivos táctiles

### Problema: Bordes se ven cortados
**Solución**: Agregar `overflow: visible;` al contenedor padre

---

## 📊 Comparación: Glassmorphism vs Neumorphism

| Característica | Glassmorphism | Neumorphism |
|----------------|---------------|-------------|
| **Fondo** | Transparente + blur | Opaco, colores suaves |
| **Sombras** | Simples | Dobles (luz + oscura) |
| **Borde** | Visible, translúcido | Sin borde |
| **Efecto** | Vidrio esmerilado | Relieve 3D |
| **Legibilidad** | Menor | Mayor |
| **Performance** | Más pesado (blur) | Más ligero |
| **Modernidad** | Muy moderno | Moderno clásico |

---

## 🚀 Próximos Pasos

1. ✅ Implementar en `base.html`
2. ✅ Actualizar `datos_guardados.html`
3. ⏳ Aplicar a `dashboard.html`
4. ⏳ Actualizar `lista_parcelas.html`
5. ⏳ Integrar logos reales
6. ⏳ Crear dark mode neumórfico

---

## 📚 Recursos

- **Documentación interna**: `/docs/NEUMORFISMO_AGROTECH_README.md`
- **Guía de integración de logos**: `/docs/GUIA_LOGOS_AGROTECH.md`
- **Diseño anterior (Glassmorphism)**: `/docs/GLASMORFISMO_AGROTECH_README.md`

---

## 👥 Créditos

**Diseño**: Sistema Neumorfismo Luminoso AgroTech  
**Desarrollado para**: AgroTech Histórico  
**Versión**: 2.0 - Enero 2025  

---

**© 2025 AgroTech Histórico - Agricultura de Precisión Inteligente** 🌾🛰️
