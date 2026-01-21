# 🎨 Guía Rápida: Sistema de PDFs Profesionales v2.0

## Para Desarrolladores

### 🚀 Generar PDF con Nuevo Diseño

```python
from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional

# 1. Obtener parcela
parcela = Parcela.objects.get(id=3)

# 2. Generar PDF
generador = GeneradorPDFProfesional()
pdf_path = generador.generar(
    parcela_id=parcela.id,
    tipo_informe='rapido',  # o 'completo'
    fecha_inicio=None,      # Auto: 6 meses atrás
    fecha_fin=None          # Auto: hoy
)

print(f"✅ PDF generado: {pdf_path}")
```

---

## 📋 Validar Calidad UX del PDF

```bash
# Ejecutar validador automático
python validar_ux_pdf_profesional.py media/informes/informe_parcela_3.pdf

# Ejemplo de salida:
# 🔤 Validando terminología...
# 🎨 Validando elementos visuales...
# 📋 Validando estructura...
# 📏 Validando compactación...
# 📝 Validando narrativa...
#
# 📊 RESULTADOS DE VALIDACIÓN
# ✅ Checks exitosos: 12
#    ✓ Sin signos de exclamación dobles agresivos
#    ✓ Terminología profesional: 'REQUIERE ATENCIÓN'
#    ✓ Documento compacto: 14 páginas ✓
#    ...
#
# 🎉 ¡PERFECTO! El PDF cumple con todos los estándares UX
```

---

## 🎨 Personalizar Colores del Banner

```python
# En generador_pdf.py, método _crear_resumen_ejecutivo()

# Modificar umbrales de eficiencia
if eficiencia >= 85:  # Antes: 80
    color_fondo = '#27AE60'  # Verde
    estado = 'EXCELENTE'
elif eficiencia >= 65:  # Antes: 60
    color_fondo = '#F39C12'  # Amber
    estado = 'REQUIERE ATENCIÓN'
else:
    color_fondo = '#E67E22'  # Soft red
    estado = 'CRÍTICO - ACCIÓN INMEDIATA'
```

---

## 📊 Agregar Nueva Sección sin Fragmentar

```python
# EVITAR:
story.extend(mi_seccion())
story.append(PageBreak())  # ❌ Fragmenta el documento

# PREFERIR:
story.extend(mi_seccion())
story.append(Spacer(1, 1*cm))  # ✅ Permite flujo natural

# Solo usar PageBreak en puntos estratégicos:
# - Fin de portada
# - Inicio de anexos técnicos
# - Inicio de diagnóstico final
```

---

## 🔧 Crear Tabla Profesional

```python
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# Datos
data = [
    ['Columna 1', 'Columna 2'],
    ['Valor 1', 'Valor 2'],
]

# Crear tabla
tabla = Table(data, colWidths=[8*cm, 7*cm])

# Estilo profesional
tabla.setStyle(TableStyle([
    # Encabezado
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    
    # Contenido
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    
    # Bordes y padding
    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#BDC3C7')),
    ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 12),
]))

story.append(tabla)
```

---

## 📝 Crear Párrafo sin Overlap

```python
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import Paragraph

# Crear estilo con leading apropiado
estilo = ParagraphStyle(
    'MiEstilo',
    parent=estilos['Normal'],
    fontSize=10,
    leading=14,  # 1.4x fontSize - EVITA OVERLAP
    alignment=TA_JUSTIFY,
    spaceAfter=6,
    spaceBefore=4,
    textColor=colors.HexColor('#2C3E50')
)

# Usar
parrafo = Paragraph(
    "Texto que no se superpondrá porque tiene leading apropiado.",
    estilo
)
story.append(parrafo)
```

---

## 🗂️ Mantener Elementos Juntos

```python
from reportlab.platypus import KeepTogether

# Elementos que deben estar en la misma página
mapa = Image('mapa.png', width=17*cm, height=13*cm)
tabla = generar_tabla_desglose()
descripcion = Paragraph("Descripción...", estilo)

# Usar KeepTogether
elementos_juntos = [mapa, tabla, descripcion]

try:
    story.append(KeepTogether(elementos_juntos))
except:
    # Fallback si KeepTogether falla
    story.extend(elementos_juntos)
```

