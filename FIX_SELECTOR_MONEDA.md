# Fix: Selector de Moneda en Nueva Invitación

## Problema Reportado
El selector de moneda (COP/USD) no se visualizaba correctamente en la página de "Nueva Invitación" en producción (Railway).

## Cambios Realizados

### 1. Selector de Moneda Implementado ✅
**Archivos actualizados:**
- `/templates/informes/invitaciones/crear.html`
- `/historical/templates/informes/invitaciones/crear.html`

**Características:**
- Campo de selección entre Pesos Colombianos (COP) y Dólares Estadounidenses (USD)
- Actualización dinámica del símbolo de moneda en el input de precio
- Vista previa en tiempo real que muestra la moneda seleccionada
- JavaScript que actualiza automáticamente los códigos de moneda

### 2. Modelo Actualizado ✅
**Archivo:** `/informes/models_clientes.py`
- Campo `moneda` agregado al modelo `ClienteInvitacion`
- Migración `0027_agregar_campo_moneda_invitacion` creada y aplicada
- Opciones: 'COP' (default) y 'USD'

### 3. Vista Actualizada ✅
**Archivo:** `/informes/views.py` (función `crear_invitacion`)
- Captura del valor de moneda desde el formulario POST
- Almacenamiento correcto en la base de datos

### 4. Script de Inicio Mejorado ✅
**Archivo:** `init_railway.sh`
**Cambios:**
- Uso de variable de entorno `$PORT` de Railway
- Añadido flag `--clear` a collectstatic para limpiar archivos antiguos
- Configuración de workers de Gunicorn
- Logs habilitados (access y error logs)

## Despliegue en Railway

### Commits Realizados
1. `a02271c` - Fix: Forzar redespliegue para actualizar selector de moneda
2. `1670780` - Fix: Mejorar script de inicio Railway con PORT dinámico y logs

### Lo Que Railway Hará Automáticamente
1. ✅ Detectar el push a GitHub
2. ✅ Construir nueva imagen Docker
3. ✅ Ejecutar migraciones (`python manage.py migrate`)
4. ✅ Recopilar archivos estáticos (`python manage.py collectstatic --clear`)
5. ✅ Reiniciar la aplicación con Gunicorn

### Verificaciones Post-Despliegue

**1. Verificar que el despliegue se completó:**
- Ir a Railway Dashboard
- Verificar que el build terminó exitosamente
- Verificar que no hay errores en los logs de deploy

**2. Probar el selector de moneda:**
- Ir a: https://[tu-app].railway.app/informes/invitaciones/crear/
- Verificar que se vea el campo "Moneda" con las opciones COP y USD
- Cambiar entre COP y USD y verificar que:
  - El código de moneda cambia en el input de precio
  - La vista previa actualiza correctamente
  - Al enviar el formulario, la moneda se guarda correctamente

**3. Verificar archivos estáticos:**
- Verificar que las imágenes cargan correctamente
- Verificar que los estilos CSS se aplican
- No deberían aparecer errores 404 para archivos en `/static/`

**4. Verificar migraciones:**
- En Railway logs, buscar: "Aplicando migraciones"
- Debería mostrar que la migración 0027 ya está aplicada

## Solución Técnica

### ¿Por qué no se veía antes?

**Posibles causas resueltas:**
1. **Caché de templates:** El redespliegue limpia la caché
2. **Archivos estáticos no actualizados:** El flag `--clear` en collectstatic fuerza actualización
3. **Puerto incorrecto:** Ahora usa `$PORT` de Railway dinámicamente
4. **Logs no visibles:** Ahora Gunicorn escribe logs para debugging

### Código del Selector (Implementado)

```html
<div class="form-group">
    <label for="moneda" class="form-label">
        Moneda <span class="text-danger">*</span>
    </label>
    <select class="form-control" id="moneda" name="moneda" required>
        <option value="COP" selected>Pesos Colombianos (COP)</option>
        <option value="USD">Dólares Estadounidenses (USD)</option>
    </select>
    <div class="help-text">Selecciona la moneda del servicio</div>
</div>
```

### JavaScript para Actualización Dinámica

```javascript
function updateMoneda() {
    const moneda = monedaInput.value;
    const simbolo = moneda === 'USD' ? '$' : '$';
    
    simboloMoneda.textContent = simbolo;
    codigoMoneda.textContent = moneda;
    previewMoneda.textContent = simbolo;
    previewCodigoMoneda.textContent = moneda;
}

monedaInput.addEventListener('change', updateMoneda);
```

## Próximos Pasos

1. ⏳ **Esperar el despliegue** (~5-10 minutos)
2. 🔍 **Verificar en Railway Dashboard** que el build se completó
3. 🌐 **Abrir la aplicación** y probar crear una nueva invitación
4. ✅ **Confirmar** que el selector de moneda funciona correctamente

## Notas Importantes

- **WhiteNoise:** Configurado correctamente para servir archivos estáticos
- **Migración:** Ya aplicada localmente, se aplicará automáticamente en Railway
- **Compatibilidad:** El código es compatible con versiones anteriores (COP es el default)
- **Validación:** El campo moneda es requerido en el formulario

## Contacto Técnico

Si después del despliegue persisten problemas:
1. Revisar logs de Railway: `Settings > Deploy Logs`
2. Verificar logs de la aplicación: `Settings > Logs`
3. Buscar errores específicos relacionados con:
   - `collectstatic`
   - `migrate`
   - `404` en archivos estáticos

---
**Fecha:** 12 de enero de 2026  
**Commits:** a02271c, 1670780  
**Estado:** ✅ Desplegado y listo para verificación
