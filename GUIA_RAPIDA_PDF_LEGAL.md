# ⚡ Guía Rápida - Sistema PDF Legal AgroTech

## 🚀 Comandos Principales

### 1️⃣ Generar PDF para Parcela #2 (ID=6)
```bash
cd "/Users/sebasflorez16/Documents/AgroTech Historico"
python generar_pdf_verificacion_casanare.py
```
**Resultado:** `./media/verificacion_legal/verificacion_legal_casanare_parcela_6_MEJORADO.pdf`

### 2️⃣ Abrir PDF generado
```bash
open "./media/verificacion_legal/verificacion_legal_casanare_parcela_6_MEJORADO.pdf"
```

### 3️⃣ Ver datos de una parcela
```bash
python manage.py shell << 'EOF'
from informes.models import Parcela
p = Parcela.objects.get(id=6)
print(f"{p.id}: {p.nombre} - {p.propietario} - {p.area_hectareas} ha")
EOF
```

### 4️⃣ Listar todas las parcelas
```bash
python manage.py shell << 'EOF'
from informes.models import Parcela
for p in Parcela.objects.all():
    print(f"ID {p.id}: {p.nombre} ({p.area_hectareas:.2f} ha)")
EOF
```

---

## 📝 Editar para Otra Parcela

### Cambiar a Bio Energy (ID=11)
Edita `generar_pdf_verificacion_casanare.py` línea 27:
```python
# Cambiar de:
parcela_real = Parcela.objects.get(id=6)

# A:
parcela_real = Parcela.objects.get(id=11)
```

Luego ejecuta:
```bash
python generar_pdf_verificacion_casanare.py
```

---

## 🗺️ Datos Geográficos

### Ver red hídrica cargada
```bash
python diagnosticar_red_hidrica_completo.py
```

### Descargar/actualizar red hídrica
```bash
python descargar_red_hidrica_igac.py
```

### Verificar shapefiles
```bash
ls -lh datos_geograficos/*/
```

---

## 🔍 Verificación de Datos

### Comparar DB vs PDF
```bash
# 1. Ver datos en DB
python manage.py shell << 'EOF'
from informes.models import Parcela
p = Parcela.objects.get(id=6)
print(f"Nombre: {p.nombre}")
print(f"Propietario: {p.propietario}")
print(f"Área: {p.area_hectareas} ha")
centroide = p.geometria.centroid
print(f"Centroide: {centroide.y}°N, {centroide.x}°W")
EOF

# 2. Abrir PDF
open "./media/verificacion_legal/verificacion_legal_casanare_parcela_6_MEJORADO.pdf"

# 3. Comparar visualmente
```

---

## 📊 Estructura de Archivos

### Scripts Principales
```
generar_pdf_verificacion_casanare.py   → Genera PDF para parcela
generador_pdf_legal.py                 → Lógica de generación PDF
verificador_legal.py                   → Verificación de restricciones
descargar_red_hidrica_igac.py          → Descarga shapefiles
```

### Datos Geográficos
```
datos_geograficos/
├── red_hidrica/drenajes.shp           → 2000 cauces Casanare
├── runap/runap.shp                    → 1837 áreas protegidas
├── resguardos_indigenas/              → 954 resguardos
└── paramos/                           → Páramos (vacío en llanura)
```

### PDFs Generados
```
media/verificacion_legal/
└── verificacion_legal_casanare_parcela_6_MEJORADO.pdf
```

### Documentación
```
RESUMEN_EJECUTIVO_CORRECCION_PDF.md    → Resumen general
VALIDACION_FINAL_PDF_REAL.md           → Validación de datos
ANTES_DESPUES_CORRECCION_PDF.md        → Comparación antes/después
README_RED_HIDRICA.md                  → Guía de red hídrica
```

---

## ✅ Checklist de Validación

Después de generar un PDF, verifica:

- [ ] **Portada:** Nombre y propietario correctos
- [ ] **Área:** Coincide con la base de datos
- [ ] **Mapa:** La parcela aparece en coordenadas correctas
- [ ] **Análisis:** Distancias a ríos son razonables
- [ ] **Tabla:** Niveles de confianza indican fuentes
- [ ] **Sin errores:** No hay warnings ni datos faltantes

---

## 🆘 Solución de Problemas

### Error: Parcela no encontrada
```bash
# Verificar que existe en la DB
python manage.py shell -c "from informes.models import Parcela; print(Parcela.objects.filter(id=6).exists())"
```

### Error: Shapefile no encontrado
```bash
# Descargar de nuevo
python descargar_red_hidrica_igac.py
```

### Error: PDF no abre
```bash
# Verificar tamaño del archivo
ls -lh ./media/verificacion_legal/*.pdf

# Regenerar
python generar_pdf_verificacion_casanare.py
```

### Warning GDAL PROJ
```bash
# Ignorar (no afecta resultados)
# Es un warning de versión de librerías geoespaciales
```

---

## 📚 Recursos Adicionales

### Documentación
- `README.md` - Guía general del proyecto
- `README_RED_HIDRICA.md` - Sistema de red hídrica
- `PROGRESO_FINAL_RED_HIDRICA_PDF.md` - Progreso completo

### Logs
```bash
# Ver logs recientes
tail -100 agrotech.log

# Buscar errores
grep -i "error" agrotech.log
```

### Base de Datos
```bash
# Conectar a PostgreSQL
psql -d agrotech_db -U sebasflorez16

# Ver parcelas
SELECT id, nombre, area_hectareas FROM informes_parcela;
```

---

## 🎯 Flujo Típico de Trabajo

1. **Verificar parcela en DB**
   ```bash
   python manage.py shell -c "from informes.models import Parcela; print(Parcela.objects.get(id=6))"
   ```

2. **Generar PDF**
   ```bash
   python generar_pdf_verificacion_casanare.py
   ```

3. **Revisar PDF**
   ```bash
   open "./media/verificacion_legal/verificacion_legal_casanare_parcela_6_MEJORADO.pdf"
   ```

4. **Validar datos**
   - Comparar PDF con datos de la DB
   - Verificar mapa muestra ubicación correcta
   - Confirmar distancias a ríos son razonables

5. **Listo para usar** ✅

---

## 💡 Tips

- ✅ **Siempre usa la parcela real de la DB** (nunca geometría inventada)
- ✅ **Verifica que los shapefiles existan** antes de generar PDF
- ✅ **Compara visualmente** PDF vs datos de la DB
- ✅ **Guarda los PDFs generados** con nombres descriptivos
- ✅ **Documenta cualquier cambio** en los scripts

---

**Versión:** 1.0
**Última actualización:** Enero 2025
**Estado:** ✅ Sistema validado y funcional
