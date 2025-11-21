# 🚀 Guía Rápida: Neumorfismo Luminoso AgroTech

## ⚡ Inicio Rápido en 5 Minutos

### 🎯 ¿Qué es el Neumorfismo Luminoso?
Diseño UI con efecto **3D suave** mediante doble sombra (luz + oscura) que crea la ilusión de elementos que emergen del fondo. Combina minimalismo con profundidad visual.

---

## 📦 Componentes Listos para Usar

### 1️⃣ Card Neumórfica

```html
<div class="card datos-card">
    <div class="card-header">
        <h5><i class="fas fa-chart-line"></i> Título</h5>
    </div>
    <div class="card-body">
        <p>Contenido de la tarjeta</p>
    </div>
</div>
```

**Características**:
- ✅ Efecto elevado 3D automático
- ✅ Hover: eleva más la tarjeta
- ✅ Borde superior gradiente (verde-naranja)
- ✅ Border-radius: 28-32px

---

### 2️⃣ Botón Neumórfico

```html
<button class="btn btn-primary">
    <i class="fas fa-save"></i> Guardar
</button>
```

**Estados**:
- **Normal**: Elevado con doble sombra
- **Hover**: Se eleva más (+2px)
- **Active**: Se hunde (efecto presión)

**Colores disponibles**:
- `btn-primary` → Verde (gradiente)
- `btn-success` → Verde claro
- `btn-warning` → Naranja

---

### 3️⃣ Badge Neumórfico

```html
<span class="indice-badge fuente-eosda">
    🛰️ EOSDA
</span>

<span class="indice-badge fuente-simulado">
    ⚠️ Simulado
</span>
```

---

### 4️⃣ Tabla Neumórfica

```html
<table class="table datos-tabla">
    <thead>
        <tr>
            <th>Fecha</th>
            <th>Índice</th>
            <th>Valor</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>2025-01-15</td>
            <td>NDVI</td>
            <td class="valor-positivo">0.85</td>
        </tr>
    </tbody>
</table>
```

**Hover**: Fila se eleva y resalta

---

### 5️⃣ Spinner Satelital

```html
<div class="image-download-spinner">
    <div class="icon">🛰️</div>
    <span>Descargando imagen satelital</span>
    <div class="loading-dots">
        <span></span>
        <span></span>
        <span></span>
    </div>
</div>
```

---

### 6️⃣ Formulario Neumórfico

```html
<div class="mb-3">
    <label class="form-label">Nombre</label>
    <input type="text" class="form-control" placeholder="Ingrese nombre">
</div>

<div class="mb-3">
    <label class="form-label">Tipo</label>
    <select class="form-select">
        <option>Opción 1</option>
        <option>Opción 2</option>
    </select>
</div>
```

**Características**:
- Efecto hundido (inset shadows)
- Focus: se eleva con sombras externas
- Sin bordes

---

## 🎨 Variables CSS Principales

```css
/* Copiar al inicio del <style> de tu página */
:root {
    --agrotech-orange: #FF7A00;
    --agrotech-green: #2E8B57;
    --neuro-bg-primary: #E8F0F8;
    --neuro-bg-secondary: #F5F7FA;
    
    /* Sombras elevadas */
    --neuro-shadow-light: -8px -8px 16px rgba(255, 255, 255, 0.8);
    --neuro-shadow-dark: 8px 8px 16px rgba(46, 139, 87, 0.15);
    
    /* Sombras hover */
    --neuro-shadow-hover-light: -12px -12px 24px rgba(255, 255, 255, 0.9);
    --neuro-shadow-hover-dark: 12px 12px 24px rgba(255, 122, 0, 0.2);
}
```

---

## 🔧 Crear un Componente Personalizado

### Paso 1: HTML Base
```html
<div class="mi-componente">
    Contenido
</div>
```

### Paso 2: Aplicar Estilo Neumórfico
```css
.mi-componente {
    background: var(--neuro-bg-secondary);
    border-radius: 20px;
    padding: 24px;
    box-shadow: var(--neuro-shadow-light), var(--neuro-shadow-dark);
    transition: all 0.3s ease;
}

.mi-componente:hover {
    transform: translateY(-4px);
    box-shadow: var(--neuro-shadow-hover-light), var(--neuro-shadow-hover-dark);
}
```

