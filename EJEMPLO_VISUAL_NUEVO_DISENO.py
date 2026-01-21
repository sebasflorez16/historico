"""
EJEMPLO VISUAL: Banner Ejecutivo Profesional
=============================================

Este archivo muestra cómo luce el nuevo banner ejecutivo en el PDF.
"""

# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║      ⚠  ESTADO DEL CULTIVO: REQUIERE ATENCIÓN              ║
# ║      Detectadas áreas que necesitan intervención            ║
# ║                                                              ║
# ║                         72%                                  ║
# ║                                                              ║
# ║               Eficiencia productiva actual                   ║
# ║           12.5 hectáreas con recomendaciones                 ║
# ║                                                              ║
# ║  Consulte la sección "Diagnóstico Detallado" al final       ║
# ║       del documento para el plan de acción completo          ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝
#   
#   Características:
#   - Color de fondo: #F39C12 (Amber profesional)
#   - Borde: #D68910 (2.5px, redondeado 12px)
#   - Padding: 18-20px
#   - Texto blanco (legibilidad óptima)
#   - Icono: ⚠ (suave, no agresivo)

# ═══════════════════════════════════════════════════════════════
# COMPARACIÓN VISUAL: ANTES vs DESPUÉS
# ═══════════════════════════════════════════════════════════════

ANTES = """
╔══════════════════════════════════════════════════╗
║  !! CRÍTICO !!                                   ║
║                                                  ║
║  72%                                             ║
║                                                  ║
║  [Texto técnico sin contexto]                   ║
╚══════════════════════════════════════════════════╝

Problemas:
- Rojo brillante agresivo (#E74C3C)
- Icono "!!" no profesional
- Sin contexto claro
- Posible overlap de texto
"""

DESPUES = """
╔══════════════════════════════════════════════════╗
║                                                  ║
║  ⚠  ESTADO DEL CULTIVO: REQUIERE ATENCIÓN       ║
║  Detectadas áreas que necesitan intervención     ║
║                                                  ║
║                     72%                          ║
║                                                  ║
║          Eficiencia productiva actual            ║
║      12.5 hectáreas con recomendaciones          ║
║                                                  ║
║  Consulte la sección "Diagnóstico Detallado"    ║
║  al final del documento para el plan completo    ║
║                                                  ║
╚══════════════════════════════════════════════════╝

Mejoras:
- Amber suave (#F39C12) - no rojo brillante
- Icono ⚠ profesional
- Contexto claro ("ESTADO DEL CULTIVO")
- ParagraphStyles evitan overlap
- Borde redondeado (12px)
- Info adicional descriptiva
"""

# ═══════════════════════════════════════════════════════════════
# TABLA DE SEVERIDAD: ANTES vs DESPUÉS
# ═══════════════════════════════════════════════════════════════

TABLA_ANTES = """
┌────────────────────┬──────────┬───────────┬────────────┐
│ Nivel de Severidad │ Área (ha)│ % del Total│ Prioridad │
├────────────────────┼──────────┼───────────┼────────────┤
│ 🔴 Crítica         │   12.50  │   75.2%   │  INMEDIATA │
│ 🟠 Moderada        │    3.20  │   19.3%   │    Alta    │
│ 🟡 Leve            │    1.10  │    5.5%   │ Monitoreo  │
├────────────────────┼──────────┼───────────┼────────────┤
│ TOTAL AFECTADO     │   16.80  │   100%    │     -      │
└────────────────────┴──────────┴───────────┴────────────┘

Problemas:
- Emojis poco profesionales
- Colores brillantes (#FFCCCC, #FFE5CC)
- Terminología técnica ("Severidad")
- Bordes duros (no redondeados)
"""

TABLA_DESPUES = """
╭────────────────────┬──────────┬───────────┬────────────╮
│ Nivel de Prioridad │ Hectáreas│  % Área   │   Acción   │
├────────────────────┼──────────┼───────────┼────────────┤
│ ● Prioridad Alta   │  12.50 ha│   75.2%   │  Inmediata │
│ ● Prioridad Media  │   3.20 ha│   19.3%   │  Programar │
│ ● Monitoreo        │   1.10 ha│    5.5%   │  Observar  │
├────────────────────┼──────────┼───────────┼────────────┤
│ TOTAL              │  16.80 ha│   100%    │     -      │
╰────────────────────┴──────────┴───────────┴────────────╯

Mejoras:
- Iconos ● (mejor compatibilidad PDF)
- Colores MUY suaves (#FADBD8, #FEF5E7, #FEF9E7)
- Terminología comercial ("Prioridad", no "Severidad")
- Acciones claras ("Inmediata", "Programar", "Observar")
- Bordes redondeados (6px)
- Padding generoso (10-12px)
"""

# ═══════════════════════════════════════════════════════════════
# NARRATIVA DE CAMPO: Ejemplos
# ═══════════════════════════════════════════════════════════════

NARRATIVA_TECNICA = """
Zona 1: Déficit Hídrico Recurrente
NDVI: 0.34 | NDMI: -0.12 | SAVI: 0.28
Severidad: 78% | Confianza: 92%
"""

