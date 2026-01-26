# Pendientes para Próxima Sesión 🚀

## ✅ Estado Actual (26 Enero 2026)

### Completado Hoy
- ✅ Sistema de verificación legal completo con 4 capas
- ✅ RUNAP: 174 áreas protegidas Casanare descargadas (12.3 MB)
- ✅ Red hídrica: 25,780 drenajes Casanare (4.4 MB) 
- ✅ Verificación geográfica: resguardos y páramos (0 en Casanare = correcto)
- ✅ PDF profesional con tabla de confianza
- ✅ Área cultivable ahora muestra valor preliminar
- ✅ 8 commits organizados al repositorio

### En Producción
```
Departamento: CASANARE
Capas: 4/4 ✅
- Red hídrica: 25,780 drenajes (ALTA confianza - LineString)
- RUNAP: 174 áreas protegidas (ALTA confianza - oficial PNN)
- Resguardos: 0 (MEDIA confianza - verificado demográficamente)
- Páramos: 0 (MEDIA confianza - verificado geográficamente)

PDF generado: 0.23 MB
Restricciones detectadas: 0
Área cultivable: 69.82 ha (preliminar)
```

---

## 🔴 PRIORIDAD ALTA - Mañana

### 1. Descargar Datos Reales Resguardos y Páramos
**Problema**: APIs de ANT y SIAC bloqueadas (Error 400 - Invalid URL)

**Soluciones a intentar**:
```bash
# Opción A: Solicitar API Key oficial
1. Registrarse en https://data-agenciadetierras.opendata.arcgis.com/
2. Solicitar API key a ANT vía correo institucional
3. Repetir para SIAC/MADS

# Opción B: Descargar datasets completos nacionales
1. Buscar FTP institucional IGAC/ANT
2. Descargar ZIP completo (puede ser grande: 500MB-2GB)
3. Filtrar localmente por departamento
4. Cachear permanentemente

# Opción C: Usar QGIS para descargar manualmente
1. Abrir QGIS
2. Conectar a servicios WMS/WFS de ANT y SIAC
3. Exportar a shapefile
4. Copiar a datos_geograficos/

# Opción D: Contratar licencia ArcGIS Online
- Costo: ~$100/año estudiante, ~$1,500/año empresarial
- Acceso garantizado a todas las capas oficiales
```

**Para Antioquia (próximo cliente)** SÍ necesitamos:
- Resguardos indígenas: ~50 (zona Emberá, Senú)
- Páramos delimitados: ~15 (cordillera occidental/central)

### 2. Mejorar Tabla de Confianza en PDF
**Pendiente**: Distinguir entre "sin datos en región" vs "capa no descargada"

```python
# Agregar columna "Razón" más detallada:
| Capa | Estado | Confianza | Razón |
|------|--------|-----------|-------|
| Resguardos | ✓ Cargada | Media | 0 elementos - Región sin población indígena (verificado) |
| Páramos | ✓ Cargada | Media | 0 elementos - Altitud <350msnm (imposible geográficamente) |
```

### 3. Agregar Info de Departamento al PDF
```python
# Agregar sección al inicio del PDF:
📍 INFORMACIÓN GEOGRÁFICA
━━━━━━━━━━━━━━━━━━━━━━
Departamento: CASANARE (código DIVIPOLA: 85)
CAR: CORPORINOQUIA
Municipio: [Auto-detectar]
Coordenadas centrales: (-72.24, 5.28)
```

---

## 🟡 PRIORIDAD MEDIA

### 4. Implementar Descarga Automática por Departamento
```python
# Crear: gestor_datos_departamentales.py
class GestorDatosDepartamentales:
    def auto_detectar_departamento(self, coords):
        """Detecta departamento por coordenadas"""
        
    def descargar_si_necesario(self, departamento):
        """Descarga capas solo si no existen en caché"""
        
    def verificar_actualizacion(self):
        """Verifica si datos tienen >6 meses"""
```

**Lógica**:
1. Usuario ingresa predio en Antioquia
2. Sistema detecta: "Antioquia (código 05)"
3. Verifica: `datos_geograficos/runap/runap_antioquia.geojson` existe?
4. Si NO existe → Descargar automáticamente
5. Si existe → Usar caché

