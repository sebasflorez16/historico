# 🎯 PLAN: Panel de Demos en Dashboard Principal

## Contexto
El usuario quiere gestionar los demos **desde su dashboard** (no desde Django Admin),
con envío por WhatsApp/Email, tracking de conversiones, y reutilización de polígonos
al convertir un lead en cliente pagante.

## Lo que ya existe:
- Dashboard en `/informes/` con: parcelas, informes, economía, invitaciones, sistema
- Template: `templates/informes/dashboard.html` (846 líneas, Bootstrap 5)
- Views: `informes/views.py` → `dashboard()` (superusuario)
- URLs: `informes/urls.py` con `app_name='informes'`
- Modelo de invitaciones: `ClienteInvitacion` con email y WhatsApp
- Sistema demo: `DemoToken` + `DemoLead` ya funcional (10/10 tests)

## Implementación en 3 bloques:

### Bloque A: Vista + URL para gestión de demos
- `views_demo.py` → agregar `panel_demos()` (lista, crear, detalle, convertir)
- `urls.py` → agregar rutas `/informes/demos/`, `/informes/demos/crear/`, etc.
- Todo con `@login_required` + `@user_passes_test(is_superuser)`

### Bloque B: Templates del panel
- `templates/informes/demos/panel.html` → Lista de tokens + stats de conversión
- `templates/informes/demos/crear.html` → Formulario crear token + enviar
- `templates/informes/demos/detalle.html` → Detalle del lead + botón convertir
- Widget en `dashboard.html` → Tarjetas + acceso rápido a demos

### Bloque C: Conversión Lead → Parcela real
- Vista `convertir_lead()` que:
  1. Toma la geometría del `DemoLead`
  2. Crea una `Parcela` real con esa misma geometría
  3. Marca `DemoLead.convertido_a_cliente = True`
  4. Redirige al detalle de la nueva parcela

## Archivos a crear/modificar:
```
informes/views_demo.py         → AGREGAR vistas panel (con @login_required)
informes/urls.py               → AGREGAR rutas /demos/*
templates/informes/demos/      → CREAR panel.html, crear.html, detalle.html
templates/informes/dashboard.html → AGREGAR widget de demos
```
