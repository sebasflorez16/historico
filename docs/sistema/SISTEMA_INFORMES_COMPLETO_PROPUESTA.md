# 📊 SISTEMA INTELIGENTE DE INFORMES AGROTECH - PROPUESTA COMPLETA

## 🎯 VISIÓN GENERAL

Sistema de generación de informes profesionales con análisis satelital impulsado por IA, optimizado para eficiencia y múltiples canales de distribución.

---

## 📋 TABLA DE CONTENIDOS

1. [Arquitectura del Sistema](#arquitectura)
2. [Flujo de Generación](#flujo)
3. [Selección Inteligente de Índices](#indices)
4. [Análisis con IA](#ia)
5. [Generación de PDF](#pdf)
6. [Canales de Distribución](#distribucion)
7. [Interfaz de Usuario](#interfaz)
8. [Funciones Adicionales](#funciones)
9. [Plan de Implementación](#implementacion)

---

## 🏗️ ARQUITECTURA DEL SISTEMA {#arquitectura}

```
┌─────────────────────────────────────────────────────────────┐
│                   INTERFAZ DE USUARIO                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│  │Configurar │  │ Previsual │  │ Generar   │              │
│  │ Informe   │  │   izar    │  │ Informe   │              │
│  └───────────┘  └───────────┘  └───────────┘              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              MOTOR DE GENERACIÓN DE INFORMES                │
│                                                             │
│  1. Validación de Datos Disponibles                        │
│  2. Selección Inteligente de Índices                       │
│  3. Descarga Optimizada (solo lo necesario)                │
│  4. Análisis con IA                                        │
│  5. Generación de Gráficos                                 │
│  6. Compilación de PDF                                     │
│  7. Distribución Multi-canal                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    ALMACENAMIENTO                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Base de  │  │ Archivos │  │  Cache   │                 │
│  │  Datos   │  │   PDF    │  │   IA     │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUJO DE GENERACIÓN DE INFORMES {#flujo}

### Paso 1: Configuración del Informe

```python
# Usuario selecciona:
{
    'parcela_id': 123,
    'periodo': '6 meses',  # 6, 12, 24 meses
    'indices_requeridos': ['ndvi', 'ndmi'],  # Selección múltiple
    'incluir_analisis_ia': True,
    'incluir_imagenes': True,
    'idioma': 'es',  # español, inglés
    'nivel_tecnico': 'mixto'  # técnico, común, mixto
}
```

### Paso 2: Validación Pre-Generación

```python
def validar_datos_disponibles(parcela_id, periodo, indices):
    """
    Verifica qué datos ya están en la base de datos
    y qué falta descargar
    """
    resultado = {
        'datos_completos': False,
        'meses_disponibles': [],
        'meses_faltantes': [],
        'indices_disponibles': {
            'ndvi': ['2024-01', '2024-02', ...],
            'ndmi': ['2024-01', ...],
            'savi': []  # Vacío, hay que descargar
        },
        'imagenes_disponibles': {
            'ndvi': 5,  # 5 imágenes guardadas
            'ndmi': 0,  # Sin imágenes
        },
        'accion_requerida': 'descargar_parcial'  # o 'todo_listo'
    }
    return resultado
```

### Paso 3: Descarga Optimizada

```python
class OptimizadorDescargas:
    """
    Descarga SOLO lo que falta, no todo de nuevo
    """
    
    def descargar_indices_faltantes(self, parcela, indices, periodo):
        """
        Estrategia de descarga inteligente:
        1. Verificar caché local
        2. Consultar base de datos
        3. Descargar solo meses/índices faltantes
        4. Reutilizar datos existentes
        """
        descargas_pendientes = []
        
        for indice in indices:
            meses_faltantes = self.obtener_meses_sin_datos(
                parcela, indice, periodo
            )
            
            if meses_faltantes:
                descargas_pendientes.append({
                    'indice': indice,
                    'meses': meses_faltantes
                })
        
        # Descargar en lote, una request por índice
        for descarga in descargas_pendientes:
            self.descargar_indice_batch(
                parcela, 
                descarga['indice'], 
                descarga['meses']
            )
    
    def descargar_imagenes_necesarias(self, parcela, indices, max_imagenes=3):
        """
        Descarga solo imágenes clave:
        - Mes más reciente
        - Mejor calidad (menos nubosidad)
        - Máximo 3 imágenes por índice
        """
        for indice in indices:
            # Obtener mejores fechas disponibles
            fechas_optimas = self.seleccionar_mejores_fechas(
                parcela, indice, max_imagenes
            )
            
            for fecha in fechas_optimas:
                if not self.imagen_existe(parcela, indice, fecha):
                    self.descargar_imagen(parcela, indice, fecha)
```

---

## 📈 SELECCIÓN INTELIGENTE DE ÍNDICES {#indices}

### Catálogo de Índices Disponibles

```python
INDICES_DISPONIBLES = {
    'ndvi': {
        'nombre': 'NDVI - Índice de Vegetación',
        'descripcion': 'Mide vigor y salud vegetal',
        'rango': '0 a 1',
        'uso': 'Monitoreo general, detección estrés',
        'prioridad': 1,  # Siempre incluir
        'costo_descarga': 'bajo'
    },
    'ndmi': {
        'nombre': 'NDMI - Índice de Humedad',
        'descripcion': 'Detecta contenido de agua en plantas',
        'rango': '-1 a 1',
        'uso': 'Riego, sequía, estrés hídrico',
        'prioridad': 2,
        'costo_descarga': 'bajo'
    },
    'savi': {
        'nombre': 'SAVI - Vegetación Ajustada al Suelo',
        'descripcion': 'NDVI corregido para suelos expuestos',
        'rango': '0 a 1',
        'uso': 'Cultivos jóvenes, baja cobertura',
        'prioridad': 3,
        'costo_descarga': 'bajo'
    },
    'evi': {
        'nombre': 'EVI - Índice de Vegetación Mejorado',
        'descripcion': 'Menos sensible a atmósfera',
        'rango': '0 a 1',
        'uso': 'Zonas tropicales, alta biomasa',
        'prioridad': 4,
        'costo_descarga': 'medio',
        'disponible_eosda': True
    },
    'lai': {
        'nombre': 'LAI - Índice de Área Foliar',
        'descripcion': 'Área de hojas por unidad de suelo',
        'rango': '0 a 8+',
        'uso': 'Desarrollo del cultivo, biomasa',
        'prioridad': 5,
        'costo_descarga': 'alto'
    },
    'msavi': {
        'nombre': 'MSAVI - SAVI Modificado',
        'descripcion': 'SAVI con autocorrección',
        'rango': '0 a 1',
        'uso': 'Suelos variables',
        'prioridad': 6,
        'costo_descarga': 'medio'
    }
}
```

### UI de Selección de Índices

```html
<!-- Interfaz con checkboxes inteligentes -->
<div class="indice-selector">
    <h5>📊 Selecciona Índices para el Informe</h5>
    
    <!-- Índices esenciales (siempre recomendados) -->
    <div class="indices-esenciales mb-4">
        <h6 class="text-success">✅ Índices Esenciales (Recomendados)</h6>
        <div class="row">
            <div class="col-md-6">
                <div class="indice-card recomendado">
                    <input type="checkbox" name="indices" value="ndvi" checked>
                    <div class="indice-info">
                        <strong>NDVI</strong> - Salud Vegetal
                        <small>Datos: 12/12 meses ✅</small>
                        <small>Imágenes: 3 disponibles 📷</small>
                    </div>
                    <span class="badge bg-success">Listo</span>
                </div>
            </div>
            <div class="col-md-6">
                <div class="indice-card warning">
                    <input type="checkbox" name="indices" value="ndmi" checked>
                    <div class="indice-info">
                        <strong>NDMI</strong> - Humedad
                        <small>Datos: 8/12 meses ⚠️</small>
                        <small>Imágenes: 0 disponibles</small>
                    </div>
                    <span class="badge bg-warning">Descargar 4 meses</span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Índices adicionales (opcionales) -->
    <div class="indices-adicionales">
        <h6 class="text-info">💡 Índices Adicionales (Opcional)</h6>
        <div class="row">
            <div class="col-md-4">
                <div class="indice-card">
                    <input type="checkbox" name="indices" value="savi">
                    <div class="indice-info">
                        <strong>SAVI</strong>
                        <small>Datos: 0/12 meses</small>
                    </div>
                    <span class="badge bg-secondary">Requiere descarga completa</span>
                </div>
            </div>
            <div class="col-md-4">
                <div class="indice-card">
                    <input type="checkbox" name="indices" value="evi">
                    <div class="indice-info">
                        <strong>EVI</strong>
                        <small>No disponible</small>
                    </div>
                    <span class="badge bg-danger">No soportado</span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Resumen de descarga -->
    <div class="descarga-resumen mt-4">
        <div class="alert alert-info">
            <strong>📥 Resumen de Descarga:</strong>
            <ul class="mb-0">
                <li>NDVI: ✅ Todo listo (0 requests)</li>
                <li>NDMI: ⚠️ Descargar 4 meses (1 request)</li>
                <li>SAVI: 📥 Descargar 12 meses (1 request)</li>
            </ul>
            <hr>
            <strong>Total: 2 requests a EOSDA API</strong>
        </div>
    </div>
</div>
```

---

## 🤖 ANÁLISIS CON IA {#ia}

### Integración con OpenAI / Claude / Local LLM

```python
class AnalizadorIA:
    """
    Genera análisis inteligentes según nivel técnico
    """
    
    def __init__(self):
        # Opción 1: OpenAI API (pago)
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Opción 2: Claude API (pago, mejor para español técnico)
        # self.claude_client = anthropic.Anthropic(api_key=...)
        
        # Opción 3: LLM local (gratuito, privado)
        # self.local_llm = Ollama(model='llama3')
    
    def generar_analisis_completo(
        self, 
        datos_indices, 
        nivel_tecnico='mixto',
        idioma='es'
    ):
        """
        Genera análisis en dos niveles:
        1. Técnico: Para agrónomos
        2. Común: Para propietarios sin conocimientos técnicos
        """
        
        # Preparar contexto
        contexto = self._preparar_contexto(datos_indices)
        
        # Generar análisis técnico
        analisis_tecnico = self._generar_tecnico(contexto, idioma)
        
        # Generar análisis para usuario común
        analisis_comun = self._generar_comun(contexto, idioma)
        
        # Generar recomendaciones accionables
        recomendaciones = self._generar_recomendaciones(
            contexto, nivel_tecnico, idioma
        )
        
        return {
            'tecnico': analisis_tecnico,
            'comun': analisis_comun,
            'recomendaciones': recomendaciones,
            'alertas': self._detectar_alertas(datos_indices)
        }
    
    def _preparar_contexto(self, datos_indices):
        """
        Estructura datos para el LLM
        """
        return {
            'parcela': {
                'nombre': datos_indices['parcela']['nombre'],
                'area': datos_indices['parcela']['area_hectareas'],
                'cultivo': datos_indices['parcela']['tipo_cultivo']
            },
            'periodo': {
                'inicio': datos_indices['fecha_inicio'],
                'fin': datos_indices['fecha_fin'],
                'meses': datos_indices['meses_analizados']
            },
            'indices': {
                'ndvi': {
                    'promedio': 0.75,
                    'tendencia': 'ascendente',
                    'variacion': '+12% respecto período anterior',
                    'picos': ['Marzo 2024', 'Julio 2024'],
                    'valles': ['Enero 2024']
                },
                'ndmi': {
                    'promedio': 0.42,
                    'tendencia': 'estable',
                    'alerta': 'Estrés hídrico detectado en Junio'
                }
            },
            'clima': {
                'temp_promedio': 24.5,
                'precipitacion_total': 1250,
                'meses_secos': ['Enero', 'Febrero']
            }
        }
    
    def _generar_tecnico(self, contexto, idioma='es'):
        """
        Análisis técnico para agrónomos
        """
        prompt = f"""
Eres un agrónomo experto especializado en análisis de datos satelitales.
Genera un análisis técnico detallado del cultivo basado en estos datos:

{json.dumps(contexto, indent=2, ensure_ascii=False)}

El análisis debe incluir:
1. Evaluación de índices de vegetación (NDVI, NDMI, SAVI)
2. Interpretación de tendencias temporales
3. Correlación con datos climáticos
4. Identificación de patrones anómalos
5. Terminología técnica apropiada

Idioma: {idioma}
Formato: Texto profesional, párrafos bien estructurados
Longitud: 400-600 palabras
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un agrónomo experto en teledetección."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def _generar_comun(self, contexto, idioma='es'):
        """
        Análisis simplificado para usuarios sin conocimientos técnicos
        """
        prompt = f"""
Eres un asesor agrícola que explica conceptos complejos de forma sencilla.
Genera un análisis claro y comprensible para un propietario sin conocimientos técnicos:

{json.dumps(contexto, indent=2, ensure_ascii=False)}

El análisis debe:
1. Usar lenguaje simple y cotidiano
2. Evitar términos técnicos (o explicarlos)
3. Usar analogías y comparaciones
4. Enfocarse en QUÉ SIGNIFICA para el cultivo
5. Ser optimista pero honesto

Ejemplo de tono: "Su cultivo está saludable, como una planta bien cuidada en casa..."

Idioma: {idioma}
Formato: Texto conversacional, párrafos cortos
Longitud: 200-300 palabras
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asesor que explica agricultura de forma simple."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=600
        )
        
        return response.choices[0].message.content
    
    def _generar_recomendaciones(self, contexto, nivel, idioma='es'):
        """
        Recomendaciones accionables específicas
        """
        prompt = f"""
Basado en estos datos del cultivo:
{json.dumps(contexto, indent=2, ensure_ascii=False)}

Genera 5-7 recomendaciones ACCIONABLES y ESPECÍFICAS.

Nivel técnico: {nivel}
- Si es 'técnico': recomendaciones para agrónomos (fertilización NPK, riego mm, etc.)
- Si es 'común': recomendaciones simples (cuándo regar, cuándo fertilizar, etc.)
- Si es 'mixto': incluir ambos niveles

Formato:
1. [Prioridad: Alta/Media/Baja] Recomendación específica
   Explicación breve
   Beneficio esperado

Idioma: {idioma}
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un agrónomo que da recomendaciones prácticas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    def _detectar_alertas(self, datos_indices):
        """
        Detecta situaciones que requieren atención inmediata
        """
        alertas = []
        
        # Alerta: NDVI muy bajo
        if datos_indices.get('ndvi_promedio', 1) < 0.3:
            alertas.append({
                'tipo': 'critico',
                'icono': '🚨',
                'titulo': 'Salud Vegetal Crítica',
                'mensaje': 'El NDVI promedio (0.25) está por debajo del umbral saludable. Se requiere intervención inmediata.',
                'acciones': [
                    'Inspeccionar físicamente el cultivo',
                    'Revisar sistema de riego',
                    'Verificar plagas/enfermedades'
                ]
            })
        
        # Alerta: Tendencia descendente pronunciada
        if datos_indices.get('ndvi_tendencia') == 'descendente_fuerte':
            alertas.append({
                'tipo': 'advertencia',
                'icono': '⚠️',
                'titulo': 'Tendencia Negativa Detectada',
                'mensaje': 'El NDVI ha disminuido 25% en los últimos 3 meses.',
                'acciones': [
                    'Analizar posibles causas (sequía, plagas, nutrientes)',
                    'Programar visita técnica'
                ]
            })
        
        # Alerta: Estrés hídrico
        if datos_indices.get('ndmi_promedio', 1) < 0.2:
            alertas.append({
                'tipo': 'advertencia',
                'icono': '💧',
                'titulo': 'Posible Estrés Hídrico',
                'mensaje': 'El NDMI indica bajo contenido de humedad en la vegetación.',
                'acciones': [
                    'Aumentar frecuencia de riego',
                    'Verificar sistema de irrigación'
                ]
            })
        
        return alertas
```

---

## 📄 GENERACIÓN DE PDF PROFESIONAL {#pdf}

### Biblioteca: ReportLab + WeasyPrint

```python
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, 
    PageBreak, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

class GeneradorPDF:
    """
    Genera PDFs profesionales con diseño AgroTech
    """
    
    def __init__(self):
        self.pagesize = A4
        self.styles = self._crear_estilos()
        self.colores_agrotech = {
            'verde': colors.HexColor('#2E8B57'),
            'naranja': colors.HexColor('#FF7A00'),
            'gris': colors.HexColor('#2c3e50')
        }
    
    def generar_informe_completo(
        self, 
        datos, 
        analisis_ia, 
        graficos,
        output_path
    ):
        """
        Genera el PDF completo
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.pagesize,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Portada
        story.extend(self._crear_portada(datos))
        story.append(PageBreak())
        
        # Índice
        story.extend(self._crear_indice())
        story.append(PageBreak())
        
        # Resumen ejecutivo
        story.extend(self._crear_resumen_ejecutivo(analisis_ia))
        story.append(PageBreak())
        
        # Datos de la parcela
        story.extend(self._crear_info_parcela(datos))
        story.append(Spacer(1, 0.5*cm))
        
        # Análisis técnico
        story.extend(self._crear_analisis_tecnico(analisis_ia))
        story.append(PageBreak())
        
        # Análisis para usuario común
        story.extend(self._crear_analisis_comun(analisis_ia))
        story.append(PageBreak())
        
        # Gráficos y tendencias
        story.extend(self._crear_seccion_graficos(graficos))
        story.append(PageBreak())
        
        # Imágenes satelitales
        story.extend(self._crear_seccion_imagenes(datos))
        story.append(PageBreak())
        
        # Recomendaciones
        story.extend(self._crear_recomendaciones(analisis_ia))
        story.append(PageBreak())
        
        # Alertas (si existen)
        if analisis_ia.get('alertas'):
            story.extend(self._crear_alertas(analisis_ia['alertas']))
            story.append(PageBreak())
        
        # Datos detallados (tabla)
        story.extend(self._crear_tabla_datos(datos))
        story.append(PageBreak())
        
        # Pie de página con info técnica
        story.extend(self._crear_footer_tecnico(datos))
        
        # Construir PDF
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        
        return output_path
    
    def _crear_portada(self, datos):
        """
        Portada profesional con logo y datos clave
        """
        elements = []
        
        # Logo AgroTech (centrado, grande)
        logo_path = 'static/img/agrotech-logo.svg'
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=8*cm, height=2*cm)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 1*cm))
        
        # Título del informe
        titulo_style = self.styles['titulo_portada']
        titulo = Paragraph(
            f"Informe Satelital Agrícola<br/>{datos['parcela']['nombre']}",
            titulo_style
        )
        elements.append(titulo)
        elements.append(Spacer(1, 2*cm))
        
        # Información clave en tabla
        info_data = [
            ['Parcela:', datos['parcela']['nombre']],
            ['Propietario:', datos['parcela']['propietario']],
            ['Cultivo:', datos['parcela']['tipo_cultivo']],
            ['Área:', f"{datos['parcela']['area_hectareas']} ha"],
            ['Período:', f"{datos['fecha_inicio']} a {datos['fecha_fin']}"],
            ['Generado:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        info_table = Table(info_data, colWidths=[5*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), self.colores_agrotech['verde']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 3*cm))
        
        # Pie de portada
        pie = Paragraph(
            "Este informe fue generado automáticamente mediante análisis satelital "
            "con tecnología EOSDA y asistencia de Inteligencia Artificial.",
            self.styles['pie_portada']
        )
        elements.append(pie)
        
        return elements
    
    def _crear_seccion_graficos(self, graficos):
        """
        Crea gráficos con matplotlib y los inserta en el PDF
        """
        elements = []
        
        # Título de sección
        titulo = Paragraph("📊 Análisis Gráfico de Índices", self.styles['titulo_seccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Gráfico 1: Evolución temporal NDVI, NDMI, SAVI
        grafico1_buffer = self._generar_grafico_temporal(graficos['datos_mensuales'])
        grafico1 = Image(grafico1_buffer, width=16*cm, height=10*cm)
        elements.append(grafico1)
        elements.append(Spacer(1, 0.3*cm))
        
        descripcion1 = Paragraph(
            "<b>Figura 1:</b> Evolución temporal de índices de vegetación. "
            "NDVI (verde) indica salud general, NDMI (azul) contenido de humedad, "
            "SAVI (naranja) vegetación ajustada al suelo.",
            self.styles['caption']
        )
        elements.append(descripcion1)
        elements.append(Spacer(1, 1*cm))
        
        # Gráfico 2: Gráfico de barras comparativo
        grafico2_buffer = self._generar_grafico_comparativo(graficos['promedios'])
        grafico2 = Image(grafico2_buffer, width=16*cm, height=8*cm)
        elements.append(grafico2)
        elements.append(Spacer(1, 0.3*cm))
        
        descripcion2 = Paragraph(
            "<b>Figura 2:</b> Comparación de promedios mensuales de índices. "
            "Valores más altos indican mejor salud vegetal.",
            self.styles['caption']
        )
        elements.append(descripcion2)
        
        return elements
    
    def _generar_grafico_temporal(self, datos_mensuales):
        """
        Genera gráfico de líneas con matplotlib
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Configurar estilo AgroTech
        sns.set_style("whitegrid")
        
        meses = [f"{d['año']}-{d['mes']:02d}" for d in datos_mensuales]
        ndvi = [d.get('ndvi_promedio', 0) for d in datos_mensuales]
        ndmi = [d.get('ndmi_promedio', 0) for d in datos_mensuales]
        savi = [d.get('savi_promedio', 0) for d in datos_mensuales]
        
        # Graficar
        ax.plot(meses, ndvi, marker='o', linewidth=2.5, color='#2E8B57', label='NDVI')
        ax.plot(meses, ndmi, marker='s', linewidth=2.5, color='#17a2b8', label='NDMI')
        ax.plot(meses, savi, marker='^', linewidth=2.5, color='#FF7A00', label='SAVI')
        
        # Configurar ejes
        ax.set_xlabel('Período', fontsize=12, fontweight='bold')
        ax.set_ylabel('Valor del Índice', fontsize=12, fontweight='bold')
        ax.set_title('Evolución Temporal de Índices de Vegetación', 
                     fontsize=14, fontweight='bold', color='#2c3e50')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Rotar etiquetas de X
        plt.xticks(rotation=45, ha='right')
        
        # Ajustar layout
        plt.tight_layout()
        
        # Guardar en buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
```

---

## 📱 CANALES DE DISTRIBUCIÓN {#distribucion}

### 1. Descarga Directa (PDF)

```python
@login_required
def descargar_informe(request, informe_id):
    """
    Descarga directa del PDF generado
    """
    informe = get_object_or_404(Informe, id=informe_id)
    
    # Verificar permisos
    if not request.user.is_superuser and informe.parcela.propietario != request.user:
        messages.error(request, 'No tiene permisos para este informe')
        return redirect('dashboard')
    
    if not informe.archivo_pdf:
        messages.error(request, 'El PDF aún no ha sido generado')
        return redirect('ver_informe', informe_id=informe_id)
    
    # Enviar archivo
    response = FileResponse(
        informe.archivo_pdf.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{informe.get_filename()}"'
    
    # Registrar descarga
    informe.registro_descargas.create(
        usuario=request.user,
        fecha=timezone.now(),
        metodo='descarga_directa'
    )
    
    return response
```

### 2. Envío por Email

```python
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

class EnviadorInformes:
    """
    Maneja envío de informes por email
    """
    
    def enviar_por_email(
        self, 
        informe, 
        destinatarios, 
        mensaje_personalizado=None
    ):
        """
        Envía el informe PDF por email
        """
        # Generar email HTML
        contexto = {
            'informe': informe,
            'parcela': informe.parcela,
            'mensaje_personalizado': mensaje_personalizado
        }
        
        html_message = render_to_string(
            'emails/envio_informe.html', 
            contexto
        )
        
        # Crear email
        email = EmailMessage(
            subject=f'📊 Informe Satelital - {informe.parcela.nombre}',
            body=html_message,
            from_email='agrotechdigitalcolombia@gmail.com',
            to=destinatarios,
            reply_to=['soporte@agrotech.com']
        )
        
        email.content_subtype = "html"
        
        # Adjuntar PDF
        email.attach_file(informe.archivo_pdf.path)
        
        # Adjuntar imágenes clave (opcional)
        if informe.mapa_ndvi_imagen:
            email.attach_file(
                informe.mapa_ndvi_imagen.path,
                mimetype='image/png'
            )
        
        # Enviar
        try:
            email.send(fail_silently=False)
            
            # Registrar envío
            informe.registro_envios.create(
                destinatarios=', '.join(destinatarios),
                metodo='email',
                exitoso=True,
                fecha=timezone.now()
            )
            
            return {'exito': True, 'mensaje': 'Email enviado exitosamente'}
            
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}
```

### 3. Envío por WhatsApp

```python
from twilio.rest import Client
import requests

class EnviadorWhatsApp:
    """
    Envía informes via WhatsApp usando Twilio API
    """
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_from = settings.TWILIO_WHATSAPP_NUMBER  # 'whatsapp:+14155238886'
        self.client = Client(self.account_sid, self.auth_token)
    
    def enviar_informe_whatsapp(
        self, 
        informe, 
        numero_destino, 
        mensaje_intro=None
    ):
        """
        Envía el informe por WhatsApp
        
        Args:
            numero_destino: Formato '+57 300 123 4567'
            mensaje_intro: Mensaje personalizado opcional
        """
        # Limpiar número
        numero_limpio = self._limpiar_numero(numero_destino)
        whatsapp_to = f'whatsapp:{numero_limpio}'
        
        # Subir PDF a servidor público temporal
        pdf_url = self._subir_pdf_temporal(informe.archivo_pdf)
        
        # Mensaje de texto
        mensaje_body = mensaje_intro or self._generar_mensaje_default(informe)
        mensaje_body += f"\n\n📄 Descarga el informe completo aquí: {pdf_url}"
        
        try:
            # Enviar mensaje con link
            message = self.client.messages.create(
                from_=self.whatsapp_from,
                to=whatsapp_to,
                body=mensaje_body
            )
            
            # Si el PDF es pequeño (<5MB), enviarlo como media
            if informe.archivo_pdf.size < 5 * 1024 * 1024:
                media_message = self.client.messages.create(
                    from_=self.whatsapp_from,
                    to=whatsapp_to,
                    media_url=[pdf_url]
                )
            
            # Enviar imagen principal
            if informe.mapa_ndvi_imagen:
                imagen_url = self._subir_imagen_temporal(informe.mapa_ndvi_imagen)
                imagen_message = self.client.messages.create(
                    from_=self.whatsapp_from,
                    to=whatsapp_to,
                    media_url=[imagen_url],
                    body='🗺️ Mapa NDVI de tu parcela'
                )
            
            # Registrar envío
            informe.registro_envios.create(
                destinatarios=numero_destino,
                metodo='whatsapp',
                exitoso=True,
                fecha=timezone.now(),
                twilio_sid=message.sid
            )
            
            return {
                'exito': True, 
                'mensaje': 'Enviado por WhatsApp',
                'sid': message.sid
            }
            
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {str(e)}")
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}
    
    def _subir_pdf_temporal(self, archivo_pdf):
        """
        Sube el PDF a un servidor temporal (24h)
        Opciones: AWS S3, Google Cloud Storage, file.io, etc.
        """
        # Opción 1: file.io (público, temporal, gratuito)
        with archivo_pdf.open('rb') as f:
            response = requests.post(
                'https://file.io',
                files={'file': f},
                data={'expires': '1d'}  # 24 horas
            )
        
        if response.status_code == 200:
            return response.json()['link']
        
        # Opción 2: AWS S3 con URL pre-firmada
        # s3_client = boto3.client('s3')
        # url = s3_client.generate_presigned_url(...)
        # return url
        
        # Fallback: URL del servidor Django (debe ser pública)
        return f'https://tu-dominio.com{archivo_pdf.url}'
    
    def _generar_mensaje_default(self, informe):
        """
        Genera mensaje automático de WhatsApp
        """
        return f"""
🌾 *AgroTech - Informe Satelital*

📊 Parcela: *{informe.parcela.nombre}*
📅 Período: {informe.fecha_inicio_analisis.strftime('%d/%m/%Y')} - {informe.fecha_fin_analisis.strftime('%d/%m/%Y')}

✅ Tu informe está listo con:
• Análisis de salud vegetal (NDVI)
• Monitoreo de humedad (NDMI)
• Recomendaciones personalizadas
• Imágenes satelitales

📱 Consulta el análisis completo en el PDF adjunto.
"""
```

---

## 💻 INTERFAZ DE USUARIO {#interfaz}

### Vista de Generación de Informe

```html
{% extends 'base.html' %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Header -->
    <div class="row mb-4">
        <div class="col-12">
            <h2 class="mb-0">
                <i class="fas fa-file-alt me-2" style="color: var(--agrotech-green);"></i>
                Generar Informe Satelital
            </h2>
            <p class="text-muted">Parcela: <strong>{{ parcela.nombre }}</strong></p>
        </div>
    </div>
    
    <!-- Wizard de configuración -->
    <div class="row">
        <div class="col-lg-8">
            <form method="post" id="form-generar-informe">
                {% csrf_token %}
                
                <!-- Paso 1: Período -->
                <div class="card mb-4 datos-card">
                    <div class="card-header">
                        <h5><i class="fas fa-calendar-alt me-2"></i>1. Período de Análisis</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">Fecha Inicio</label>
                                <input type="date" name="fecha_inicio" class="form-control" 
                                       value="{{ fecha_inicio_sugerida }}" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Fecha Fin</label>
                                <input type="date" name="fecha_fin" class="form-control" 
                                       value="{{ fecha_fin_sugerida }}" required>
                            </div>
                        </div>
                        
                        <!-- Shortcuts de período -->
                        <div class="mt-3">
                            <p class="mb-2"><small class="text-muted">Atajos rápidos:</small></p>
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-sm btn-outline-secondary" 
                                        onclick="setPeriodo(6)">Últimos 6 meses</button>
                                <button type="button" class="btn btn-sm btn-outline-secondary" 
                                        onclick="setPeriodo(12)">Último año</button>
                                <button type="button" class="btn btn-sm btn-outline-secondary" 
                                        onclick="setPeriodo(24)">Últimos 2 años</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Paso 2: Selección de Índices -->
                <div class="card mb-4 datos-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line me-2"></i>2. Índices a Incluir</h5>
                    </div>
                    <div class="card-body">
                        <!-- Aquí va el selector de índices detallado -->
                        {% include 'informes/partials/selector_indices.html' %}
                    </div>
                </div>
                
                <!-- Paso 3: Opciones de Análisis -->
                <div class="card mb-4 datos-card">
                    <div class="card-header">
                        <h5><i class="fas fa-robot me-2"></i>3. Análisis con IA</h5>
                    </div>
                    <div class="card-body">
                        <div class="form-check form-switch mb-3">
                            <input class="form-check-input" type="checkbox" 
                                   id="incluir_ia" name="incluir_ia" checked>
                            <label class="form-check-label" for="incluir_ia">
                                <strong>Incluir análisis con Inteligencia Artificial</strong>
                                <br><small class="text-muted">Genera recomendaciones y conclusiones automáticas</small>
                            </label>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Nivel Técnico del Informe</label>
                            <select name="nivel_tecnico" class="form-select">
                                <option value="mixto" selected>Mixto (Técnico + Usuario Común)</option>
                                <option value="tecnico">Solo Técnico (Agrónomos)</option>
                                <option value="comun">Solo Usuario Común (Propietarios)</option>
                            </select>
                            <small class="text-muted">El nivel mixto incluye ambas secciones en el PDF</small>
                        </div>
                        
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" 
                                   id="incluir_imagenes" name="incluir_imagenes" checked>
                            <label class="form-check-label" for="incluir_imagenes">
                                <strong>Incluir imágenes satelitales</strong>
                                <br><small class="text-muted">Añade mapas NDVI, NDMI, SAVI al PDF</small>
                            </label>
                        </div>
                    </div>
                </div>
                
                <!-- Paso 4: Distribución -->
                <div class="card mb-4 datos-card">
                    <div class="card-header">
                        <h5><i class="fas fa-share-alt me-2"></i>4. Opciones de Distribución</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">¿Cómo deseas recibir el informe?</label>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" 
                                       id="descargar_pdf" name="descargar_pdf" checked>
                                <label class="form-check-label" for="descargar_pdf">
                                    📥 Descargar PDF directamente
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" 
                                       id="enviar_email" name="enviar_email">
                                <label class="form-check-label" for="enviar_email">
                                    📧 Enviar por Email
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" 
                                       id="enviar_whatsapp" name="enviar_whatsapp">
                                <label class="form-check-label" for="enviar_whatsapp">
                                    📱 Enviar por WhatsApp
                                </label>
                            </div>
                        </div>
                        
                        <!-- Campos condicionales -->
                        <div id="email-fields" style="display: none;">
                            <label class="form-label">Destinatarios (separados por coma)</label>
                            <input type="email" name="emails" class="form-control" 
                                   placeholder="usuario@ejemplo.com, otro@ejemplo.com" multiple>
                        </div>
                        
                        <div id="whatsapp-fields" style="display: none;">
                            <label class="form-label">Número de WhatsApp</label>
                            <input type="tel" name="whatsapp" class="form-control" 
                                   placeholder="+57 300 123 4567">
                        </div>
                    </div>
                </div>
                
                <!-- Botones de acción -->
                <div class="d-flex justify-content-between">
                    <a href="{% url 'detalle_parcela' parcela.id %}" class="btn btn-light">
                        <i class="fas fa-arrow-left me-1"></i> Cancelar
                    </a>
                    
                    <div>
                        <button type="button" class="btn btn-info me-2" onclick="previsualizarInforme()">
                            <i class="fas fa-eye me-1"></i> Previsualizar
                        </button>
                        <button type="submit" class="btn btn-success">
                            <i class="fas fa-cog me-1"></i> Generar Informe
                        </button>
                    </div>
                </div>
            </form>
        </div>
        
        <!-- Sidebar con resumen -->
        <div class="col-lg-4">
            <div class="card datos-card sticky-top" style="top: 20px;">
                <div class="card-header">
                    <h5><i class="fas fa-info-circle me-2"></i>Resumen de Generación</h5>
                </div>
                <div class="card-body">
                    <div id="resumen-generacion">
                        <!-- Se actualiza con JavaScript -->
                        <p><strong>Período:</strong> <span id="resumen-periodo">No seleccionado</span></p>
                        <p><strong>Índices:</strong> <span id="resumen-indices">Ninguno</span></p>
                        <p><strong>IA:</strong> <span id="resumen-ia">Activado</span></p>
                        <p><strong>Distribución:</strong> <span id="resumen-dist">Descarga</span></p>
                        
                        <hr>
                        
                        <h6>Optimización de Requests:</h6>
                        <div class="alert alert-info mb-0">
                            <small>
                                <strong id="total-requests">0</strong> requests a EOSDA<br>
                                <strong id="datos-existentes">0</strong> meses en caché<br>
                                <strong id="datos-descargar">0</strong> meses a descargar
                            </small>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                💡 <strong>Tip:</strong> Incluir menos índices reduce el tiempo de generación.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// JavaScript para actualizar resumen en tiempo real
document.querySelectorAll('input, select').forEach(el => {
    el.addEventListener('change', actualizarResumen);
});

function actualizarResumen() {
    // Lógica para actualizar el sidebar
    const periodo = calcularPeriodo();
    const indices = obtenerIndicesSeleccionados();
    const ia = document.getElementById('incluir_ia').checked;
    
    document.getElementById('resumen-periodo').textContent = periodo;
    document.getElementById('resumen-indices').textContent = indices.join(', ');
    document.getElementById('resumen-ia').textContent = ia ? 'Activado' : 'Desactivado';
    
    // Calcular requests necesarios
    calcularOptimizacion(indices, periodo);
}

function calcularOptimizacion(indices, periodo) {
    // AJAX para obtener datos existentes
    fetch(`/api/verificar-datos/?parcela={{ parcela.id }}&indices=${indices.join(',')}&periodo=${periodo}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-requests').textContent = data.requests_necesarios;
            document.getElementById('datos-existentes').textContent = data.meses_en_cache;
            document.getElementById('datos-descargar').textContent = data.meses_a_descargar;
        });
}
</script>
{% endblock %}
```

---

## 🎁 FUNCIONES ADICIONALES SUGERIDAS {#funciones}

### 1. **Comparación entre Períodos**
- Comparar 2024 vs 2023
- Ver evolución año a año
- Detectar patrones estacionales

### 2. **Informes Programados**
- Generar automáticamente cada mes
- Enviar por email al propietario
- Alertas proactivas por WhatsApp

### 3. **Benchmarking**
- Comparar con parcelas similares
- Ranking regional de salud vegetal
- "Tu parcela está en el top 15% de la región"

### 4. **Predicciones**
- ML para predecir próximos valores de NDVI
- "Se espera que el NDVI siga aumentando"
- Alertas tempranas de problemas

### 5. **Informes Personalizados por Cultivo**
- Plantillas específicas (café, cacao, arroz)
- Indicadores clave por tipo de cultivo
- Recomendaciones especializadas

### 6. **Exportar a Otros Formatos**
- Word (.docx) para editar
- Excel (.xlsx) con datos crudos
- PowerPoint (.pptx) para presentaciones

### 7. **Modo Offline**
- Generar informes sin conexión
- Sincronizar cuando haya internet
- PWA (Progressive Web App)

### 8. **Colaboración**
- Compartir informe con agrónomos
- Comentarios y anotaciones
- Versionado de informes

---

## 📅 PLAN DE IMPLEMENTACIÓN {#implementacion}

### Fase 1: Fundamentos (Semana 1-2)
✅ **Objetivo:** Sistema básico funcional

1. Diseñar modelo de datos para Informes
2. Implementar lógica de selección de índices
3. Crear sistema de verificación de datos
4. Implementar descarga optimizada

### Fase 2: Generación PDF (Semana 3-4)
✅ **Objetivo:** PDFs profesionales

1. Integrar ReportLab
2. Diseñar plantillas PDF AgroTech
3. Generar gráficos con matplotlib
4. Incluir imágenes satelitales

### Fase 3: IA (Semana 5-6)
✅ **Objetivo:** Análisis inteligente

1. Integrar OpenAI/Claude API
2. Diseñar prompts para análisis técnico/común
3. Sistema de recomendaciones
4. Detección de alertas

### Fase 4: Distribución (Semana 7-8)
✅ **Objetivo:** Multi-canal

1. Descarga directa ✅
2. Envío por Email
3. Integración WhatsApp (Twilio)
4. Sistema de tracking

### Fase 5: Interfaz (Semana 9-10)
✅ **Objetivo:** UX excepcional

1. Wizard de generación
2. Previsualización
3. Dashboard de informes
4. Historial y gestión

### Fase 6: Funciones Avanzadas (Semana 11-12)
✅ **Objetivo:** Diferenciadores

1. Informes programados
2. Comparación entre períodos
3. Exportar a otros formatos
4. Colaboración básica

---

## 📊 MÉTRICAS DE ÉXITO

- **Optimización:** <2 requests promedio por informe (vs 10+ sin optimización)
- **Velocidad:** <30 segundos para informe de 12 meses con IA
- **Calidad:** Análisis IA comprensible para 95% de usuarios
- **Distribución:** 100% de informes enviados exitosamente
- **Satisfacción:** >4.5/5 estrellas en feedback de usuarios

---

## 💰 COSTOS ESTIMADOS

### API Costs (Mensual para 100 usuarios)
- **EOSDA:** $200-400 (depende de requests)
- **OpenAI GPT-4:** $50-150 (análisis IA)
- **Twilio WhatsApp:** $20-50 (envíos)
- **AWS S3 (storage):** $10-30

**Total:** ~$300-650/mes

### Alternativas Low-Cost:
- **IA local** (Ollama + Llama 3): Gratis
- **Email only** (sin WhatsApp): -$20-50
- **Storage local**: -$10-30

**Total Low-Cost:** ~$200-400/mes

---

## 🎯 DECISIÓN: ¿IMPLEMENTAMOS?

### ✅ Ventajas
- Sistema completo y profesional
- Optimización real de requests
- IA añade valor tremendo
- Multi-canal (email + WhatsApp)
- Escalable y mantenible

### ⚠️ Consideraciones
- Desarrollo: ~12 semanas (completo)
- Costos API mensuales
- Mantenimiento de integraciones

### 🚀 Mi Recomendación

**SÍ, implementar en fases:**

1. **Fase 1-2 (MVP):** Solo PDF con datos básicos (2 semanas)
2. **Fase 3 (IA básica):** Análisis simple con IA (1 semana)
3. **Fase 4 (Email):** Distribución por email (1 semana)
4. **Fases 5-6:** Ir agregando según feedback

**Total MVP:** 4-5 semanas

---

## 📝 SIGUIENTE PASO

¿Quieres que empecemos con:
1. **MVP rápido:** PDF básico + IA simple (4 semanas)
2. **Completo:** Todo el sistema (12 semanas)
3. **Custom:** Tú eliges las fases

**¿Cuál prefieres? 🤔**
