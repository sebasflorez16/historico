# 🛰️ GUÍA COMPLETA: Conexión Eficiente con EOSDA API

## 📋 Resumen Ejecutivo

EOSDA (EOS Data Analytics) requiere autenticación mediante **query parameter** usando `api-connect.eos.com` como base URL.

**Configuración correcta:**
```bash
Base URL: https://api-connect.eos.com
Método de autenticación: Query parameter (?api_key=xxx)
Headers: Solo Content-Type: application/json
```

---

## ✅ Configuración Actual (Funcionando)

### 1. Variables de Entorno

**Local (.env):**
```bash
EOSDA_API_KEY=apk.tu_api_key_completa_aqui
EOSDA_BASE_URL=https://api-connect.eos.com
```

**Railway (Producción):**
```bash
EOSDA_API_KEY=apk.3160391d89d7711663e46354c1f9b07e96b34bfb8964111ac18dc4ef58ed1d00
EOSDA_BASE_URL=https://api-connect.eos.com
```

### 2. Implementación en Código

**Archivo:** `informes/services/eosda_api.py`

```python
class EosdaAPIService:
    def __init__(self):
        self.api_key = settings.EOSDA_API_KEY
        self.base_url = settings.EOSDA_BASE_URL  # https://api-connect.eos.com
        self.session = requests.Session()
        
        # IMPORTANTE: NO usar headers de autenticación
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def _build_url(self, endpoint: str) -> str:
        """
        Construye URL con api_key como query parameter
        """
        endpoint = endpoint.lstrip('/')
        base = self.base_url.rstrip('/')
        url = f"{base}/{endpoint}"
        
        # Agregar api_key como parámetro
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}api_key={self.api_key}"
    
    def listar_campos(self):
        """
        Ejemplo de uso correcto
        """
        url = self._build_url("field-management/fields")
        # URL final: https://api-connect.eos.com/field-management/fields?api_key=xxx
        
        response = self.session.get(url, timeout=30)
        return response.json()
```

---

## 🔐 Métodos de Autenticación Probados

### ❌ Métodos que NO funcionan:

1. **Header x-api-key**
```python
headers = {'x-api-key': api_key}  # ❌ Error 403
```

2. **Header Authorization Bearer**
```python
headers = {'Authorization': f'Bearer {api_key}'}  # ❌ Error 403
```

3. **Base URL incorrecta**
```python
base_url = 'https://api.eos.com'  # ❌ No resuelve DNS
base_url = 'https://api.eosda.com'  # ❌ No existe
```

### ✅ Método que SÍ funciona:

**Query Parameter con api-connect.eos.com:**
```python
url = f"https://api-connect.eos.com/field-management/fields?api_key={api_key}"
response = requests.get(url, headers={'Content-Type': 'application/json'})
# ✅ Status 200 - 6 campos obtenidos
```

---

## 🚀 Endpoints Disponibles

### Field Management API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/field-management/fields` | GET | Listar todos los campos |
| `/field-management` | POST | Crear nuevo campo |
| `/field-management/{field_id}` | GET | Obtener campo específico |
| `/field-management/{field_id}` | PUT | Actualizar campo |
| `/field-management/{field_id}` | DELETE | Eliminar campo |
| `/field-management/fields/crop-types` | GET | Tipos de cultivos válidos (285 tipos) |

### Statistics API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/field-management/{field_id}/statistics` | GET | Obtener estadísticas (NDVI, NDMI, etc.) |

---

## 📊 Ejemplo de Petición Completa

```python
import requests

# Configuración
API_KEY = "apk.3160391d89d7711663e46354c1f9b07e96b34bfb8964111ac18dc4ef58ed1d00"
BASE_URL = "https://api-connect.eos.com"

# Construir URL
endpoint = "field-management/fields"
url = f"{BASE_URL}/{endpoint}?api_key={API_KEY}"

# Headers (solo Content-Type)
headers = {
    'Content-Type': 'application/json'
}

# Hacer petición
response = requests.get(url, headers=headers, timeout=30)

# Verificar respuesta
if response.status_code == 200:
    campos = response.json()
    print(f"✅ Éxito: {len(campos)} campos obtenidos")
    for campo in campos:
        print(f"  - {campo.get('name', 'Sin nombre')} (ID: {campo['id']})")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
```

**Resultado esperado:**
```
✅ Éxito: 6 campos obtenidos
  - Sin nombre (ID: 10800114)
  - Sin nombre (ID: 10800423)
  - Sin nombre (ID: 10800473)
  - Sin nombre (ID: 10804354)
  - Sin nombre (ID: 10842160)
  - Sin nombre (ID: 10842606)
```

---

## 🔧 Optimizaciones Implementadas

### 1. Caché de Peticiones

```python
class EosdaAPIService:
    def __init__(self):
        self._cultivos_validos_cache = None
    
    def obtener_cultivos_validos(self):
        if self._cultivos_validos_cache:
            return self._cultivos_validos_cache
        
        url = self._build_url("field-management/fields/crop-types")
        response = self.session.get(url, timeout=30)
        
        if response.status_code == 200:
            self._cultivos_validos_cache = response.json()
            return self._cultivos_validos_cache
```

**Beneficio:** Evita consultar tipos de cultivos repetidamente (285 tipos).