NARRATIVA_CAMPO = """
╭─────────────────────────────────────────────────────────╮
│ Zona 1: Déficit Hídrico Recurrente                     │
│                                                         │
│ Esta zona de 12.5 hectáreas muestra signos claros de   │
│ falta de agua. Las plantas presentan bajo vigor        │
│ (NDVI: 0.34) y muy baja humedad (NDMI: -0.12).         │
│ Es probable que el riego no esté llegando de manera    │
│ uniforme o que haya problemas con el sistema.          │
│                                                         │
│ Ubicación: -34.567890, -58.123456 | Área: 12.50 ha     │
╰─────────────────────────────────────────────────────────╯

Mejoras:
- Lenguaje descriptivo ("signos claros de falta de agua")
- Explicación práctica ("riego no está llegando")
- Valores técnicos como referencia (no foco principal)
- Cuadro con borde redondeado
- Background suave (#FDFEFE)
"""

# ═══════════════════════════════════════════════════════════════
# CÓDIGO DE IMPLEMENTACIÓN
# ═══════════════════════════════════════════════════════════════

CODIGO_BANNER = '''
# Banner profesional en generador_pdf.py

# Determinar color y estado
if eficiencia >= 80:
    color_fondo = '#27AE60'  # Verde profesional
    color_borde = '#1E8449'
    estado = 'EXCELENTE'
    mensaje = 'El cultivo presenta condiciones óptimas'
    icono = '✓'
elif eficiencia >= 60:
    color_fondo = '#F39C12'  # Amber profesional
    color_borde = '#D68910'
    estado = 'REQUIERE ATENCIÓN'
    mensaje = 'Detectadas áreas que necesitan intervención'
    icono = '⚠'
else:
    color_fondo = '#E67E22'  # Soft red
    color_borde = '#CA6F1E'
    estado = 'CRÍTICO - ACCIÓN INMEDIATA'
    mensaje = 'Múltiples zonas requieren intervención urgente'
    icono = '●'

# Estilo sin overlap
estilo_banner = ParagraphStyle(
    'BannerProfesional',
    fontSize=11,
    leading=15,  # ← 1.36x fontSize - evita overlap
    textColor=colors.white,
    alignment=TA_CENTER
)

# Tabla con bordes redondeados
tabla_resumen.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(color_fondo)),
    ('BOX', (0, 0), (-1, -1), 2.5, colors.HexColor(color_borde)),
    ('ROUNDEDCORNERS', [12, 12, 12, 12]),  # ← Bordes redondeados
    ('TOPPADDING', (0, 0), (-1, -1), 18),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
]))
'''

CODIGO_TABLA = '''
# Tabla profesional en diagnostico_pdf_helper.py

# Colores suaves (NO brillantes)
('BACKGROUND', (0, row), (-1, row), colors.HexColor('#FADBD8')),  # Rosa MUY suave
('TEXTCOLOR', (0, row), (0, row), colors.HexColor('#C0392B')),    # Texto rojo suave
('ROUNDEDCORNERS', [6, 6, 6, 6]),  # Bordes redondeados
('TOPPADDING', (0, 0), (-1, -1), 10),  # Padding generoso
('BOTTOMPADDING', (0, 0), (-1, -1), 10),

# Terminología comercial
data = [
    ['Nivel de Prioridad', 'Hectáreas', '% Área', 'Acción'],
    ['● Prioridad Alta', f"{critica:.2f} ha", f"{pct}%", 'Inmediata'],
    # ...
]
'''

# ═══════════════════════════════════════════════════════════════
# TESTING VISUAL
# ═══════════════════════════════════════════════════════════════

CHECKLIST_VISUAL = """
VALIDACIÓN VISUAL DEL PDF GENERADO
===================================

[ ] Banner Ejecutivo:
    [ ] Color suave (amber #F39C12 o soft red #E67E22)
    [ ] Bordes redondeados visibles
    [ ] Icono apropiado (✓, ⚠, ●)
    [ ] Texto NO superpuesto
    [ ] Número grande (72%) centrado y claro
    [ ] Info adicional presente y legible

[ ] Tabla de Severidad:
    [ ] Colores MUY suaves (rosa #FADBD8, amber #FEF5E7)
    [ ] Bordes redondeados visibles
    [ ] Terminología: "Nivel de Prioridad"
    [ ] Acciones: "Inmediata", "Programar", "Observar"
    [ ] Iconos ● (no emojis)

[ ] Diagnóstico Detallado:
    [ ] Mapa y tabla EN LA MISMA PÁGINA
    [ ] Narrativa descriptiva (lenguaje de campo)
    [ ] Cuadros de zonas con bordes redondeados
    [ ] Recomendaciones en cuadro amber suave

[ ] Layout General:
    [ ] Documento compacto (<16 páginas)
    [ ] Sin saltos de página innecesarios
    [ ] Espaciado consistente
    [ ] Sin texto superpuesto en ninguna sección
"""

print("Ejemplo visual del nuevo diseño de PDFs de AgroTech")
print("=" * 60)
print("\n1. BANNER EJECUTIVO - DESPUÉS:")
print(DESPUES)
print("\n2. TABLA DE SEVERIDAD - DESPUÉS:")
print(TABLA_DESPUES)
print("\n3. NARRATIVA DE CAMPO:")
print(NARRATIVA_CAMPO)
print("\n4. CHECKLIST DE VALIDACIÓN:")
print(CHECKLIST_VISUAL)
