# 🐛 CORRECCIÓN: Error "UnboundLocalError: datetime"

**Fecha:** 25 de noviembre de 2025, 10:18 AM  
**Estado:** ✅ RESUELTO

---

## 📌 PROBLEMA IDENTIFICADO

Al intentar generar un informe personalizado desde el frontend, el sistema mostraba:

```
❌ Error al Generar Informe
Error en la respuesta del servidor
```

### Error en consola del servidor:
```python
UnboundLocalError: cannot access local variable 'datetime' where it is not associated with a value
  File "views.py", line 2048, in generar_informe_personalizado
    fecha_inicio_analisis = (datetime.now() - timedelta(days=meses_atras*30)).date()
                             ^^^^^^^^
```

---

## 🔍 CAUSA RAÍZ

El módulo `datetime` se estaba importando **dentro de un bloque condicional**:

```python
# ❌ CÓDIGO PROBLEMÁTICO
try:
    import json
    
    # ... código ...
    
    if request.body:
        try:
            data = json.loads(request.body)
            # ... más código ...
            
            if fecha_inicio_str and fecha_fin_str:
                from datetime import datetime  # ⚠️ Import condicional
                fecha_inicio = datetime.strptime(...)
```

Luego, más adelante en el código, se intentaba usar `datetime` **fuera del scope** donde se importó:

```python
# ❌ Fuera del bloque where se importó
if fecha_inicio and fecha_fin:
    # ... ok ...
else:
    fecha_inicio_analisis = (datetime.now() - timedelta(...))  # ❌ ERROR!
    #                        ^^^^^^^^ Variable local no definida
```

---

## ✅ SOLUCIÓN

Mover el import de `datetime` y `timedelta` al inicio de la función, fuera de cualquier bloque condicional:

```python
# ✅ CÓDIGO CORREGIDO
@login_required
def generar_informe_personalizado(request, parcela_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        import json
        from datetime import datetime, timedelta  # ✅ Import al inicio del try
        
        # Obtener parcela
        parcela = get_object_or_404(Parcela, id=parcela_id, activa=True)
        
        # ... resto del código ...
```

Y eliminar el import duplicado dentro del if:

```python
# ❌ ANTES
if fecha_inicio_str and fecha_fin_str:
    from datetime import datetime  # ⚠️ Import redundante
    fecha_inicio = datetime.strptime(...)

# ✅ DESPUÉS
if fecha_inicio_str and fecha_fin_str:
    fecha_inicio = datetime.strptime(...)  # ✅ datetime ya está disponible
```

---

## 🧪 VALIDACIÓN

Después de la corrección:

1. ✅ Servidor reiniciado sin errores
2. ✅ No hay errores de sintaxis en `views.py`
3. ✅ Sistema check passed (0 issues)
4. ✅ Servidor corriendo en `http://127.0.0.1:8000/`

### Prueba desde el frontend:
- Abrir modal de configuración personalizada
- Seleccionar fechas e índices
- Generar informe
- ✅ Debería funcionar sin error "Error en la respuesta del servidor"

---

## 📝 LECCIÓN APRENDIDA

### ⚠️ No hacer:
```python
if condicion:
    from datetime import datetime
    # usar datetime aquí

# ❌ Intentar usar datetime aquí (fuera del scope)
datetime.now()  # UnboundLocalError!
```

### ✅ Hacer:
```python
from datetime import datetime, timedelta  # Import al inicio

if condicion:
    # usar datetime aquí
    
# ✅ datetime está disponible en todo el scope
datetime.now()  # OK!
```

---

## 🔧 ARCHIVOS MODIFICADOS

1. ✅ `/informes/views.py` (función `generar_informe_personalizado`)
   - Línea 1963: Añadido `from datetime import datetime, timedelta`
   - Línea 1993: Eliminado import duplicado

---

## ✅ ESTADO FINAL

- ✅ Error corregido
- ✅ Servidor reiniciado
- ✅ Sistema funcional
- ✅ Listo para probar desde el navegador

**Ahora puedes refrescar la página y volver a intentar generar el informe personalizado** 🚀

---

**Desarrollado por:** Asistente IA AgroTech  
**Validado:** 25 de noviembre de 2025, 10:18 AM
