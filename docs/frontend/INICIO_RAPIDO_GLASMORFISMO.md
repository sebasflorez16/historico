# 🚀 INICIO RÁPIDO - Glasmorfismo AgroTech

## ⚡ 3 Pasos para Activar el Nuevo Diseño

### 1️⃣ Copiar los Logos (2 minutos)

Guarda las dos imágenes que te envié en:

```bash
historical/static/img/agrotech-logo.png    # Logo completo horizontal
historical/static/img/agrotech-icon.png    # Ícono circular
```

**Ruta completa**:
```
/Users/sebasflorez16/Documents/AgroTech Historico/historical/static/img/
```

### 2️⃣ Recolectar Static Files (1 minuto)

Abre terminal en la carpeta del proyecto y ejecuta:

```bash
cd /Users/sebasflorez16/Documents/AgroTech\ Historico/historical
python manage.py collectstatic --noinput
```

### 3️⃣ Reiniciar Servidor (30 segundos)

```bash
# Si el servidor está corriendo, detenerlo (Ctrl+C)
# Luego iniciarlo nuevamente:
python manage.py runserver
```

---

## ✅ Verificación

Abre el navegador en:
```
http://127.0.0.1:8000/informes/parcelas/[ID]/datos-guardados/
```

**Deberías ver**:
- ✅ Logo AgroTech flotante en esquina superior izquierda
- ✅ Fondo con degradado suave (gris → verde → naranja)
- ✅ Tarjetas semitransparentes con efecto cristal
- ✅ Animaciones suaves al pasar el cursor
- ✅ Colores verde y naranja en toda la interfaz
- ✅ Spinner satelital 🛰️ al descargar imágenes

---

## 🎨 ¿Qué Cambió?

### Antes ❌
```
┌─────────────────────────────┐
│ AgroTech (texto simple)     │
│ Datos Guardados             │
│                             │
│ [Tarjetas blancas básicas]  │
│ [Botones Bootstrap default] │
└─────────────────────────────┘
```

### Después ✅
```
┌─────────────────────────────┐
│ 🛰️ agrotech. [Logo flotante]│
│                             │
│ Datos Guardados             │
│ [Fondo degradado suave]     │
│                             │
│ [Tarjetas glassmorphism]    │
│ [Efecto cristal + blur]     │
│ [Animaciones fluidas]       │
│ [Colores verde + naranja]   │
└─────────────────────────────┘
```

---

## 🔧 Si Algo No Funciona

### Logo no aparece ❌
```bash
# Verificar que el archivo existe:
ls -la historical/static/img/

# Debe mostrar:
agrotech-logo.png
agrotech-icon.png

# Si no están, copiarlos nuevamente
```

### Estilos no se aplican ❌
```bash
# Limpiar caché del navegador:
# Chrome/Edge: Ctrl + Shift + R (Windows/Linux)
# Chrome/Edge: Cmd + Shift + R (Mac)

# O abrir en modo incógnito:
# Ctrl + Shift + N (Windows/Linux)
# Cmd + Shift + N (Mac)
```

### Error 404 en static files ❌
```bash
# Verificar settings.py:
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Ejecutar collectstatic nuevamente:
python manage.py collectstatic --noinput
```

---

## 📱 Probar en Móvil

1. Obtén tu IP local:
```bash
# En terminal:
ipconfig getifaddr en0   # Mac
hostname -I              # Linux
ipconfig                 # Windows
```

2. Abre en el móvil (misma red WiFi):
```
http://TU_IP:8000/informes/parcelas/[ID]/datos-guardados/
```

3. Verifica:
   - ✅ Logo más pequeño
   - ✅ Botones apilados verticalmente
   - ✅ Tarjetas en columna única
   - ✅ Todo legible y funcional

---

## 🎯 Páginas Ya Actualizadas

| Página | Estado | URL |
|--------|--------|-----|
| Datos Guardados | ✅ 100% | `/parcelas/[ID]/datos-guardados/` |
| Base Template | ✅ 100% | Todos los templates heredan |
| Dashboard | 🟡 Parcial | Heredan estilos base |
| Galería | 🟡 Parcial | Heredan estilos base |
| Login | 🟡 Parcial | Heredan estilos base |

---

## 📚 Documentación Completa

Si necesitas más detalles:

1. **Sistema de Diseño**: `GLASMORFISMO_AGROTECH_README.md`
2. **Guía de Logos**: `GUIA_LOGOS_AGROTECH.md`
3. **Resumen Ejecutivo**: `RESUMEN_EJECUTIVO_GLASMORFISMO.md`

---

## 🎨 Usar el Diseño en Nuevas Páginas

### Plantilla Base:
```html
{% extends 'informes/base.html' %}
{% load static %}

{% block extra_css %}
<style>
    /* Tus estilos personalizados aquí */
    /* Las variables CSS ya están disponibles */
</style>
{% endblock %}

{% block content %}
<!-- Logo flotante (opcional) -->
<div class="agrotech-logo-header">
    <img src="{% static 'img/agrotech-logo.png' %}" alt="AgroTech">
    <span class="agrotech-brand-text">agrotech.</span>
</div>

<!-- Tarjeta glassmorphism -->
<div class="datos-card" style="padding: 24px;">
    <h3 style="color: var(--agrotech-green);">Título</h3>
    <p>Contenido con efecto cristal automático</p>
</div>

<!-- Botón AgroTech -->
<button class="btn btn-success">
    <i class="fas fa-check"></i> Acción
</button>
{% endblock %}
```

---

## 🚀 Próximo Sprint (Opcional)

Si quieres expandir el diseño:

1. **Dashboard**: Aplicar glassmorphism a todas las tarjetas
2. **Login**: Logo grande centrado + formulario glassmorphism
3. **Galería**: Lightbox con efecto cristal
4. **Formularios**: Inputs con glassmorphism
5. **Footer**: Agregar con logo y links

---

## 💡 Tips Rápidos

### Usar Variables CSS:
```css
color: var(--agrotech-green);      /* Verde #2E8B57 */
color: var(--agrotech-orange);     /* Naranja #FF7A00 */
background: var(--glass-bg);       /* Fondo semitransparente */
box-shadow: var(--shadow-soft);    /* Sombra suave */
```

### Crear Tarjeta Rápida:
```html
<div class="datos-card text-center" style="padding: 24px;">
    <div style="font-size: 2.5rem;">🌾</div>
    <h3 style="color: var(--agrotech-green);">Título</h3>
    <p class="text-muted">Descripción</p>
</div>
```

### Agregar Notificación:
```javascript
showToast('✅ Operación exitosa', 'success');
showToast('❌ Error ocurrido', 'error');
showToast('⚠️ Advertencia', 'warning');
```

---

## ✅ Checklist Rápido

- [ ] Logos copiados en `static/img/`
- [ ] Ejecutado `collectstatic`
- [ ] Servidor reiniciado
- [ ] Caché del navegador limpiado
- [ ] Página de prueba abierta
- [ ] Logo visible en header
- [ ] Tarjetas con efecto cristal
- [ ] Animaciones funcionando
- [ ] Probado en móvil (opcional)

---

## 🎉 ¡Listo!

Si seguiste los 3 pasos iniciales, **tu interfaz AgroTech ya tiene el nuevo diseño Glasmorfismo Luminoso** aplicado.

**Disfruta el nuevo look profesional de AgroTech!** 🌿🛰️✨

---

**¿Necesitas ayuda?**  
Consulta los archivos de documentación completa o revisa el código en `datos_guardados.html` como referencia.
