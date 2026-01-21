# 📁 Directorio `informes/` - AgroTech Histórico

## ⚠️ IMPORTANTE: Archivo de Generación de PDF

### ✅ ARCHIVO OFICIAL (ÚNICO QUE DEBES USAR)

```
informes/generador_pdf.py
```

**Clase:** `GeneradorPDFProfesional`  
**Tamaño:** 1725 líneas  
**Estado:** ✅ ACTIVO - Este es el generador profesional completo

**Uso:**
```python
from informes.generador_pdf import generador_pdf_profesional

resultado = generador_pdf_profesional.generar_informe_completo(
    parcela=parcela,
    usuario=usuario,
    periodo_meses=12,
    tipo_analisis='rapido'
)
```

---

### ❌ ARCHIVOS OBSOLETOS (NO USAR)

```
informes/services/generador_pdf_OBSOLETO_NO_USAR.py
```

**Estado:** ❌ OBSOLETO - Marcado para eliminación  
**Razón:** Generador antiguo que causaba confusión  
**Acción:** NO IMPORTAR - Será eliminado en futuras versiones

---

## 📖 Documentación Completa

Ver: `docs/FLUJO_GENERACION_INFORMES_PDF.md`

---

## 🚀 Quick Start

### Generar informe profesional:

```bash
# Desde línea de comandos
python test_generador_profesional_completo.py

# Desde vista Django
from informes.generador_pdf import generador_pdf_profesional
resultado = generador_pdf_profesional.generar_informe_completo(...)
```

### Validar salida:

```bash
# El PDF debe estar en:
media/informes/informe_Parcela_X_YYYYMMDD_HHMMSS.pdf

# Tamaño esperado: 650KB - 1MB
```

---

**¿Dudas?** Consulta `docs/FLUJO_GENERACION_INFORMES_PDF.md`
