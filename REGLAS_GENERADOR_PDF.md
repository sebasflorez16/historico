# 🔒 REGLAS DE GENERACIÓN DE INFORMES PDF - AgroTech Histórico

## ⚠️ ÚNICA REGLA QUE DEBES RECORDAR

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ✅ USAR SIEMPRE:                                          │
│     informes/generador_pdf.py                              │
│     Clase: GeneradorPDFProfesional                         │
│                                                             │
│  ❌ NUNCA USAR:                                            │
│     informes/services/generador_pdf_OBSOLETO_NO_USAR.py   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Código de Ejemplo (Copiar y Pegar)

```python
# ✅ CORRECTO - Única forma válida de generar informes
from informes.generador_pdf import generador_pdf_profesional

resultado = generador_pdf_profesional.generar_informe_completo(
    parcela=parcela,
    usuario=usuario,
    periodo_meses=12,
    tipo_analisis='rapido'  # o 'completo'
)

if resultado['success']:
    pdf_url = resultado['archivo_pdf']
    print(f"✅ PDF generado: {pdf_url}")
else:
    print(f"❌ Error: {resultado['error']}")
```

```python
# ❌ INCORRECTO - NO HACER ESTO
from informes.services.generador_pdf import GeneradorInformePDF  # ❌ OBSOLETO
from informes.services.generador_pdf import generador_pdf  # ❌ OBSOLETO
```

---

## 🎯 Para Agregar Nuevas Funcionalidades

### ✅ HACER (Regla de Oro):

1. **SOLO AGREGAR** nuevas secciones, nunca modificar las existentes
2. Editar **únicamente** `informes/generador_pdf.py`
3. Crear método privado `_crear_mi_nueva_seccion()`
4. Agregarlo en `generar_informe_completo()` en el lugar apropiado
5. Probar con `test_generador_profesional_completo.py`

### ❌ NUNCA HACER:

1. ❌ Modificar secciones existentes que ya funcionan
2. ❌ Crear archivos nuevos de generador de PDF
3. ❌ Tocar el archivo `generador_pdf_OBSOLETO_NO_USAR.py`
4. ❌ Llamar directamente a EOSDA API desde el generador

---

## 📚 Documentación Detallada

- **Flujo completo:** `docs/FLUJO_GENERACION_INFORMES_PDF.md`
- **README del módulo:** `informes/README_GENERADOR_PDF.md`

---

**Fecha:** 21 de enero de 2026  
**Motivo:** Evitar confusión entre generadores obsoletos y actual