---

## 📱 Clases de Utilidad

### Animaciones
- `.fade-in-up` → Aparece desde abajo
- `.pulse-glow` → Pulso de brillo
- `.neuro-float` → Flotación suave

### Valores (para datos)
- `.valor-positivo` → Verde, negrita
- `.valor-neutro` → Gris
- `.valor-negativo` → Naranja, negrita

### Responsive
- Desktop: Automático
- Tablet (≤768px): Ajustes automáticos
- Mobile (≤480px): Optimizado táctil

---

## 🖼️ Integrar Logos

### En Navbar
```html
<a class="navbar-brand neuro-float" href="#">
    {% load static %}
    <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech" class="logo-agrotech">
    <span>AgroTech Histórico</span>
</a>
```

### Header Flotante (datos_guardados.html)
```html
<div class="agrotech-logo-header">
    <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech Logo">
    <div class="agrotech-brand-text">AgroTech</div>
</div>
```

---

## ✅ Checklist de Integración

- [ ] Extender de `base.html`
- [ ] Usar clases `.datos-card` para tarjetas
- [ ] Aplicar `.btn-primary` a botones principales
- [ ] Usar `.datos-tabla` para tablas
- [ ] Agregar `.fade-in-up` a elementos que aparecen
- [ ] Integrar logos en navbar/header
- [ ] Verificar responsive en móvil
- [ ] Probar hover/active en todos los botones

---

## 🎯 Template Página Completa

```html
{% extends 'informes/base.html' %}
{% load static %}

{% block title %}Mi Página - AgroTech{% endblock %}

{% block extra_css %}
<style>
    /* Estilos específicos de la página aquí */
    /* Los estilos neumórficos base ya están en base.html */
</style>
{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <h2 class="mb-4">
                <i class="fas fa-chart-bar text-success"></i>
                Título de la Página
            </h2>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6 mb-4">
            <div class="card datos-card fade-in-up">
                <div class="card-header">
                    <h5><i class="fas fa-database"></i> Datos</h5>
                </div>
                <div class="card-body">
                    <p>Contenido de la tarjeta</p>
                    <button class="btn btn-primary">
                        <i class="fas fa-sync"></i> Actualizar
                    </button>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-4">
            <div class="card datos-card fade-in-up" style="animation-delay: 0.1s;">
                <div class="card-header">
                    <h5><i class="fas fa-chart-line"></i> Gráfico</h5>
                </div>
                <div class="card-body">
                    <canvas id="miGrafico"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // JavaScript específico de la página
</script>
{% endblock %}
```

---

## 🔥 Tips Avanzados

### 1. Efecto Hundido (para inputs/áreas de texto)
```css
box-shadow: inset -4px -4px 8px rgba(255, 255, 255, 0.7),
            inset 4px 4px 8px rgba(46, 139, 87, 0.1);
```

### 2. Efecto Presionado (para botones activos)
```css
box-shadow: inset -6px -6px 12px rgba(255, 255, 255, 0.6),
            inset 6px 6px 12px rgba(46, 139, 87, 0.15);
transform: translateY(0);
```

### 3. Borde Superior Gradiente Animado
```css
.card::before {
    content: '';
    position: absolute;
    top: -3px;
    left: 30px;
    right: 30px;
    height: 6px;
    background: linear-gradient(90deg, var(--agrotech-green), var(--agrotech-orange));
    border-radius: 32px 32px 0 0;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.card:hover::before {
    opacity: 1;
}
```

---

## 📞 Soporte

**Documentación completa**: `NEUMORFISMO_AGROTECH_README.md`  
**Guía de logos**: `GUIA_LOGOS_AGROTECH.md`  

---

## 🎉 ¡Listo para Usar!

Con estos componentes puedes crear cualquier página del sistema AgroTech manteniendo el diseño neumórfico consistente y profesional.

**© 2025 AgroTech Histórico** 🌾🛰️
