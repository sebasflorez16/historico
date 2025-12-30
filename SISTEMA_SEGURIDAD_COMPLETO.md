# 🔐 Sistema de Seguridad y Autenticación - AgroTech Histórico

## Resumen Ejecutivo
Se ha implementado un **sistema completo de seguridad y gestión de sesiones** para proteger tanto a usuarios administrativos (superusuarios) como a clientes invitados en el proceso de registro de parcelas.

---

## 🎯 Mejoras de Seguridad Implementadas

### 1. **Configuración de Sesiones Seguras** (`settings.py`)

#### Timeouts y Expiración
```python
SESSION_COOKIE_AGE = 900  # 15 minutos de inactividad
SESSION_SAVE_EVERY_REQUEST = True  # Renovar en cada request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Cerrar al cerrar navegador
SESSION_ABSOLUTE_TIMEOUT = 7200  # 2 horas máximo (incluso con actividad)
```

#### Seguridad de Cookies
```python
SESSION_COOKIE_HTTPONLY = True  # Prevenir acceso desde JavaScript
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS en producción
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF adicional
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
```

#### Protección contra Fijación de Sesión
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'agrotech_sessionid'
```

---

### 2. **Middleware de Timeout Absoluto** (`informes/middleware.py`)

**Función:** Cierra automáticamente la sesión después de 2 horas, incluso si hay actividad continua.

**Características:**
- ✅ Registra timestamp de inicio de sesión
- ✅ Calcula tiempo transcurrido en cada request
- ✅ Logout automático al exceder `SESSION_ABSOLUTE_TIMEOUT`
- ✅ Mensaje informativo al usuario
- ✅ Logging de eventos de expiración

**Flujo:**
```
Login → session_start_time registrado
   ↓
Cada Request → Verificar tiempo transcurrido
   ↓
> 2 horas? → Logout automático + mensaje
```

---

### 3. **Sistema de Invitaciones Reforzado** (`models_clientes.py`)

#### Nuevos Campos de Seguridad
```python
intentos_uso = models.IntegerField(default=0)
max_intentos = models.IntegerField(default=3)
bloqueada = models.BooleanField(default=False)
ip_ultimo_intento = models.GenericIPAddressField(blank=True, null=True)
```

#### Nuevas Propiedades y Métodos
- **`puede_usarse`**: Validación completa antes de permitir uso
- **`registrar_intento(ip)`**: Auditoría de intentos con IP
- **`marcar_como_utilizada(parcela)`**: Invalidación automática del token

---

### 4. **Vista de Registro con Validaciones Múltiples** (`views.py`)

#### Verificaciones Implementadas

1. **Token ya utilizado** → Error: "Invitación ya utilizada"
2. **Token bloqueado** → Error: "Invitación bloqueada por seguridad"
3. **Token expirado** → Error: "Invitación expirada"
4. **No puede usarse** → Error: "Invitación no disponible"
5. **Parcela ya asociada** → Error: "Parcela ya registrada"
6. **Límite de intentos** → Bloqueo automático tras 3 intentos

#### Auditoría y Logging
```python
- Captura de IP del cliente en cada intento
- Logging detallado de todos los eventos
- Registro de intentos fallidos
- Marca temporal de utilización
```

#### Invalidación de Token Post-Uso
```python
invitacion.marcar_como_utilizada(parcela)
# → estado = 'utilizada'
# → bloqueada = True
# → Imposible reutilizar
```

---

### 5. **Login Mejorado con Auditoría** (`views.py`)

#### Características
- ✅ Detección de sesión expirada (mensaje específico)
- ✅ Inicialización de `session_start_time`
- ✅ Logging de IP en cada intento de login
- ✅ Auditoría de intentos fallidos
- ✅ Redirección diferenciada (superuser vs regular user)

```python
# Inicializar sesión segura
request.session['session_start_time'] = timezone.now().isoformat()