---

## 🎨 Paleta de Colores Estándar

```python
# Importar
from reportlab.lib import colors

# Definir constantes
VERDE_EXCELENTE = colors.HexColor('#27AE60')
AMBER_ATENCION = colors.HexColor('#F39C12')
SOFT_RED_CRITICO = colors.HexColor('#E67E22')
GRIS_OSCURO = colors.HexColor('#34495E')
GRIS_MEDIO = colors.HexColor('#7F8C8D')
GRIS_CLARO = colors.HexColor('#BDC3C7')
BACKGROUND_SUAVE = colors.HexColor('#F8F9FA')

# Usar en tablas/párrafos
tabla.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), GRIS_OSCURO),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    # ...
]))
```

---

## 🔍 Debugging de Layout

```python
# Activar modo debug en generador
import logging
logging.basicConfig(level=logging.DEBUG)

# Ver logs durante generación
# Buscar:
# - "PageBreak agregado en..." 
# - "Spacer agregado: X cm"
# - "Sección Y ocupa Z elementos"

# Verificar manualmente el PDF generado
# - Abrir en Adobe Reader (mejor que Preview)
# - Verificar saltos de página innecesarios
# - Revisar overlap de texto
# - Validar colores y bordes
```

---

## 📦 Archivos Clave Modificados

```
informes/
├── generador_pdf.py                    # Motor principal de generación
│   ├── _crear_resumen_ejecutivo()      # Banner profesional
│   ├── _crear_seccion_guia_intervencion()  # Diagnóstico final
│   └── generar()                       # Optimización PageBreaks
│
└── helpers/
    └── diagnostico_pdf_helper.py       # Helpers de diagnóstico
        └── generar_tabla_desglose_severidad()  # Tabla moderna
```

---

## 🧪 Testing Manual

```bash
# 1. Generar PDF de prueba
python manage.py shell
>>> from informes.generador_pdf import GeneradorPDFProfesional
>>> gen = GeneradorPDFProfesional()
>>> pdf = gen.generar(parcela_id=3, tipo_informe='rapido')

# 2. Validar automáticamente
python validar_ux_pdf_profesional.py media/informes/informe_parcela_3.pdf

# 3. Verificar visualmente
open media/informes/informe_parcela_3.pdf

# Checklist visual:
# □ Banner ejecutivo con colores suaves
# □ Sin overlap de texto
# □ Mapa y tabla en misma página
# □ Terminología profesional ("REQUIERE ATENCIÓN")
# □ Documento compacto (<16 páginas)
# □ Narrativa en lenguaje de campo
# □ Bordes redondeados en cuadros
```

---

## ⚠️ Errores Comunes

### 1. AttributeError: 'GeneradorPDFProfesional' object has no attribute 'ancho_pagina'

```python
# ❌ INCORRECTO
ancho_tabla = self.ancho_pagina - 2*self.margen

# ✅ CORRECTO
ancho_tabla = self.ancho - 2*self.margen
```

### 2. Overlap de texto en Paragraphs

```python
# ❌ INCORRECTO (leading no especificado)
estilo = ParagraphStyle('Malo', fontSize=10)

# ✅ CORRECTO (leading 1.4x fontSize)
estilo = ParagraphStyle('Bueno', fontSize=10, leading=14)
```

### 3. KeepTogether falla con elementos grandes

```python
# ❌ PUEDE FALLAR si elementos son muy grandes
story.append(KeepTogether([imagen_gigante, tabla_enorme]))

# ✅ MEJOR (con fallback)
try:
    story.append(KeepTogether(elementos))
except:
    story.extend(elementos)
```

---

## 📞 Soporte

**Documentación:**
- [REFACTORIZACION_UX_PDF_PROFESIONAL.md](REFACTORIZACION_UX_PDF_PROFESIONAL.md)
- [ReportLab Docs](https://www.reportlab.com/docs/reportlab-userguide.pdf)

**Herramientas:**
- `validar_ux_pdf_profesional.py` - Validador automático
- `verificar_pdf_generado.py` - Verificador básico (legacy)

---

**Última actualización:** $(date)  
**Versión:** 2.0.0 - Refactorización UX Profesional