### 2. Timeout Apropiado

```python
response = self.session.get(url, timeout=30)
```

**Beneficio:** Evita que peticiones lentas bloqueen el sistema.

### 3. Manejo de Errores Robusto

```python
try:
    response = self.session.get(url, timeout=30)
    
    if response.status_code == 200:
        return {'exito': True, 'data': response.json()}
    elif response.status_code == 404:
        return {'exito': False, 'error': 'Campo no encontrado'}
    elif response.status_code == 403:
        return {'exito': False, 'error': 'API key inválida'}
    else:
        return {'exito': False, 'error': f'Error {response.status_code}'}
        
except requests.exceptions.Timeout:
    return {'exito': False, 'error': 'Timeout - EOSDA no respondió'}
except Exception as e:
    return {'exito': False, 'error': str(e)}
```

### 4. Session Reutilizable

```python
self.session = requests.Session()
```

**Beneficio:** Reutiliza conexiones TCP, mejora rendimiento en peticiones múltiples.

---

## 🧪 Pruebas y Verificación

### Test Local

```bash
# Ejecutar test actualizado
python test_eosda_actualizado.py

# Resultado esperado:
# ✅ ÉXITO - Conexión exitosa!
# 📊 Datos recibidos: Total de campos: 6
```

### Test en Railway (Producción)

```bash
# Opción 1: Verificar desde dashboard
https://tu-app.railway.app/sistema/estado/

# Opción 2: SSH a Railway
railway ssh
python manage.py shell

>>> from informes.services.eosda_api import EosdaAPIService
>>> service = EosdaAPIService()
>>> campos = service.listar_campos()
>>> print(f"Campos: {len(campos['fields'])}")
```

---

## ⚠️ Problemas Comunes y Soluciones

### Error 403: Missing Authentication Token

**Causa:** API key inválida o URL incorrecta

**Solución:**
1. Verificar que `EOSDA_BASE_URL=https://api-connect.eos.com`
2. Verificar que API key empiece con `apk.`
3. Regenerar API key en https://eos.com/dashboard

### Error de DNS: Failed to resolve

**Causa:** URL incorrecta (api.eos.com o api.eosda.com)

**Solución:**
```bash
# Cambiar a:
EOSDA_BASE_URL=https://api-connect.eos.com
```

### Timeout

**Causa:** EOSDA API lenta o no disponible

**Solución:**
- Aumentar timeout: `timeout=60`
- Implementar reintentos con backoff exponencial
- Verificar estado de EOSDA: https://status.eos.com

---

## 📈 Mejores Prácticas

### 1. Rate Limiting

```python
import time

class EosdaAPIService:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.5  # 500ms entre peticiones
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def listar_campos(self):
        self._rate_limit()
        # ... hacer petición
```

### 2. Logging Detallado

```python
import logging

logger = logging.getLogger(__name__)

def listar_campos(self):
    logger.info("Listando campos de EOSDA")
    url = self._build_url("field-management/fields")
    
    try:
        response = self.session.get(url, timeout=30)
        logger.info(f"EOSDA respondió: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Obtenidos {len(data)} campos")
            return data
    except Exception as e:
        logger.error(f"Error listando campos: {str(e)}")
        raise
```

### 3. Retry con Backoff

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def __init__(self):
    self.session = requests.Session()
    
    # Configurar reintentos automáticos
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    self.session.mount("https://", adapter)
```

---

## 🔒 Seguridad

### 1. No exponer API key en logs

```python
# ❌ MAL
logger.info(f"Using API key: {self.api_key}")

# ✅ BIEN
logger.info(f"Using API key: {self.api_key[:15]}...")
```

### 2. Variables de entorno

```python
# ❌ MAL - hardcoded
API_KEY = "apk.1234567890..."

# ✅ BIEN - desde entorno
API_KEY = os.getenv('EOSDA_API_KEY')
```

### 3. Validar antes de usar

```python
def validar_configuracion(self):
    if not self.api_key:
        raise ValueError("EOSDA_API_KEY no configurada")
    
    if not self.api_key.startswith('apk.'):
        raise ValueError("API key debe empezar con 'apk.'")
    
    if len(self.api_key) != 68:
        logger.warning(f"API key tiene longitud inusual: {len(self.api_key)}")
```

---

## 📚 Documentación Oficial

- **Dashboard EOSDA:** https://eos.com/dashboard
- **Documentación API:** https://doc.eos.com/
- **Field Management API:** https://doc.eos.com/docs/field-management-api/
- **Soporte:** support@eos.com

---

## ✅ Checklist de Conexión Exitosa

- [ ] Variable `EOSDA_API_KEY` configurada
- [ ] Variable `EOSDA_BASE_URL=https://api-connect.eos.com`
- [ ] API key válida (empieza con `apk.`, 68 caracteres)
- [ ] Cuenta EOSDA activa con acceso a Field Management API
- [ ] Test local exitoso (6 campos obtenidos)
- [ ] Test en producción exitoso
- [ ] Logs muestran peticiones exitosas
- [ ] Dashboard muestra "API EOSDA: Operativo"

---

**Última actualización:** 3 de enero de 2026  
**Estado:** ✅ Funcionando correctamente (6 campos sincronizados)