# Log con IP
logger.info(f"✅ Usuario '{username}' inició sesión desde IP: {get_client_ip(request)}")
```

---

### 6. **Logout con Limpieza Total** (`views.py`)

```python
@login_required
def user_logout(request):
    username = request.user.username
    request.session.flush()  # Eliminar TODOS los datos de sesión
    logout(request)
    logger.info(f"✅ Usuario '{username}' cerró sesión correctamente")
    return redirect('informes:login')
```

**Previene:**
- Reutilización de sesiones antiguas
- Persistencia de datos sensibles
- Fijación de sesión

---

### 7. **Templates con Feedback de Seguridad**

#### `exito.html`
```html
<!-- Alerta de token invalidado -->
{% if token_invalidado %}
<div class="alert alert-warning">
    <i class="fas fa-shield-alt"></i>
    Por seguridad, tu token ha sido invalidado automáticamente
    y no puede ser reutilizado.
</div>
{% endif %}
```

#### `registro.html`
```html
<!-- Intentos restantes -->
{% if intentos_restantes %}
<div class="alert alert-warning">
    Tienes {{ intentos_restantes }} intento(s) restante(s).
    La invitación se bloqueará tras múltiples intentos fallidos.
</div>
{% endif %}
```

---

## 🛡️ Capas de Protección

### Para Usuarios Autenticados (Superusers y Staff)

| Capa | Protección | Implementación |
|------|------------|----------------|
| **1. Timeout Inactividad** | 15 minutos sin actividad | `SESSION_COOKIE_AGE` |
| **2. Timeout Absoluto** | 2 horas máximo | `SessionAbsoluteTimeoutMiddleware` |
| **3. Cierre de Navegador** | Sesión expira | `SESSION_EXPIRE_AT_BROWSER_CLOSE` |
| **4. Cookies Seguras** | HTTPOnly, Secure, SameSite | `SESSION_COOKIE_*` |
| **5. Logout Manual** | Limpieza total de sesión | `request.session.flush()` |
| **6. Auditoría** | Log de IPs y eventos | Logger personalizado |

### Para Usuarios Invitados (Sin Autenticación)

| Capa | Protección | Implementación |
|------|------------|----------------|
| **1. Token Único** | Un solo uso por token | `estado = 'utilizada'` |
| **2. Expiración Temporal** | Fecha límite configurable | `fecha_expiracion` |
| **3. Límite de Intentos** | Máximo 3 intentos | `intentos_uso` |
| **4. Bloqueo Automático** | Tras 3 intentos fallidos | `bloqueada = True` |
| **5. Invalidación Post-Uso** | Token inutilizable después del registro | `marcar_como_utilizada()` |
| **6. Validación de Parcela** | Una parcela por invitación | `parcela = OneToOneField` |
| **7. Auditoría de IP** | Registro de intentos por IP | `ip_ultimo_intento` |

---

## 📊 Flujo de Seguridad

### Flujo de Usuario Autenticado

```
┌─────────────┐
│   LOGIN     │
└──────┬──────┘
       │ ✓ Credenciales válidas
       │ ✓ session_start_time registrado
       │ ✓ IP logged
       ↓
┌─────────────────┐
│   Dashboard     │ ← SESSION_COOKIE_AGE (15 min inactividad)
│   o Parcelas    │ ← SESSION_ABSOLUTE_TIMEOUT (2h máximo)
└──────┬──────────┘
       │
       ├─→ Actividad continua → Renovar sesión
       │
       ├─→ > 15 min inactividad → Logout + mensaje
       │
       ├─→ > 2 horas total → Logout automático
       │
       └─→ Cerrar navegador → Sesión eliminada
```

### Flujo de Usuario Invitado

```
┌─────────────────┐
│ URL + Token     │
└────────┬────────┘
         │
         ↓
    Verificaciones:
    ✓ Token existe?
    ✓ No utilizado?
    ✓ No bloqueado?
    ✓ No expirado?
    ✓ Sin parcela asociada?
    ✓ Intentos < 3?
         │
         ↓
┌─────────────────┐
│ Formulario      │
│ Registro        │
└────────┬────────┘
         │
         ↓ POST
    Registrar intento
    (intentos_uso++)
         │
         ├─→ Error? → Intentos < 3? → Permitir reintento
         │                          └→ Intentos >= 3 → BLOQUEAR
         │
         ↓ Éxito
    Crear Parcela
    marcar_como_utilizada()
    → estado = 'utilizada'
    → bloqueada = True
    → Token INVALIDADO
         │
         ↓
