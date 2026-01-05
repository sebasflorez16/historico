# 📊 Análisis del Sistema Contable Actual

## ✅ Lo que YA existe y funciona

### 1. **RegistroEconomico** (models_clientes.py)
Sistema completo de contabilidad para servicios:

```python
class RegistroEconomico:
    - valor_servicio: Decimal (precio base)
    - descuento: DecimalField 0-100% 
    - valor_final: Decimal (auto-calculado)
    - pagado: Boolean
    - fecha_pago: DateTimeField
    - metodo_pago: CharField
    - referencia_pago: CharField
    - tipo_servicio: Choice (analisis_basico, analisis_completo, etc.)
```

**Se crea automáticamente cuando:**
- Usuario registra parcela con invitación (línea 1146 views.py)
- Se asocia a: invitacion + parcela

### 2. **ClienteInvitacion** (models_clientes.py)
Sistema de invitaciones con precio:

```python
class ClienteInvitacion:
    - costo_servicio: Decimal
    - pagado: Boolean
    - fecha_pago: DateTimeField
    - notas_pago: TextField
```

**Se usa en:**
- Vista de crear invitaciones (línea 948 views.py: precio_servicio)
- Al registrar parcela por token

### 3. **Informe** (models.py - ACTUALIZADO)
Modelo con campos de pago completos:

```python
class Informe:
    # Campos de pago (recién agregados)
    precio_base: Decimal
    descuento_porcentaje: Decimal 0-100%
    precio_final: Decimal (auto-calculado)
    estado_pago: Choice (pagado/pendiente/vencido/parcial/cortesia)
    monto_pagado: Decimal
    saldo_pendiente: Decimal (auto-calculado)
    fecha_pago: DateTimeField
    fecha_vencimiento: DateField
    metodo_pago: CharField
    referencia_pago: CharField
    notas_pago: TextField
    cliente: FK a ClienteInvitacion
    
    # Métodos
    - save(): Auto-calcula precio_final, saldo, estado
    - marcar_como_pagado()
    - registrar_pago_parcial()
    
    # Properties
    - esta_vencido
    - dias_vencido
    - porcentaje_pagado
```

---

## ❌ Lo que FALTABA (problemas encontrados)

### 1. Clase Informe Duplicada ✅ CORREGIDO
- Había 2 definiciones de `class Informe` (líneas 400 y 854)
- **Solución:** Eliminada la duplicación (854-967)
- Ahora solo existe UNA clase con todos los campos de pago

### 2. Generación de Informe SIN registro contable
`generar_informe_pdf()` (línea 1896 views.py):
- Crea el objeto `Informe`
- ❌ NO asigna precio
- ❌ NO crea RegistroEconomico
- ❌ NO vincula con cliente

### 3. Admin sin campos de pago
`InformeAdmin` (admin.py):
- Solo muestra: titulo_corto, parcela, periodo, fecha
- ❌ NO muestra estado_pago, precio, saldo

---

## 🎯 Plan de Integración

### Paso 1: Actualizar vista generar_informe_pdf ✅
```python
# Al crear Informe:
- Obtener cliente de parcela (si existe invitacion)
- Calcular precio base según periodo_analisis_meses
- Asignar fecha_vencimiento (ej: +30 días)
- Vincular con cliente
- Crear RegistroEconomico vinculado
```

### Paso 2: Actualizar InformeAdmin ✅
```python
# Añadir fieldsets:
fieldsets = [
    ('Información General', {...}),
    ('💰 Información de Pago', {
        'fields': ('estado_pago', 'precio_base', 'descuento_porcentaje',
                   'precio_final', 'monto_pagado', 'saldo_pendiente')
    }),
    ('📅 Fechas de Pago', {...}),
    ('💳 Detalles de Pago', {...}),
]

# Añadir a list_display:
'estado_pago', 'precio_final', 'saldo_pendiente'

# Añadir filtros:
list_filter = ('estado_pago', 'fecha_vencimiento')
```

### Paso 3: Crear Migración ✅
```bash
python manage.py makemigrations
python manage.py migrate
```

### Paso 4: Actualizar template detalle_parcela ✅
Mostrar informes con estado de pago:
- Estado: Pagado ✅ / Pendiente ⏳ / Vencido ⚠️
- Precio: $XX.XX
- Saldo: $XX.XX

---

## 🔄 Flujo Completo Propuesto

```
1. Usuario recibe invitación con costo_servicio
   ↓
2. Registra parcela → Crea RegistroEconomico
   ↓
3. Sistema genera Informe PDF →
   - Calcula precio según tipo análisis
   - Asigna cliente de la invitación
   - Crea estado_pago = 'pendiente'
   - Registra en RegistroEconomico
   ↓
4. Admin puede:
   - Marcar como pagado
   - Registrar pago parcial
   - Aplicar descuentos
   - Ver saldo pendiente
   ↓
5. Sistema auto-actualiza estado según:
   - Monto pagado
   - Fecha vencimiento
```

---

## 📋 Tabla de Precios Sugerida

| Tipo Análisis | Meses | Precio Base |
|---------------|-------|-------------|
| Básico        | 6     | $50.00      |
| Estándar      | 12    | $80.00      |
| Completo      | 24    | $120.00     |

---

## ✨ Mejoras Adicionales (Opcionales)

1. **Vista de facturación:**
   - Lista de informes pendientes de pago
   - Total por cobrar
   - Informes vencidos

2. **Notificaciones:**
   - Email cuando se genera informe
   - Recordatorio de pago próximo a vencer
   - Alerta de pago vencido

3. **Reportes financieros:**
   - Ingresos mensuales
   - Pagos pendientes
   - Descuentos aplicados

4. **Integración con pasarelas:**
   - Stripe / PayPal
   - Generar link de pago automático

---

## ⚙️ Configuración Recomendada

```python
# settings.py o .env
PRECIO_INFORME_BASICO = 50.00
PRECIO_INFORME_ESTANDAR = 80.00
PRECIO_INFORME_COMPLETO = 120.00
DIAS_VENCIMIENTO_PAGO = 30
```

---

**Fecha:** 2025-01-25  
**Estado:** Análisis completado  
**Próximo paso:** Implementar integración en generar_informe_pdf + admin
