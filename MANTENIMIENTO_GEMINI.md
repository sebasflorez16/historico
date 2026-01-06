# 🔧 MANTENIMIENTO DEL SISTEMA DE OPTIMIZACIÓN GEMINI

## 📊 Monitoreo del Sistema

### Ver Consumo Diario
```bash
cd /Users/sebastianflorez/Documents/Agrotech\ Hisotrico
conda activate agro-rest
python test_optimizacion_gemini.py
```

### Consultar Informes en Django Shell
```python
python manage.py shell

from informes.models import InformeGenerado, AnalisisImagen
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import datetime

# Ver informes de hoy
hoy = datetime.now().date()
informes_hoy = InformeGenerado.objects.filter(fecha_generacion__date=hoy)

print(f"Informes generados hoy: {informes_hoy.count()}")
print(f"Tokens consumidos: {informes_hoy.aggregate(Sum('tokens_consumidos'))}")

# Ver por usuario
for user in User.objects.all():
    count = InformeGenerado.contar_informes_hoy(user)
    puede = InformeGenerado.puede_generar_informe(user, 3)
    print(f"{user.username}: {count}/3 informes - Puede generar: {puede}")

# Ver estadísticas de caché
total_cache = AnalisisImagen.objects.count()
print(f"\nImágenes en caché: {total_cache}")
```

---

## 🗑️ Limpieza de Datos

### Eliminar Caché Antiguo (>30 días)
```python
from informes.models import AnalisisImagen
from datetime import timedelta
from django.utils import timezone

fecha_limite = timezone.now() - timedelta(days=30)
antiguos = AnalisisImagen.objects.filter(fecha_analisis__lt=fecha_limite)

print(f"Registros a eliminar: {antiguos.count()}")
antiguos.delete()
print("✅ Caché antiguo eliminado")
```

### Limpiar Informes Antiguos (>90 días)
```python
from informes.models import InformeGenerado
from datetime import timedelta
from django.utils import timezone

fecha_limite = timezone.now() - timedelta(days=90)
antiguos = InformeGenerado.objects.filter(fecha_generacion__lt=fecha_limite)

print(f"Informes a archivar: {antiguos.count()}")
# Opcional: exportar antes de eliminar
# antiguos.delete()
```

---

## ⚙️ Ajustes de Configuración

### Modificar Límite Diario de Informes

**Archivo**: `informes/views.py`

```python
# Buscar la línea (~1920):
if not InformeGenerado.puede_generar_informe(usuario=request.user, limite_diario=3):

# Cambiar el 3 por el nuevo límite:
if not InformeGenerado.puede_generar_informe(usuario=request.user, limite_diario=5):
```

**También actualizar en**:
```python
# views.py - función detalle_parcela (~285):
limite_diario = 3  # Cambiar este valor
```

### Modificar Número de Imágenes por Informe

**Archivo**: `informes/utils/image_selector.py`

```python
# Línea ~12:
MAX_IMAGENES_POR_INFORME = 10  # Cambiar a 15, 20, etc.
```

**⚠️ IMPORTANTE**: Más imágenes = más tokens = más consumo de API

| Imágenes | Tokens Aprox | Informes/mes (tier gratuito) |
|----------|--------------|------------------------------|
| 5        | 2,500        | 20-24                        |
| 10       | 5,000        | 12-20                        |
| 15       | 7,500        | 8-13                         |
| 20       | 10,000       | 6-10                         |
| 30       | 15,000       | 4-6                          |

### Modificar Validez del Caché

**Archivo**: `informes/generador_pdf.py`

```python
# Buscar la línea (~380):
if ultimo_indice.analisis_gemini and edad_cache < timedelta(days=30):

# Cambiar días de validez:
if ultimo_indice.analisis_gemini and edad_cache < timedelta(days=60):
```

---

## 🔍 Diagnóstico de Problemas

### Problema: "Límite diario alcanzado" pero debería poder generar

**Solución**:
```python
# En Django shell
from informes.models import InformeGenerado
from django.contrib.auth.models import User

user = User.objects.get(username='nombre_usuario')
count = InformeGenerado.contar_informes_hoy(user)
print(f"Informes hoy: {count}")

# Si count es incorrecto, verificar timezone
from django.utils import timezone
print(f"Fecha/hora actual: {timezone.now()}")
print(f"Fecha actual: {timezone.now().date()}")

# Ver informes del usuario hoy
informes = InformeGenerado.objects.filter(
    usuario=user,
    fecha_generacion__date=timezone.now().date()
)
for i in informes:
    print(f"  - {i.fecha_generacion}: {i.parcela.nombre}")
```

### Problema: Caché no se está usando

**Verificación**:
```python
# En Django shell
from informes.models import AnalisisImagen

# Ver análisis en caché
for a in AnalisisImagen.objects.all()[:10]:
    print(f"{a.parcela.nombre} - {a.fecha_imagen} - {a.indice}")
    print(f"  Edad: {(timezone.now() - a.fecha_analisis).days} días")
```

**Revisar logs**:
```bash
# Ver logs del servidor
tail -f logs/django.log  # O donde estén los logs

# Buscar mensajes como:
# "💾 Usando análisis cacheado..."
# "🆕 Generando nuevo análisis..."
```

### Problema: Gemini API Key no funciona

**Verificación**:
```bash
# Verificar que la key está en .env
grep GEMINI_API_KEY .env

# Verificar en Django
python manage.py shell -c "
import os
from django.conf import settings
print(f'GEMINI_API_KEY configurada: {bool(os.getenv(\"GEMINI_API_KEY\"))}')
"
```

---

## 📈 Reportes y Estadísticas