┌─────────────────┐
│  Éxito + Aviso  │
│ Token Invalidado│
└─────────────────┘
```

---

## 🔧 Configuración Recomendada para Producción

### 1. Habilitar HTTPS
```python
# settings.py
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

### 2. Configurar Dominio de Cookies
```python
SESSION_COOKIE_DOMAIN = '.agrotech.com'
CSRF_COOKIE_DOMAIN = '.agrotech.com'
```

### 3. Ajustar Timeouts según Necesidad
```python
# Para operaciones más largas:
SESSION_COOKIE_AGE = 1800  # 30 minutos
SESSION_ABSOLUTE_TIMEOUT = 10800  # 3 horas
```

### 4. Habilitar Logging Avanzado
```python
LOGGING = {
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'informes.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
        },
    },
}
```

---

## 🧪 Testing de Seguridad

### Pruebas Manuales

1. **Timeout de Inactividad**
   - Login → Esperar 16 minutos sin actividad → Verificar logout automático

2. **Timeout Absoluto**
   - Login → Actividad continua por 2 horas → Verificar logout automático

3. **Token de Invitación**
   - Usar token → Completar registro → Intentar reusar URL → Verificar error

4. **Límite de Intentos**
   - Ingresar datos incorrectos 3 veces → Verificar bloqueo

5. **Cierre de Navegador**
   - Login → Cerrar navegador → Reabrir → Verificar sesión cerrada

---

## 📝 Logs de Seguridad

### Ejemplos de Logs Generados

```
INFO ✅ Usuario 'admin' inició sesión desde IP: 192.168.1.100
INFO ⏰ Sesión expirada para usuario: cliente1 (timeout absoluto)
WARNING ⚠️ Intento de login fallido para usuario: hacker desde IP: 10.0.0.50
WARNING ⚠️ Intento de reutilizar invitación ya utilizada: abc123 desde IP: 172.16.0.20
INFO ✅ Parcela registrada exitosamente: token-456 - Lote Norte - IP: 192.168.1.105
INFO ✅ Usuario 'admin' cerró sesión correctamente
```

---

## ✅ Checklist de Seguridad Implementado

- [x] Timeout de sesión por inactividad (15 min)
- [x] Timeout absoluto de sesión (2 horas)
- [x] Cookies HTTPOnly y Secure
- [x] Protección CSRF mejorada
- [x] Cierre de sesión al cerrar navegador
- [x] Limpieza total de sesión en logout
- [x] Middleware de timeout personalizado
- [x] Tokens de invitación de un solo uso
- [x] Invalidación automática de tokens post-uso
- [x] Límite de intentos por invitación (3 máximo)
- [x] Bloqueo automático tras intentos fallidos
- [x] Validación de parcela única por invitación
- [x] Auditoría de IPs en intentos
- [x] Logging detallado de eventos de seguridad
- [x] Mensajes informativos al usuario
- [x] Prevención de reutilización de tokens
- [x] Prevención de fijación de sesión

---

## 🚀 Próximos Pasos (Opcional)

1. **Rate Limiting**: Limitar intentos de login por IP
2. **2FA**: Autenticación de dos factores para superusuarios
3. **Notificaciones**: Emails de alerta en eventos sospechosos
4. **Captcha**: Protección contra bots en formularios públicos
5. **Geofencing**: Restricción por ubicación geográfica
6. **IP Whitelist**: Lista de IPs permitidas para superusuarios

---

## 📞 Soporte

Para más información sobre el sistema de seguridad:
- **Documentación Técnica**: Ver código en `informes/views.py`, `models_clientes.py`, `middleware.py`
- **Configuración**: Ver `agrotech_historico/settings.py`
- **Logs**: Revisar `agrotech.log` para eventos de seguridad

---

**Última actualización**: Enero 2025
**Versión del sistema**: 2.0.0 (con seguridad reforzada)