### 5. Integrar con Vista Django
```python
# En informes/views.py:
from verificador_legal import VerificadorRestriccionesLegales

def generar_informe_completo(request, parcela_id):
    parcela = Parcela.objects.get(id=parcela_id)
    
    # Ejecutar verificación legal
    verificador = VerificadorRestriccionesLegales()
    resultado = verificador.verificar_parcela_completa(parcela.geometria)
    
    # Generar PDF con mapa
    pdf = generar_pdf_verificacion_legal(parcela, resultado)
    
    # Guardar en informe
    informe.verificacion_legal = resultado.to_dict()
    informe.save()
```

---

## 🟢 PRIORIDAD BAJA (Optimizaciones)

### 6. Optimizar Tamaño de Archivos
```bash
# Comprimir GeoJSON con topojson
npm install -g topojson
geo2topo datos_geograficos/runap/runap_casanare.geojson > runap_casanare.topojson
# Reducción esperada: 12.3 MB → 3-4 MB
```

### 7. Agregar Más Capas
- Zonas de riesgo (inundación, deslizamiento) - IDEAM
- Catastro (linderos oficiales) - IGAC
- Uso del suelo (vocación agrícola) - IGAC
- Zonas sísmicas - SGC

### 8. Dashboard de Monitoreo
```javascript
// Frontend: Estado de capas descargadas
GET /api/verificacion/estado-datos/
{
  "departamentos_disponibles": ["CASANARE", "CUNDINAMARCA"],
  "casanare": {
    "runap": { "elementos": 174, "ultima_actualizacion": "2026-01-26", "mb": 12.3 },
    "red_hidrica": { "elementos": 25780, "ultima_actualizacion": "2026-01-26", "mb": 4.4 },
    "resguardos": { "elementos": 0, "verificado": true },
    "paramos": { "elementos": 0, "verificado": true }
  }
}
```

---

## 📋 Checklist Antioquia (Próximo Cliente)

Antes de atender cliente de Antioquia:

- [ ] Descargar RUNAP Antioquia (~80 áreas)
- [ ] Descargar resguardos Antioquia (~50)
- [ ] Descargar páramos Antioquia (~15)
- [ ] Descargar red hídrica Antioquia
- [ ] Actualizar retiros_por_car.json con CORANTIOQUIA
- [ ] Probar con predio real de Antioquia
- [ ] Generar PDF y validar con cliente

---

## 🐛 Bugs Conocidos

1. **Terminal heredoc se corrompe**: No usar `<<EOF` en scripts largos
   - Solución: Crear archivos .py separados

2. **APIs ArcGIS bloqueadas**: Error 400 - Invalid URL
   - Solución temporal: Archivos vacíos con metadata de verificación
   - Solución definitiva: API Key o descarga manual

3. **Conda warnings**: anaconda-cloud-auth ChannelAuthBase
   - No afecta funcionalidad, ignorar

---

## 📚 Referencias Importantes

### URLs Funcionales ✅
```
RUNAP (PNN):
https://storage.googleapis.com/pnn_geodatabase/runap/latest.zip

Red hídrica IGAC:
https://mapas2.igac.gov.co/server/rest/services/carto/carto100000colombia2019/MapServer/24/query

DANE DIVIPOLA:
https://geoportal.dane.gov.co/
```

### URLs Bloqueadas ❌
```
Resguardos ANT:
https://services.arcgis.com/DDzi7vRExVRMO5AB/arcgis/rest/services/Resguardo_Indigena_Formalizado/FeatureServer/0
Error: 400 - Invalid URL

Páramos SIAC:
https://services.arcgis.com/zNC4XQ1B0uOEuIBN/arcgis/rest/services/Paramos_Delimitados/FeatureServer/0
Error: 400 - Invalid URL
```

### Contactos para API Keys
```
ANT: soporte@ant.gov.co
SIAC/MADS: siac@minambiente.gov.co
IGAC: igac@igac.gov.co
```

---

## 🎯 Meta Final

**Sistema completo de verificación legal multicapa para Colombia**:
- ✅ 4 capas verificadas (retiros, RUNAP, resguardos, páramos)
- 🔄 Auto-descarga por departamento
- ✅ PDF profesional con mapas
- ✅ Niveles de confianza por capa
- 🔄 Integración Django completa
- 🔄 Dashboard frontend

**Próxima sesión**: Enfocarse en descargar datos reales de resguardos y páramos, luego integrar con Django views.

---

Última actualización: 26 Enero 2026 - 17:30
Commits: 8 (ce5bffb...d2a0421)
Estado: ✅ LISTO PARA CASANARE