### Crear Script de Reporte Mensual

**Archivo**: `scripts/reporte_gemini_mensual.py`

```python
#!/usr/bin/env python
"""
Genera reporte de uso mensual de Gemini AI
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import InformeGenerado, AnalisisImagen
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# Mes actual
hoy = timezone.now()
inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
fin_mes = (inicio_mes + relativedelta(months=1)) - timedelta(seconds=1)

# Estadísticas de informes
informes_mes = InformeGenerado.objects.filter(
    fecha_generacion__range=(inicio_mes, fin_mes)
)

total_informes = informes_mes.count()
total_tokens = informes_mes.aggregate(Sum('tokens_consumidos'))['tokens_consumidos__sum'] or 0
total_peticiones = informes_mes.aggregate(Sum('peticiones_api'))['peticiones_api__sum'] or 0
total_imagenes = informes_mes.aggregate(Sum('num_imagenes_analizadas'))['num_imagenes_analizadas__sum'] or 0

# Por usuario
por_usuario = informes_mes.values('usuario__username').annotate(
    total=Count('id'),
    tokens=Sum('tokens_consumidos')
).order_by('-total')

# Estadísticas de caché
cache_hits = AnalisisImagen.objects.filter(
    fecha_analisis__range=(inicio_mes, fin_mes)
).count()

print('='*70)
print(f'REPORTE MENSUAL DE USO GEMINI AI - {inicio_mes.strftime("%B %Y")}'.upper())
print('='*70)
print(f'\n📊 RESUMEN GENERAL')
print(f'  Total informes generados: {total_informes}')
print(f'  Total tokens consumidos: {total_tokens:,}')
print(f'  Total peticiones API: {total_peticiones}')
print(f'  Total imágenes analizadas: {total_imagenes}')
print(f'  Análisis en caché: {cache_hits}')
print(f'\n💰 PROMEDIO POR INFORME')
if total_informes > 0:
    print(f'  Tokens: {total_tokens/total_informes:,.0f}')
    print(f'  Imágenes: {total_imagenes/total_informes:.1f}')
    print(f'  Peticiones API: {total_peticiones/total_informes:.1f}')

print(f'\n👥 POR USUARIO')
for u in por_usuario:
    print(f'  {u["usuario__username"]}: {u["total"]} informes ({u["tokens"]:,} tokens)')

print(f'\n📈 PROYECCIÓN')
dias_transcurridos = (hoy - inicio_mes).days + 1
dias_mes = 30
proyeccion_informes = (total_informes / dias_transcurridos) * dias_mes
proyeccion_tokens = (total_tokens / dias_transcurridos) * dias_mes

print(f'  Informes proyectados al final del mes: {proyeccion_informes:.0f}')
print(f'  Tokens proyectados al final del mes: {proyeccion_tokens:,.0f}')

# Verificar límite tier gratuito
LIMITE_TOKENS_TIER_GRATUITO = 60000
if proyeccion_tokens > LIMITE_TOKENS_TIER_GRATUITO:
    print(f'\n⚠️  ADVERTENCIA: Se excederá el límite del tier gratuito!')
    print(f'  Límite: {LIMITE_TOKENS_TIER_GRATUITO:,} tokens')
    print(f'  Proyección: {proyeccion_tokens:,.0f} tokens')
    print(f'  Exceso: {proyeccion_tokens - LIMITE_TOKENS_TIER_GRATUITO:,.0f} tokens')
else:
    print(f'\n✅ Dentro del límite del tier gratuito')
    print(f'  Uso proyectado: {(proyeccion_tokens/LIMITE_TOKENS_TIER_GRATUITO)*100:.1f}%')

print('='*70 + '\n')
```

**Ejecutar**:
```bash
python scripts/reporte_gemini_mensual.py
```

---

## 🔄 Actualización del Sistema

### Si se obtiene Plan de Pago de Gemini

1. **Habilitar análisis completo (30 imágenes)**:
   ```python
   # informes/views.py - agregar parámetro tipo_analisis
   tipo_analisis = request.POST.get('tipo_analisis', 'rapido')
   
   # informes/generador_pdf.py
   indices_seleccionados, stats = image_selector.seleccionar_mejores_imagenes(
       indices_mensuales, tipo_analisis=tipo_analisis  # 'rapido' o 'completo'
   )
   ```

2. **Actualizar UI para selección de tipo**:
   ```django
   <!-- templates/informes/parcelas/detalle.html -->
   <select id="tipoAnalisis" class="form-control">
       <option value="rapido">Análisis Rápido (10 imágenes)</option>
       <option value="completo">Análisis Completo (30 imágenes)</option>
   </select>
   ```

3. **Aumentar límites**:
   ```python
   # views.py
   limite_diario = 10  # Aumentar a 10 o más
   ```

---

## 🔐 Seguridad

### Proteger API Key

**Nunca commitear `.env` al repositorio**:
```bash
# .gitignore (verificar que contenga)
.env
*.env
```

### Rotar API Key Periodicamente
```bash
# 1. Generar nueva key en Google Cloud Console
# 2. Actualizar .env
GEMINI_API_KEY=nueva_key_aqui

# 3. Reiniciar servidor
python manage.py runserver
```

---

## 📞 Contacto y Soporte

Para problemas técnicos:
1. Verificar logs del servidor
2. Ejecutar `test_optimizacion_gemini.py`
3. Revisar configuración en `.env`
4. Consultar documentación en `OPTIMIZACION_GEMINI_COMPLETA.md`

---

**Última Actualización**: 2024  
**Versión del Sistema**: 1.0  
**Estado**: Producción ✅
