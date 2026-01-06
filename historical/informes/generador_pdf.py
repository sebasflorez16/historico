"""
Generador de Informes Técnicos en PDF - AgroTech
Sistema de Análisis Satelital Agrícola con Motor Determinístico

MOTOR DE ANÁLISIS:
- Procesamiento de índices espectrales (NDVI, NDMI, SAVI)
- Análisis estadístico de series temporales
- Detección de tendencias mediante regresión lineal
- Evaluación de variabilidad espacial y temporal
- Generación de recomendaciones agronómicas basadas en umbrales científicos

FUENTES DE DATOS:
- Imágenes satelitales Sentinel-2 (ESA)
- Resolución espacial: 10-20 metros
- Datos climáticos históricos
- Metadatos de calidad de imagen
"""
import os
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from io import BytesIO
from dateutil.relativedelta import relativedelta

# ReportLab imports
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, 
    Table, TableStyle, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas

# Matplotlib para gráficos (usar backend no-GUI para evitar problemas con threads)
import matplotlib
matplotlib.use('Agg')  # ✅ Backend no-GUI, seguro para threads y servidores web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns

# Django imports
from django.conf import settings

# Modelos locales
from informes.models import Parcela, IndiceMensual

# Analizadores
from informes.analizadores.ndvi_analyzer import AnalizadorNDVI
from informes.analizadores.ndmi_analyzer import AnalizadorNDMI
from informes.analizadores.savi_analyzer import AnalizadorSAVI
from informes.analizadores.tendencias_analyzer import DetectorTendencias
from informes.analizadores.recomendaciones_engine import GeneradorRecomendaciones

import logging
logger = logging.getLogger(__name__)


def limpiar_html_completo(texto: str) -> str:
    """
    Limpia HTML COMPLETAMENTE - convierte a formato ReportLab sin tags visibles
    
    Usa enfoque de 3 pasos:
    1. Convertir tags deseados a marcadores temporales
    2. Eliminar TODOS los tags HTML restantes  
    3. Restaurar solo los tags necesarios en formato ReportLab
    """
    if not texto:
        return ""
    
    # Convertir a string
    texto = str(texto)
    
    # Limpieza agresiva de strong mal formados
    texto = re.sub(r'<strong>\s*</strong>', '', texto)  # Eliminar strong vacíos
    texto = re.sub(r'<strong>([^<]*?)(?=<strong>|$)', r'<b>\1</b>', texto)  # strong sin cerrar
    
    # Normalizar <strong> a <b> y </strong> a </b> para evitar duplicidad y errores
    texto = texto.replace('<strong>', '<b>').replace('</strong>', '</b>')
    # PASO 1: Reemplazar tags que queremos mantener con marcadores temporales
    replacements = {
        '<b>': '**BOLD_START**',
        '</b>': '**BOLD_END**',
        '<em>': '**ITALIC_START**',
        '</em>': '**ITALIC_END**',
        '<i>': '**ITALIC_START**',
        '</i>': '**ITALIC_END**',
        '<br>': '**LINEBREAK**',
        '<br/>': '**LINEBREAK**',
        '<BR>': '**LINEBREAK**',
    }
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    
    # PASO 2: Eliminar CUALQUIER tag HTML que quede (regex agresivo)
    texto = re.sub(r'<[^>]+>', '', texto)
    
    # PASO 3: Restaurar los tags que queremos en formato ReportLab
    texto = texto.replace('**BOLD_START**', '<b>')
    texto = texto.replace('**BOLD_END**', '</b>')
    texto = texto.replace('**ITALIC_START**', '<i>')
    texto = texto.replace('**ITALIC_END**', '</i>')
    texto = texto.replace('**LINEBREAK**', '<br/>')
    
    # PASO 4: Limpiar saltos de línea
    texto = texto.replace('\n\n', '<br/><br/>')
    texto = texto.replace('\n', ' ')
    
    # PASO 5: Formatear bullets
    texto = re.sub(r'•\s*', '<br/>  • ', texto)
    texto = re.sub(r'\*\s+', '<br/>  • ', texto)
    
    # PASO 6: Limpiar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'(<br/>\s*){3,}', '<br/><br/>', texto)
    
    return texto.strip()


class GeneradorPDFProfesional:
    """
    Genera informes PDF profesionales con:
    - Logos AgroTech
    - Análisis inteligente de índices
    - Gráficos matplotlib
    - Recomendaciones accionables
    - Diseño moderno y profesional
    """
    
    def __init__(self):
        self.pagesize = A4
        self.ancho, self.alto = A4
        self.margen = 2*cm
        
        # Colores corporativos AgroTech
        self.colores = {
            'verde_principal': colors.HexColor('#2E8B57'),  # Verde AgroTech
            'verde_claro': colors.HexColor('#90EE90'),
            'naranja': colors.HexColor('#FF7A00'),
            'azul': colors.HexColor('#17a2b8'),
            'gris_oscuro': colors.HexColor('#2c3e50'),
            'gris_claro': colors.HexColor('#ecf0f1'),
        }
        
        # Estilos
        self.estilos = self._crear_estilos()
    
    def formato_mes_año_español(self, fecha: date) -> str:
        """Formatea fecha en español (Enero 2025)"""
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[fecha.month]} {fecha.year}"
    
    def _decorar_seccion(self, img_name, height=1.2*cm):
        """Devuelve una banda decorativa para usar como separador de secciones"""
        from reportlab.platypus import Image
        img_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', img_name)
        if os.path.exists(img_path):
            try:
                banda = Image(img_path, width=15*cm, height=height, kind='proportional')
                banda.hAlign = 'CENTER'
                return [banda, Spacer(1, 0.2*cm)]
            except Exception as e:
                logger.warning(f"No se pudo cargar banda decorativa {img_name}: {e}")
        return []

    def _crear_estilos(self):
        """Crea estilos personalizados para el documento"""
        estilos = getSampleStyleSheet()
        
        # Título de portada
        estilos.add(ParagraphStyle(
            name='TituloPortada',
            parent=estilos['Heading1'],
            fontSize=28,
            textColor=self.colores['verde_principal'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo de portada
        estilos.add(ParagraphStyle(
            name='SubtituloPortada',
            parent=estilos['Normal'],
            fontSize=16,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Título de sección
        estilos.add(ParagraphStyle(
            name='TituloSeccion',
            parent=estilos['Heading1'],
            fontSize=18,
            textColor=self.colores['verde_principal'],
            spaceBefore=24,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            borderColor=self.colores['verde_principal'],
            borderWidth=2,
            borderPadding=8
        ))
        
        # Subtítulo de sección
        estilos.add(ParagraphStyle(
            name='SubtituloSeccion',
            parent=estilos['Heading2'],
            fontSize=14,
            textColor=self.colores['azul'],
            spaceBefore=16,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        estilos.add(ParagraphStyle(
            name='TextoNormal',
            parent=estilos['Normal'],
            fontSize=11,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Análisis técnico (fuente mejorada)
        estilos.add(ParagraphStyle(
            name='AnalisisTecnico',
            parent=estilos['Normal'],
            fontSize=12,
            leading=18,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=14,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leftIndent=10,
            rightIndent=10
        ))
        
        # Pie de imagen
        estilos.add(ParagraphStyle(
            name='PieImagen',
            parent=estilos['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        return estilos
    
    def generar_informe_completo(self, parcela_id: int, 
                                meses_atras: int = 12,
                                output_path: str = None) -> str:
        """
        Genera informe completo en PDF
        
        Args:
            parcela_id: ID de la parcela
            meses_atras: Período de análisis (meses)
            output_path: Ruta de salida del PDF (opcional)
        
        Returns:
            Ruta del archivo PDF generado
        """
        # Obtener parcela
        try:
            parcela = Parcela.objects.get(id=parcela_id, activa=True)
        except Parcela.DoesNotExist:
            raise ValueError(f"Parcela {parcela_id} no encontrada")
        
        # Obtener datos históricos - PERIODO REAL SEGÚN DATOS DISPONIBLES
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
        if not indices.exists():
            raise ValueError(f"No hay datos disponibles para la parcela {parcela.nombre}")
        fecha_inicio = date(indices.first().año, indices.first().mes, 1)
        fecha_fin = date(indices.last().año, indices.last().mes, 1)
        
        # Preparar datos para análisis
        datos_analisis = self._preparar_datos_analisis(indices)
        
        # Ejecutar análisis (pasando los índices originales para caché)
        analisis_completo = self._ejecutar_analisis(datos_analisis, parcela, indices)
        
        # Generar gráficos
        graficos = self._generar_graficos(datos_analisis)
        
        # Crear PDF
        if not output_path:
            nombre_archivo = f"informe_{parcela.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(settings.MEDIA_ROOT, 'informes', nombre_archivo)
        
        # Asegurar que existe el directorio
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Construir documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.pagesize,
            rightMargin=self.margen,
            leftMargin=self.margen,
            topMargin=self.margen + 1*cm,  # Espacio para header
            bottomMargin=self.margen + 0.5*cm  # Espacio para footer
        )
        
        # Contenido del documento
        story = []
        
        # Portada
        story.extend(self._crear_portada(parcela, fecha_inicio, fecha_fin))
        story.append(PageBreak())
        
        # Metodología de Análisis
        story.extend(self._crear_seccion_metodologia(parcela, indices, analisis_completo))
        story.append(PageBreak())
        
        # Resumen ejecutivo
        story.extend(self._crear_resumen_ejecutivo(analisis_completo, parcela, datos_analisis))
        story.append(PageBreak())
        
        # Información de la parcela
        story.extend(self._crear_info_parcela(parcela))
        story.append(Spacer(1, 1*cm))
        
        # Análisis de índices
        story.extend(self._crear_seccion_ndvi(analisis_completo['ndvi'], graficos))
        story.append(PageBreak())
        
        story.extend(self._crear_seccion_ndmi(analisis_completo['ndmi'], graficos))
        story.append(PageBreak())
        
        if 'savi' in analisis_completo and analisis_completo['savi']:
            story.extend(self._crear_seccion_savi(analisis_completo['savi'], graficos))
            story.append(PageBreak())
        
        # Análisis de tendencias
        story.extend(self._crear_seccion_tendencias(analisis_completo['tendencias'], graficos))
        story.append(PageBreak())
        
        # Recomendaciones
        story.extend(self._crear_seccion_recomendaciones(analisis_completo['recomendaciones']))
        story.append(PageBreak())
        
        # Tabla de datos
        story.extend(self._crear_tabla_datos(datos_analisis))
        story.append(PageBreak())
        
        # Página de créditos
        story.extend(self._crear_pagina_creditos())
        
        # Construir PDF con headers y footers
        doc.build(story, onFirstPage=self._crear_header_footer, 
                 onLaterPages=self._crear_header_footer)
        
        return output_path
    
    def _preparar_datos_analisis(self, indices: List[IndiceMensual]) -> List[Dict]:
        """Prepara datos en formato para análisis"""
        datos = []
        for indice in indices:
            datos.append({
                'mes': f"{indice.año}-{indice.mes:02d}",
                'periodo': indice.periodo_texto,
                'ndvi': indice.ndvi_promedio,
                'ndmi': indice.ndmi_promedio,
                'savi': indice.savi_promedio,
                'temperatura': indice.temperatura_promedio,
                'precipitacion': indice.precipitacion_total
            })
        return datos
    
    def _ejecutar_analisis(self, datos: List[Dict], parcela: Parcela, indices: List) -> Dict:
        """
        Ejecuta análisis técnico determinístico completo
        
        MOTOR DE ANÁLISIS:
        1. Análisis espectral (NDVI, NDMI, SAVI)
        2. Estadísticas descriptivas y distribución
        3. Detección de tendencias temporales
        4. Análisis de variabilidad espacial
        5. Generación de recomendaciones basadas en umbrales científicos
        """
        # Inicializar analizadores especializados
        analizador_ndvi = AnalizadorNDVI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_ndmi = AnalizadorNDMI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_savi = AnalizadorSAVI(tipo_cultivo=parcela.tipo_cultivo)
        detector_tendencias = DetectorTendencias()
        generador_recomendaciones = GeneradorRecomendaciones(tipo_cultivo=parcela.tipo_cultivo)
        
        # Ejecutar análisis de índices espectrales
        analisis_ndvi = analizador_ndvi.analizar(datos)
        analisis_ndmi = analizador_ndmi.analizar(datos)
        analisis_savi = analizador_savi.analizar(datos) if any(d.get('savi') for d in datos) else None
        
        # Análisis de tendencias temporales
        tendencias = detector_tendencias.analizar_temporal(datos, 'ndvi')
        
        # Generar recomendaciones agronómicas
        recomendaciones = generador_recomendaciones.generar_recomendaciones(
            analisis_ndvi, analisis_ndmi, analisis_savi, tendencias
        )
        
        return {
            'ndvi': analisis_ndvi,
            'ndmi': analisis_ndmi,
            'savi': analisis_savi,
            'tendencias': tendencias,
            'recomendaciones': recomendaciones
        }
    
    def _generar_graficos(self, datos: List[Dict]) -> Dict[str, BytesIO]:
        """Genera todos los gráficos necesarios"""
        graficos = {}
        
        # Gráfico de evolución temporal
        graficos['evolucion_temporal'] = self._grafico_evolucion_temporal(datos)
        
        # Gráfico comparativo
        graficos['comparativo'] = self._grafico_comparativo(datos)
        
        return graficos
    
    def _grafico_evolucion_temporal(self, datos: List[Dict]) -> BytesIO:
        """Genera gráfico de evolución temporal"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Configurar estilo
        sns.set_style("whitegrid")
        
        # Extraer datos
        meses = [d['periodo'] for d in datos]
        ndvi = [d.get('ndvi', 0) for d in datos]
        ndmi = [d.get('ndmi', 0) for d in datos]
        savi = [d.get('savi', 0) for d in datos]
        
        # Graficar
        ax.plot(meses, ndvi, marker='o', linewidth=2.5, color='#2E8B57', label='NDVI (Salud)', markersize=6)
        ax.plot(meses, ndmi, marker='s', linewidth=2.5, color='#17a2b8', label='NDMI (Humedad)', markersize=6)
        if any(savi):
            ax.plot(meses, savi, marker='^', linewidth=2.5, color='#FF7A00', label='SAVI (Cobertura)', markersize=6)
        
        # Configurar
        ax.set_xlabel('Período', fontsize=12, fontweight='bold')
        ax.set_ylabel('Valor del Índice', fontsize=12, fontweight='bold')
        ax.set_title('Evolución Temporal de Índices de Vegetación', 
                     fontsize=14, fontweight='bold', color='#2c3e50')
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Rotar etiquetas
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Guardar en buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _grafico_comparativo(self, datos: List[Dict]) -> BytesIO:
        """Genera gráfico de barras comparativo"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calcular promedios (filtrar None)
        ndvi_valores = [d.get('ndvi') for d in datos if d.get('ndvi') is not None]
        ndmi_valores = [d.get('ndmi') for d in datos if d.get('ndmi') is not None]
        savi_valores = [d.get('savi') for d in datos if d.get('savi') is not None]
        
        ndvi_prom = sum(ndvi_valores) / len(ndvi_valores) if ndvi_valores else 0
        ndmi_prom = sum(ndmi_valores) / len(ndmi_valores) if ndmi_valores else 0
        savi_prom = sum(savi_valores) / len(savi_valores) if savi_valores else 0
        
        indices = ['NDVI\n(Salud)', 'NDMI\n(Humedad)', 'SAVI\n(Cobertura)']
        valores = [ndvi_prom, ndmi_prom, savi_prom]
        colores_barra = ['#2E8B57', '#17a2b8', '#FF7A00']
        
        # Crear barras
        bars = ax.bar(indices, valores, color=colores_barra, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Añadir valores encima de las barras
        for bar, valor in zip(bars, valores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{valor:.3f}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Valor Promedio', fontsize=12, fontweight='bold')
        ax.set_title('Comparación de Índices - Promedio del Período', 
                    fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_ylim(0, max(valores) * 1.2)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _crear_portada(self, parcela: Parcela, fecha_inicio: date, fecha_fin: date) -> List:
        """Crea la portada del informe con diseño profesional estilo EOSDA"""
        from reportlab.lib.utils import ImageReader
        elements = []
        # === IMAGEN DE FONDO DECORATIVA (1.png) ===
        img_fondo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', '1.png')
        if os.path.exists(img_fondo_path):
            try:
                img_fondo = Image(img_fondo_path, width=15*cm, height=8*cm, kind='proportional')
                img_fondo.hAlign = 'CENTER'
                elements.append(img_fondo)
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo cargar imagen de portada: {e}")
        else:
            elements.append(Spacer(1, 2*cm))
        
        # === LOGO AGROTECH GRANDE ===
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Agro Tech logo solo.png')
        if not os.path.exists(logo_path):
            # Alternativa con texto
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'agrotech solo negro.png')
        
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=8*cm, height=8*cm, kind='proportional')
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.8*cm))
            except Exception as e:
                logger.warning(f"No se pudo cargar logo: {e}")
                titulo_logo = Paragraph(
                    '<font size="24" color="#2E8B57"><strong>agrotech</strong></font>',
                    self.estilos['TituloPortada']
                )
                elements.append(titulo_logo)
                elements.append(Spacer(1, 0.5*cm))
        
        # === TÍTULO PRINCIPAL MODERNO CON IMAGEN DECORATIVA AL LADO (2.png) ===
        titulo_img_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', '2.png')
        if os.path.exists(titulo_img_path):
            titulo_principal = Paragraph(
                '<para align="left">'
                '<font size="22" color="#2E8B57"><strong>Análisis Satelital de Precisión</strong></font>'
                '</para>',
                self.estilos['TituloPortada']
            )
            img_titulo = Image(titulo_img_path, width=3*cm, height=3*cm, kind='proportional')
            tabla_titulo = Table([[titulo_principal, img_titulo]], colWidths=[12*cm, 3*cm])
            tabla_titulo.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
            elements.append(tabla_titulo)
        else:
            titulo_principal = Paragraph(
                '<para align="center">'
                '<font size="22" color="#2E8B57"><strong>Análisis Satelital de Precisión</strong></font>'
                '</para>',
                self.estilos['TituloPortada']
            )
            elements.append(titulo_principal)
        elements.append(Spacer(1, 0.3*cm))
        
        subtitulo = Paragraph(
            '<para align="center">'
            '<font size="14" color="#555555"><i>Sistema Inteligente de Monitoreo Agrícola</i></font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(subtitulo)
        # Banda decorativa bajo el título (3.png)
        banda_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', '3.png')
        if os.path.exists(banda_path):
            try:
                banda = Image(banda_path, width=15*cm, height=1.2*cm, kind='proportional')
                banda.hAlign = 'CENTER'
                elements.append(banda)
            except Exception as e:
                logger.warning(f"No se pudo cargar banda decorativa portada: {e}")
        elements.append(Spacer(1, 1.2*cm))
        
        # === CARD FLOTANTE MINIMALISTA CON INFO ===
        info_card_data = [
            ['Parcela', parcela.nombre],
            ['Cultivo', parcela.tipo_cultivo or 'No especificado'],
            ['Extensión', f"{parcela.area_hectareas:.2f} hectáreas"],
            ['Período', f"{self.formato_mes_año_español(fecha_inicio)} - {self.formato_mes_año_español(fecha_fin)}"]
        ]
        
        tabla_card = Table(info_card_data, colWidths=[4.5*cm, 8*cm])
        tabla_card.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2E8B57')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E8B57')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E0E0E0')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (0, -1), 15),
            ('RIGHTPADDING', (0, 0), (0, -1), 10),
            ('LEFTPADDING', (1, 0), (1, -1), 15),
        ]))
        
        # Centrar la card
        from reportlab.platypus import KeepTogether
        tabla_card.hAlign = 'CENTER'
        elements.append(tabla_card)
        elements.append(Spacer(1, 2*cm))
        # Imagen decorativa inferior portada (4.png)
        img_inf_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', '4.png')
        if os.path.exists(img_inf_path):
            try:
                img_inf = Image(img_inf_path, width=15*cm, height=2*cm, kind='proportional')
                img_inf.hAlign = 'CENTER'
                elements.append(img_inf)
            except Exception as e:
                logger.warning(f"No se pudo cargar imagen inferior portada: {e}")
        
        # === PIE DE PORTADA MINIMALISTA ===
        pie = Paragraph(
            '<para align="center">'
            '<font size="9" color="#888888">'
            'Informe Técnico de Análisis Satelital<br/>'
            f'<strong>{datetime.now().strftime("%d de %B de %Y")}</strong>'
            '</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(pie)
        return elements
        def _decorar_seccion(self, img_name, height=1.2*cm):
            """Devuelve una banda decorativa para usar como separador de secciones"""
            from reportlab.platypus import Image
            img_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', img_name)
            if os.path.exists(img_path):
                try:
                    banda = Image(img_path, width=15*cm, height=height, kind='proportional')
                    banda.hAlign = 'CENTER'
                    return [banda, Spacer(1, 0.2*cm)]
                except Exception as e:
                    logger.warning(f"No se pudo cargar banda decorativa {img_name}: {e}")
            return []
    
    def _crear_header_footer(self, canvas_obj, doc):
        """Crea header y footer en cada página"""
        canvas_obj.saveState()
        
        # Header - Logo pequeño
        logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'img', 'favicon.svg')
        if os.path.exists(logo_path):
            try:
                canvas_obj.drawImage(logo_path, self.margen, self.alto - self.margen + 0.5*cm, 
                                   width=1*cm, height=1*cm, preserveAspectRatio=True)
            except:
                pass
        
        # Header - Texto
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(self.colores['gris_oscuro'])
        canvas_obj.drawString(self.margen + 1.5*cm, self.alto - self.margen + 0.7*cm, 
                            "AgroTech - Análisis Satelital Agrícola")
        
        # Footer - Número de página
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawCentredString(self.ancho / 2, self.margen / 2, 
                                     f"Página {doc.page}")
        
        # Footer - Fecha
        canvas_obj.drawRightString(self.ancho - self.margen, self.margen / 2,
                                  datetime.now().strftime('%d/%m/%Y'))
        
        canvas_obj.restoreState()
    
    # Continúo en el siguiente mensaje con las secciones del informe...
    
    def _crear_seccion_metodologia(self, parcela: Parcela, indices: List[IndiceMensual], analisis: Dict) -> List:
        """
        Crea la sección de Metodología de Análisis con explicación detallada del motor técnico
        """
        elements = []
        
        # Decoración superior
        elements.extend(self._decorar_seccion('5.png', height=1*cm))
        
        # Título de la sección
        titulo = Paragraph("🔬 Metodología de Análisis", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Introducción
        intro = Paragraph(
            """
            <strong>El presente informe se basa en un sistema de análisis satelital determinístico que procesa 
            imágenes satelitales de alta resolución y aplica algoritmos científicamente validados para evaluar 
            la salud y condición de los cultivos.</strong>
            """,
            self.estilos['TextoNormal']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.4*cm))
        
        # 1. Fuentes de Datos
        subtitulo1 = Paragraph("📡 <strong>1. Fuentes de Datos Satelitales</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo1)
        elements.append(Spacer(1, 0.2*cm))
        
        texto_fuentes = Paragraph(
            """
            • <strong>Satélite:</strong> Sentinel-2 (ESA - Agencia Espacial Europea)<br/>
            • <strong>Resolución espacial:</strong> 10-20 metros por píxel<br/>
            • <strong>Frecuencia de captura:</strong> Cada 5-10 días (sujeto a condiciones atmosféricas)<br/>
            • <strong>Bandas espectrales utilizadas:</strong> Rojo (B4), Infrarrojo cercano (B8), Infrarrojo de onda corta (B11, B12)<br/>
            • <strong>Validación de calidad:</strong> Se filtran imágenes con nubosidad superior al 20%
            """,
            self.estilos['TextoNormal']
        )
        elements.append(texto_fuentes)
        elements.append(Spacer(1, 0.4*cm))
        
        # 2. Índices Espectrales Calculados
        subtitulo2 = Paragraph("📊 <strong>2. Índices Espectrales Calculados</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo2)
        elements.append(Spacer(1, 0.2*cm))
        
        # Tabla de índices
        datos_indices = [
            ['Índice', 'Fórmula', 'Interpretación', 'Umbrales'],
            [
                '<strong>NDVI</strong><br/>(Vigor Vegetal)',
                '(NIR - Red) / (NIR + Red)',
                'Mide la cantidad y salud de la vegetación. Valores altos indican vegetación densa y saludable.',
                '< 0.2: Suelo desnudo<br/>0.2-0.4: Vegetación escasa<br/>0.4-0.6: Vegetación moderada<br/>> 0.6: Vegetación densa'
            ],
            [
                '<strong>NDMI</strong><br/>(Humedad)',
                '(NIR - SWIR) / (NIR + SWIR)',
                'Evalúa el contenido de humedad en la vegetación. Fundamental para detectar estrés hídrico.',
                '< 0.2: Estrés hídrico severo<br/>0.2-0.4: Estrés moderado<br/>0.4-0.6: Humedad adecuada<br/>> 0.6: Alta humedad'
            ],
            [
                '<strong>SAVI</strong><br/>(Cobertura)',
                '(NIR - Red) / (NIR + Red + L) × (1 + L)<br/>L = 0.5',
                'Ajusta el NDVI para áreas con cobertura vegetal parcial, minimizando el efecto del suelo expuesto.',
                '< 0.2: Suelo predominante<br/>0.2-0.4: Cobertura baja<br/>0.4-0.6: Cobertura moderada<br/>> 0.6: Cobertura alta'
            ]
        ]
        
        tabla_indices = Table(datos_indices, colWidths=[3*cm, 3.5*cm, 5*cm, 4*cm])
        tabla_indices.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.colores['verde_principal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(tabla_indices)
        elements.append(Spacer(1, 0.4*cm))
        
        # 3. Procesamiento y Análisis
        subtitulo3 = Paragraph("⚙️ <strong>3. Procesamiento y Análisis de Datos</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo3)
        elements.append(Spacer(1, 0.2*cm))
        
        texto_procesamiento = Paragraph(
            """
            <strong>a) Análisis Estadístico:</strong> Para cada índice se calculan estadísticas descriptivas mensuales 
            (promedio, mínimo, máximo, desviación estándar) que permiten identificar la variabilidad espacial dentro 
            de la parcela.<br/><br/>
            
            <strong>b) Análisis Temporal:</strong> Se aplica regresión lineal para detectar tendencias a lo largo del 
            período analizado, identificando si hay mejora, deterioro o estabilidad en los índices.<br/><br/>
            
            <strong>c) Análisis de Variabilidad:</strong> Se evalúa el coeficiente de variación (CV) para determinar 
            la homogeneidad espacial del cultivo. CV < 15% indica alta homogeneidad.<br/><br/>
            
            <strong>d) Detección de Anomalías:</strong> Se identifican valores atípicos que pueden indicar problemas 
            localizados (plagas, deficiencias nutricionales, problemas de riego).<br/><br/>
            
            <strong>e) Análisis Cruzado:</strong> Se correlacionan los diferentes índices para obtener una visión 
            integral. Por ejemplo, NDVI bajo + NDMI bajo puede indicar estrés hídrico.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(texto_procesamiento)
        elements.append(Spacer(1, 0.4*cm))
        
        # 4. Generación de Recomendaciones
        subtitulo4 = Paragraph("💡 <strong>4. Generación de Recomendaciones Agronómicas</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo4)
        elements.append(Spacer(1, 0.2*cm))
        
        texto_recomendaciones = Paragraph(
            """
            Las recomendaciones se generan mediante un motor de reglas basado en:<br/><br/>
            
            • <strong>Umbrales científicos:</strong> Valores de referencia validados en literatura agronómica<br/>
            • <strong>Tipo de cultivo:</strong> Adaptación de umbrales según la especie cultivada<br/>
            • <strong>Contexto temporal:</strong> Consideración de la época del año y ciclo fenológico<br/>
            • <strong>Tendencias detectadas:</strong> Priorización de problemas emergentes o recurrentes<br/>
            • <strong>Análisis multivariado:</strong> Combinación de múltiples índices para diagnósticos precisos
            """,
            self.estilos['TextoNormal']
        )
        elements.append(texto_recomendaciones)
        elements.append(Spacer(1, 0.4*cm))
        
        # 5. Resumen del Período Analizado
        subtitulo5 = Paragraph("📅 <strong>5. Datos del Período Analizado</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo5)
        elements.append(Spacer(1, 0.2*cm))
        
        # Calcular estadísticas del período
        total_imagenes = len(indices)
        imagenes_con_ndvi = sum(1 for idx in indices if idx.ndvi_promedio is not None)
        imagenes_con_ndmi = sum(1 for idx in indices if idx.ndmi_promedio is not None)
        imagenes_con_savi = sum(1 for idx in indices if idx.savi_promedio is not None)
        nubosidad_promedio = sum(idx.nubosidad_imagen or 0 for idx in indices) / total_imagenes if total_imagenes > 0 else 0
        
        datos_periodo = [
            ['Total de imágenes procesadas', str(total_imagenes)],
            ['Imágenes con NDVI válido', f"{imagenes_con_ndvi} ({imagenes_con_ndvi/total_imagenes*100:.1f}%)" if total_imagenes > 0 else "0"],
            ['Imágenes con NDMI válido', f"{imagenes_con_ndmi} ({imagenes_con_ndmi/total_imagenes*100:.1f}%)" if total_imagenes > 0 else "0"],
            ['Imágenes con SAVI válido', f"{imagenes_con_savi} ({imagenes_con_savi/total_imagenes*100:.1f}%)" if total_imagenes > 0 else "0"],
            ['Nubosidad promedio', f"{nubosidad_promedio:.1f}%"],
            ['Tipo de cultivo', parcela.tipo_cultivo or 'No especificado'],
            ['Extensión analizada', f"{parcela.area_hectareas:.2f} hectáreas"]
        ]
        
        tabla_periodo = Table(datos_periodo, colWidths=[7*cm, 8*cm])
        tabla_periodo.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), self.colores['gris_claro']),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(tabla_periodo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Nota final
        nota = Paragraph(
            """
            <font size="9" color="#666666"><i>
            <strong>Nota:</strong> Esta metodología se basa en estándares internacionales de teledetección aplicada 
            a la agricultura de precisión. Los algoritmos utilizados han sido validados por instituciones científicas 
            y agencias espaciales como la ESA (European Space Agency) y NASA.
            </i></font>
            """,
            self.estilos['TextoNormal']
        )
        tabla_nota = Table([[nota]], colWidths=[15*cm])
        tabla_nota.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2196F3')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(tabla_nota)
        
        return elements
    
    def _crear_resumen_ejecutivo(self, analisis: Dict, parcela: Parcela, datos: List[Dict]) -> List:
        """Crea resumen ejecutivo del informe basado en análisis técnico determinístico"""
        elements = []
        # Decoración superior
        elements.extend(self._decorar_seccion('6.png', height=1*cm))
        # Título
        titulo = Paragraph("📊 Resumen Ejecutivo", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # ANÁLISIS TÉCNICO DETERMINÍSTICO - SIN IA
        # Calcular métricas del período
        ndvi_datos = analisis['ndvi']
        ndmi_datos = analisis['ndmi']
        savi_datos = analisis.get('savi')
        tendencias = analisis['tendencias']
        
        # Estadísticas principales
        ndvi_prom = ndvi_datos['estadisticas']['promedio']
        ndmi_prom = ndmi_datos['estadisticas']['promedio']
        ndvi_cv = ndvi_datos['estadisticas'].get('coeficiente_variacion', 0)
        ndmi_cv = ndmi_datos['estadisticas'].get('coeficiente_variacion', 0)
        
        # Puntuaciones
        ndvi_punt = ndvi_datos.get('puntuacion', 0)
        ndmi_punt = ndmi_datos.get('puntuacion', 0)
        promedio_general = (ndvi_punt + ndmi_punt) / 2
        
        # Datos climáticos del período
        temp_valores = [d.get('temperatura') for d in datos if d.get('temperatura') is not None]
        precip_valores = [d.get('precipitacion') for d in datos if d.get('precipitacion') is not None]
        temp_prom = sum(temp_valores) / len(temp_valores) if temp_valores else None
        precip_total = sum(precip_valores) if precip_valores else None
        
        # === ANÁLISIS CRUZADO DE ÍNDICES ===
        diagnosticos = []
        nivel_confianza = "ALTA"
        
        # 1. Análisis combinado NDVI + NDMI
        if ndvi_prom < 0.4 and ndmi_prom < 0.3:
            diagnosticos.append({
                'tipo': 'crítico',
                'condicion': 'Estrés Hídrico Severo',
                'descripcion': 'Tanto la salud vegetal (NDVI) como el contenido de humedad (NDMI) están por debajo de los umbrales recomendados, indicando deficiencia severa de agua.',
                'confianza': 'ALTA',
                'recomendacion': 'Implementar riego de emergencia inmediato.'
            })
        elif ndvi_prom > 0.6 and ndmi_prom < 0.3:
            diagnosticos.append({
                'tipo': 'advertencia',
                'condicion': 'Vegetación Densa con Déficit Hídrico',
                'descripcion': 'La biomasa es alta pero el contenido de humedad es bajo, sugiriendo que el cultivo puede estar compensando con raíces profundas o entrando en estrés.',
                'confianza': 'MEDIA',
                'recomendacion': 'Monitorear evolución y considerar riego preventivo.'
            })
        elif ndvi_prom < 0.3 and ndmi_prom > 0.5:
            diagnosticos.append({
                'tipo': 'advertencia',
                'condicion': 'Baja Cobertura Vegetal con Alta Humedad',
                'descripcion': 'El suelo retiene humedad pero la vegetación es escasa. Puede indicar problemas nutricionales, plagas, o fase temprana del cultivo.',
                'confianza': 'MEDIA',
                'recomendacion': 'Evaluar nutrición del suelo y descartar plagas/enfermedades.'
            })
        elif ndvi_prom > 0.6 and ndmi_prom > 0.5:
            diagnosticos.append({
                'tipo': 'normal',
                'condicion': 'Condiciones Óptimas de Cultivo',
                'descripcion': 'Tanto la vegetación como el contenido hídrico presentan valores excelentes, indicando un cultivo saludable y bien hidratado.',
                'confianza': 'ALTA',
                'recomendacion': 'Mantener prácticas actuales de manejo.'
            })
        
        # 2. Análisis de variabilidad espacial
        if ndvi_cv > 25 or ndmi_cv > 25:
            diagnosticos.append({
                'tipo': 'advertencia',
                'condicion': 'Alta Heterogeneidad Espacial',
                'descripcion': f'El lote presenta alta variabilidad espacial (CV NDVI: {ndvi_cv:.1f}%, CV NDMI: {ndmi_cv:.1f}%), indicando condiciones desiguales dentro de la parcela.',
                'confianza': 'ALTA',
                'recomendacion': 'Realizar manejo por zonas (agricultura de precisión) para optimizar recursos.'
            })
        elif ndvi_cv < 15 and ndmi_cv < 15:
            diagnosticos.append({
                'tipo': 'normal',
                'condicion': 'Alta Homogeneidad del Lote',
                'descripcion': f'El lote presenta baja variabilidad espacial (CV < 15%), indicando condiciones uniformes y buen manejo.',
                'confianza': 'ALTA',
                'recomendacion': 'El manejo uniforme actual es adecuado.'
            })
        
        # 3. Análisis de tendencia temporal
        tendencia_dir = tendencias.get('tendencia_lineal', {}).get('direccion', 'estable')
        tendencia_cambio = tendencias.get('tendencia_lineal', {}).get('cambio_porcentual', 0)
        
        if tendencia_dir == 'creciente' and tendencia_cambio > 10:
            diagnosticos.append({
                'tipo': 'positivo',
                'condicion': 'Mejora Sostenida del Cultivo',
                'descripcion': f'Se detecta una tendencia de mejora sostenida del {tendencia_cambio:.1f}% en el período analizado.',
                'confianza': 'ALTA',
                'recomendacion': 'Continuar con las prácticas de manejo actuales.'
            })
        elif tendencia_dir == 'decreciente' and tendencia_cambio < -10:
            diagnosticos.append({
                'tipo': 'crítico',
                'condicion': 'Deterioro Progresivo del Cultivo',
                'descripcion': f'Se detecta una tendencia de deterioro del {tendencia_cambio:.1f}% en el período analizado, requiriendo intervención.',
                'confianza': 'ALTA',
                'recomendacion': 'Investigar causas (estrés hídrico, plagas, nutrición) e implementar correcciones.'
            })
        elif abs(tendencia_cambio) < 5:
            diagnosticos.append({
                'tipo': 'normal',
                'condicion': 'Estabilidad Productiva',
                'descripcion': 'El cultivo mantiene estabilidad en el tiempo sin cambios significativos.',
                'confianza': 'ALTA',
                'recomendacion': 'Monitoreo rutinario suficiente.'
            })
        
        # === CONSTRUCCIÓN DEL RESUMEN ===
        if promedio_general >= 8:
            conclusion_general = "El cultivo presenta <b>excelente estado general</b> con condiciones óptimas en el período analizado."
        elif promedio_general >= 6:
            conclusion_general = "El cultivo muestra <b>buen desempeño</b> con algunas áreas de mejora identificadas."
        elif promedio_general >= 4:
            conclusion_general = "El cultivo presenta <b>estado moderado</b> que requiere atención en ciertas áreas."
        else:
            conclusion_general = "El cultivo muestra <b>signos de estrés significativo</b> que requieren intervención inmediata."
        
        # Generar texto del resumen
        resumen_html = f"""
<b>📊 DIAGNÓSTICO TÉCNICO DEL CULTIVO</b><br/>
{conclusion_general}<br/><br/>

<b>Puntuación General: {promedio_general:.1f}/10</b><br/><br/>

<b>📈 MÉTRICAS PRINCIPALES</b><br/>
• <b>NDVI (Vigor Vegetal):</b> {ndvi_prom:.3f} - {ndvi_datos['estado']['etiqueta']} 
  <font color="{'green' if ndvi_punt >= 7 else 'orange' if ndvi_punt >= 5 else 'red'}">({ndvi_punt:.1f}/10)</font><br/>
• <b>NDMI (Contenido Hídrico):</b> {ndmi_prom:.3f} - {ndmi_datos['estado']['etiqueta']} 
  <font color="{'green' if ndmi_punt >= 7 else 'orange' if ndmi_punt >= 5 else 'red'}">({ndmi_punt:.1f}/10)</font><br/>
• <b>Variabilidad Espacial (NDVI):</b> CV = {ndvi_cv:.1f}% 
  <font color="{'green' if ndvi_cv < 15 else 'orange' if ndvi_cv < 25 else 'red'}">
  ({'Baja - Lote homogéneo' if ndvi_cv < 15 else 'Moderada' if ndvi_cv < 25 else 'Alta - Considerar manejo por zonas'})</font><br/>
• <b>Tendencia Temporal:</b> {tendencia_dir.title()} ({tendencia_cambio:+.1f}%)<br/>
"""

        if temp_prom or precip_total:
            resumen_html += f"""<br/><b>🌡️ CONDICIONES CLIMÁTICAS DEL PERÍODO</b><br/>
• Temperatura promedio: <b>{temp_prom:.1f}°C</b><br/>
• Precipitación acumulada: <b>{precip_total:.1f} mm</b><br/>
"""

        resumen_html += "<br/><b>🔍 DIAGNÓSTICOS IDENTIFICADOS (Análisis Cruzado)</b><br/>"
        
        for i, diag in enumerate(diagnosticos, 1):
            icono = {'crítico': '🔴', 'advertencia': '🟡', 'normal': '🟢', 'positivo': '🟢'}.get(diag['tipo'], '⚪')
            resumen_html += f"""<br/>{icono} <b>{diag['condicion']}</b> <font size="8" color="#666">(Confianza: {diag['confianza']})</font><br/>
{diag['descripcion']}<br/>
<i>→ {diag['recomendacion']}</i><br/>
"""
        
        # Alertas críticas
        alertas_criticas = [r for r in analisis['recomendaciones'] if r['prioridad'] == 'alta']
        if alertas_criticas:
            resumen_html += f"""<br/><b><font color="red">⚠️ ALERTAS CRÍTICAS:</font></b> 
{len(alertas_criticas)} situación(es) requiere(n) atención prioritaria (ver sección de Recomendaciones).<br/>
"""
        else:
            resumen_html += '<br/><font color="green">✅ No se detectaron situaciones críticas que requieran acción inmediata.</font><br/>'
        
        resumen_html += f"""<br/><b>📅 PERÍODO ANALIZADO</b><br/>
• Total de observaciones: {len(datos)} meses<br/>
• Imágenes satelitales procesadas: {len([d for d in datos if d.get('ndvi') is not None])}<br/>
• Tipo de cultivo: {parcela.tipo_cultivo or 'No especificado'}<br/>
• Extensión: {parcela.area_hectareas:.2f} hectáreas<br/>
"""
        
        resumen = Paragraph(resumen_html, self.estilos['TextoNormal'])
        
        # Envolver en tabla con estilo
        tabla_resumen = Table([[resumen]], colWidths=[15*cm])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('BOX', (0, 0), (-1, -1), 2, self.colores['verde_principal']),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(tabla_resumen)
        elements.append(Spacer(1, 0.5*cm))
        
        # Nota metodológica
        nota = Paragraph(
            """
            <font size="8" color="#666"><i><b>Nota Metodológica:</b> Este diagnóstico se basa en análisis cruzado 
            de múltiples índices espectrales, análisis estadístico de variabilidad espacial y temporal, y 
            aplicación de umbrales agronómicos validados científicamente. El nivel de confianza indica la 
            certeza del diagnóstico basado en la calidad y consistencia de los datos disponibles.</i></font>
            """,
            self.estilos['TextoNormal']
        )
        elements.append(nota)
        
        return elements
    
    def _crear_info_parcela(self, parcela: Parcela) -> List:
        """Crea sección de información de la parcela"""
        elements = []
        
        titulo = Paragraph("📍 Información de la Parcela", self.estilos['TituloSeccion'])
        elements.append(titulo)
        
        # Coordenadas del centroide
        if parcela.centroide:
            lat = parcela.centroide.y
            lon = parcela.centroide.x
            coordenadas = f"{lat:.6f}, {lon:.6f}"
        else:
            coordenadas = "No disponible"
        
        info_texto = f"""
<strong>Nombre:</strong> {parcela.nombre}<br/>
<strong>Propietario:</strong> {parcela.propietario}<br/>
<strong>Tipo de Cultivo:</strong> {parcela.tipo_cultivo or 'No especificado'}<br/>
<strong>Área:</strong> {parcela.area_hectareas:.2f} hectáreas<br/>
<strong>Ubicación (Centro):</strong> {coordenadas}<br/>
<strong>Fecha de Inicio de Monitoreo:</strong> {parcela.fecha_inicio_monitoreo.strftime('%d/%m/%Y') if parcela.fecha_inicio_monitoreo else 'No especificado'}<br/>
"""
        
        info = Paragraph(info_texto, self.estilos['TextoNormal'])
        elements.append(info)
        
        return elements
    
    def _crear_seccion_ndvi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDVI"""
        elements = []
        
        titulo = Paragraph("🌱 Análisis NDVI - Salud Vegetal", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado General:</strong> {estado['icono']} {estado['etiqueta']}<br/>
<strong>NDVI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis['puntuacion']}/10<br/>
<strong>Cobertura Estimada:</strong> {analisis['cobertura_estimada']}%<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['AnalisisTecnico']))
        
        # Alertas
        if analisis.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>⚠️ Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis['alertas'][:3]:  # Máximo 3 alertas
                alerta_texto = f"{alerta['icono']} <strong>{alerta['titulo']}:</strong> {alerta['mensaje']}"
                alerta_limpia = limpiar_html_completo(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
        
        return elements
    
    def _crear_seccion_ndmi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDMI"""
        elements = []
        
        titulo = Paragraph("💧 Análisis NDMI - Contenido de Humedad", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado Hídrico:</strong> {estado['icono']} {estado['etiqueta']}<br/>
<strong>NDMI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis['puntuacion']}/10<br/>
<strong>Riesgo Hídrico:</strong> {analisis['riesgo_hidrico']}<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['TextoNormal']))
        
        # Alertas
        if analisis.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>⚠️ Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis['alertas'][:3]:
                alerta_texto = f"{alerta['icono']} <strong>{alerta['titulo']}:</strong> {alerta['mensaje']}"
                alerta_limpia = limpiar_html_completo(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
        
        return elements
    
    def _crear_seccion_savi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis SAVI"""
        elements = []
        
        titulo = Paragraph("🌾 Análisis SAVI - Cobertura Vegetal", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Cobertura:</strong> {estado['icono']} {estado['etiqueta']}<br/>
<strong>SAVI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Exposición de Suelo:</strong> {analisis['exposicion_suelo']}%<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico']))
        
        return elements
    
    def _crear_seccion_tendencias(self, tendencias: Dict, graficos: Dict) -> List:
        """Crea sección de análisis de tendencias"""
        elements = []
        
        titulo = Paragraph("📈 Análisis de Tendencias Temporales", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Gráfico de evolución
        if 'evolucion_temporal' in graficos:
            img = Image(graficos['evolucion_temporal'], width=16*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 1:</strong> Evolución temporal de índices de vegetación durante el período analizado.",
                self.estilos['PieImagen']
            )
            elements.append(pie)
            elements.append(Spacer(1, 1*cm))
        
        # Resumen de tendencias
        if tendencias.get('resumen'):
            resumen_limpio = limpiar_html_completo(tendencias['resumen'])
            elements.append(Paragraph(resumen_limpio, self.estilos['TextoNormal']))
        
        # Tendencia lineal
        if 'tendencia_lineal' in tendencias:
            tl = tendencias['tendencia_lineal']
            tendencia_texto = f"""
<strong>Tendencia Lineal:</strong> {tl.get('direccion', '').title()} - 
Fuerza {tl.get('fuerza', '').title()}<br/>
<strong>Cambio Total:</strong> {tl.get('cambio_porcentual', 0):+.1f}%<br/>
<strong>Confiabilidad:</strong> {tl.get('confianza', '').title()} (R² = {tl.get('r_cuadrado', 0):.3f})<br/>
"""
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(tendencia_texto, self.estilos['TextoNormal']))
        
        # Gráfico comparativo
        if 'comparativo' in graficos:
            elements.append(Spacer(1, 1*cm))
            img = Image(graficos['comparativo'], width=14*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 2:</strong> Comparación de promedios de índices durante el período.",
                self.estilos['PieImagen']
            )
            elements.append(pie)
        
        return elements
    
    def _crear_seccion_recomendaciones(self, recomendaciones: List[Dict]) -> List:
        """Crea sección de recomendaciones"""
        elements = []
        
        titulo = Paragraph("💡 Recomendaciones Agronómicas", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        intro = Paragraph(
            "A continuación se presentan las recomendaciones priorizadas para el manejo del cultivo, "
            "ordenadas por nivel de prioridad (Alta, Media, Baja).",
            self.estilos['TextoNormal']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.5*cm))
        
        # Agrupar por prioridad
        por_prioridad = {'alta': [], 'media': [], 'baja': []}
        for rec in recomendaciones:
            prioridad = rec.get('prioridad', 'baja')
            por_prioridad[prioridad].append(rec)

        # Renderizar por prioridad
        contador = 1
        for prioridad in ['alta', 'media', 'baja']:
            if por_prioridad[prioridad]:
                # Título de prioridad
                if prioridad == 'alta':
                    titulo_prioridad = "🔴 Prioridad Alta"
                elif prioridad == 'media':
                    titulo_prioridad = "🟡 Prioridad Media"
                else:
                    titulo_prioridad = "🟢 Prioridad Baja"

                elements.append(Paragraph(f"<b>{titulo_prioridad}</b>", self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.3*cm))

                for rec in por_prioridad[prioridad]:
                    # Limpiar y justificar cada campo
                    titulo = limpiar_html_completo(f"<b>{contador}. {rec['titulo']}</b>")
                    desc_tecnica = limpiar_html_completo(f"<b>Para técnicos:</b> {rec['descripcion_tecnica']}")
                    desc_simple = limpiar_html_completo(f"<b>En palabras simples:</b> {rec['descripcion_simple']}")
                    acciones = [limpiar_html_completo(f"• {a}") for a in rec['acciones'][:5]]
                    impacto = limpiar_html_completo(f"<b>Impacto esperado:</b> {rec['impacto_esperado']}")
                    tiempo = limpiar_html_completo(f"<b>Tiempo de implementación:</b> {rec['tiempo_implementacion']}")

                    rec_data = [
                        [Paragraph(titulo, self.estilos['AnalisisTecnico'])],
                        [Paragraph(desc_tecnica, self.estilos['AnalisisTecnico'])],
                        [Paragraph(desc_simple, self.estilos['AnalisisTecnico'])],
                        [Paragraph("<b>Acciones sugeridas:</b>", self.estilos['AnalisisTecnico'])]
                    ]
                    for accion in acciones:
                        rec_data.append([Paragraph(accion, self.estilos['AnalisisTecnico'])])
                    rec_data.append([Paragraph(impacto, self.estilos['AnalisisTecnico'])])
                    rec_data.append([Paragraph(tiempo, self.estilos['AnalisisTecnico'])])

                    tabla_rec = Table(rec_data, colWidths=[16*cm])
                    tabla_rec.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('TEXTCOLOR', (0, 0), (-1, -1), self.colores['gris_oscuro']),
                        ('BACKGROUND', (0, 0), (-1, 0), self.colores['gris_claro']),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                    ]))
                    elements.append(tabla_rec)
                    elements.append(Spacer(1, 0.5*cm))
                    contador += 1
        return elements
    
    def _crear_seccion_analisis_gemini(self, analisis_gemini: Dict) -> List:
        """
        Crea sección con análisis detallado de Gemini AI
        Incluye: Análisis de Tendencias, Recomendaciones IA y Alertas
        """
        elements = []
        
        # Título principal de la sección
        titulo = Paragraph(
            "🤖 Análisis Inteligente con IA", 
            self.estilos['TituloSeccion']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.3*cm))
        # Badge informativo
        badge = Paragraph(
            '<para alignment="center"><font color="#17a2b8" size="9">'
            '<i>Los siguientes análisis han sido generados por inteligencia artificial '
            'especializada en agronomía y teledetección satelital.</i></font></para>',
            self.estilos['TextoNormal']
        )
        elements.append(badge)
        elements.append(Spacer(1, 0.7*cm))
        
        # === ANÁLISIS DE TENDENCIAS ===
        if analisis_gemini.get('analisis_tendencias'):
            subtitulo = Paragraph("📈 Análisis de Tendencias", self.estilos['SubtituloSeccion'])
            elements.append(subtitulo)
            elements.append(Spacer(1, 0.3*cm))
            
            tendencias_texto = limpiar_html_completo(analisis_gemini['analisis_tendencias'])
            
            tendencias = Paragraph(tendencias_texto, self.estilos['TextoNormal'])
            elements.append(tendencias)
            elements.append(Spacer(1, 0.7*cm))
        
        # === ANÁLISIS VISUAL DE IMÁGENES SATELITALES ===
        if analisis_gemini.get('analisis_visual'):
            analisis_visual_texto = analisis_gemini['analisis_visual'].strip()
            
            # Solo mostrar si hay análisis visual real (no el mensaje por defecto)
            if analisis_visual_texto and 'no disponible' not in analisis_visual_texto.lower():
                subtitulo = Paragraph("🛰️ Análisis Visual de Imágenes Satelitales", self.estilos['SubtituloSeccion'])
                elements.append(subtitulo)
                elements.append(Spacer(1, 0.3*cm))
                
                analisis_visual_texto = limpiar_html_completo(analisis_visual_texto)
                
                analisis_visual = Paragraph(analisis_visual_texto, self.estilos['TextoNormal'])
                
                # Tabla con fondo verde claro para análisis visual
                tabla_visual = Table([[analisis_visual]], colWidths=[16*cm])
                tabla_visual.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fff4')),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4CAF50')),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                
                elements.append(tabla_visual)
                elements.append(Spacer(1, 0.7*cm))
        
        # === RECOMENDACIONES IA ===
        if analisis_gemini.get('recomendaciones'):
            subtitulo = Paragraph("💡 Recomendaciones del Experto IA", self.estilos['SubtituloSeccion'])
            elements.append(subtitulo)
            elements.append(Spacer(1, 0.3*cm))
            
            recomendaciones_texto = limpiar_html_completo(analisis_gemini['recomendaciones'])
            
            # Crear caja destacada para recomendaciones
            recomendaciones = Paragraph(recomendaciones_texto, self.estilos['TextoNormal'])
            
            # Tabla para dar formato de caja
            tabla_rec = Table([[recomendaciones]], colWidths=[16*cm])
            tabla_rec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f8ff')),
                ('BOX', (0, 0), (-1, -1), 2, self.colores['azul']),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            elements.append(tabla_rec)
            elements.append(Spacer(1, 0.7*cm))
        
        # === ALERTAS ===
        if analisis_gemini.get('alertas'):
            alertas_texto = analisis_gemini['alertas'].strip()
            
            # Solo mostrar si hay alertas reales (no el mensaje por defecto)
            if alertas_texto and 'No se detectaron alertas' not in alertas_texto:
                subtitulo = Paragraph("⚠️ Alertas y Situaciones Críticas", self.estilos['SubtituloSeccion'])
                elements.append(subtitulo)
                elements.append(Spacer(1, 0.3*cm))
                
                alertas_texto = alertas_texto.replace('\n\n', '<br/><br/>')
                alertas_texto = alertas_texto.replace('\n', '<br/>')
                alertas_texto = limpiar_html_completo(alertas_texto)
                
                alertas = Paragraph(alertas_texto, self.estilos['TextoNormal'])
                
                # Tabla con fondo rojo claro para alertas
                tabla_alertas = Table([[alertas]], colWidths=[16*cm])
                tabla_alertas.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff5f5')),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ff4444')),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                
                elements.append(tabla_alertas)
                elements.append(Spacer(1, 0.5*cm))
            else:
                # Mensaje positivo si no hay alertas
                sin_alertas = Paragraph(
                    '<para alignment="center"><font color="green" size="10">'
                    '<b>✅ No se detectaron situaciones críticas que requieran atención inmediata.</b>'
                    '</font></para>',
                    self.estilos['TextoNormal']
                )
                elements.append(sin_alertas)
                elements.append(Spacer(1, 0.5*cm))
        
        # Nota al pie de la sección
        nota = Paragraph(
            '<para alignment="right"><font size="8" color="#666666">'
            '<i>Análisis generado por IA avanzada.</i>'
            '</font></para>',
            self.estilos['TextoNormal']
        )
        elements.append(nota)
        
        return elements
    
    def _evaluar_calidad_imagen(self, tipo_indice: str, valor_promedio: float, 
                                valor_minimo: float, valor_maximo: float) -> Dict:
        """Evalúa cualitativamente la calidad de una imagen satelital"""
        
        # Calcular heterogeneidad espacial
        rango = valor_maximo - valor_minimo if valor_maximo and valor_minimo else 0
        es_heterogeneo = rango > 0.2
        
        if tipo_indice == 'NDVI':
            if valor_promedio >= 0.7:
                return {'etiqueta': 'Excelente', 'icono': '🟢', 'color': '#4CAF50'}
            elif valor_promedio >= 0.5:
                return {'etiqueta': 'Bueno', 'icono': '🟢', 'color': '#8BC34A'}
            elif valor_promedio >= 0.3:
                return {'etiqueta': 'Regular', 'icono': '🟡', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Pobre', 'icono': '🔴', 'color': '#F44336'}
        
        elif tipo_indice == 'NDMI':
            if valor_promedio >= 0.2:
                return {'etiqueta': 'Excelente', 'icono': '💧', 'color': '#2196F3'}
            elif valor_promedio >= 0.0:
                return {'etiqueta': 'Bueno', 'icono': '💧', 'color': '#03A9F4'}
            elif valor_promedio >= -0.2:
                return {'etiqueta': 'Regular', 'icono': '⚠️', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '🔴', 'color': '#F44336'}
        
        elif tipo_indice == 'SAVI':
            if valor_promedio >= 0.5:
                return {'etiqueta': 'Excelente', 'icono': '🌾', 'color': '#4CAF50'}
            elif valor_promedio >= 0.3:
                return {'etiqueta': 'Bueno', 'icono': '🌾', 'color': '#8BC34A'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '⚠️', 'color': '#FFC107'}
        
        return {'etiqueta': 'N/D', 'icono': '❓', 'color': '#999999'}
    
    def _crear_galeria_imagenes_satelitales(self, parcela: Parcela, indices: List[IndiceMensual], analisis_gemini: Dict = None) -> List:
        """
        Crea una galería de imágenes satelitales (NDVI, NDMI, SAVI) mes a mes
        con evaluación técnica basada en umbrales agronómicos
        """
        elements = []
        # Decoración superior (6.png)
        elements.extend(self._decorar_seccion('6.png', height=1*cm))
        # Título de la sección con diseño mejorado
        titulo = Paragraph(
            '📸 <font size="16"><strong>Imágenes Satelitales y Análisis Visual Detallado</strong></font>',
            self.estilos['TituloSeccion']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Introducción mejorada con explicación de colores
        intro = Paragraph(
            """
            <strong>Esta sección presenta un análisis visual detallado de las imágenes satelitales capturadas mes a mes.</strong>
            <br/><br/>
            Cada imagen es evaluada mediante algoritmos determinísticos que analizan los valores espectrales para 
            identificar patrones espaciales, zonas específicas y cambios temporales. Los colores en las imágenes representan:
            <br/><br/>
            • <strong>NDVI (Vigor Vegetal):</strong> Verde oscuro = alta biomasa, amarillo/marrón = baja vegetación<br/>
            • <strong>NDMI (Contenido de Humedad):</strong> Azul/verde = alta humedad, rojo/amarillo = baja humedad<br/>
            • <strong>SAVI (Cobertura del Suelo):</strong> Verde = buena cobertura, marrón = suelo desnudo visible
            """,
            self.estilos['TextoNormal']
        )
        
        # Crear caja destacada para la introducción
        tabla_intro = Table([[intro]], colWidths=[15*cm])
        tabla_intro.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
            ('BOX', (0, 0), (-1, -1), 2, self.colores['verde_principal']),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(tabla_intro)
        elements.append(Spacer(1, 0.7*cm))
        
        # Procesar cada índice mensual
        imagenes_encontradas = 0
        meses_procesados = 0
        
        for idx in indices:
            tiene_imagenes = False
            
            # Verificar si hay imágenes para este mes
            if (idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path)) or \
               (idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path)) or \
               (idx.imagen_savi and os.path.exists(idx.imagen_savi.path)):
                tiene_imagenes = True
            
            # Si hay imágenes para este mes, procesarlas
            if tiene_imagenes:
                meses_procesados += 1
                
                # === SEPARADOR VISUAL ENTRE MESES ===
                if meses_procesados > 1:
                    from reportlab.platypus import HRFlowable
                    elements.append(Spacer(1, 0.3*cm))
                    elements.append(HRFlowable(
                        width="100%", 
                        thickness=2, 
                        color=self.colores['verde_principal'],
                        spaceAfter=0.5*cm,
                        spaceBefore=0.3*cm
                    ))
                
                # === TÍTULO DEL MES CON DISEÑO DESTACADO ===
                titulo_mes = Paragraph(
                    f'<font size="13" color="#2E8B57"><strong>📅 {idx.periodo_texto}</strong></font>',
                    self.estilos['SubtituloSeccion']
                )
                elements.append(titulo_mes)
                elements.append(Spacer(1, 0.2*cm))
                
                # === METADATOS DE LA CAPTURA EN FORMATO MEJORADO ===
                # Coordenadas del centroide
                coord_texto = 'N/A'
                if parcela.centroide:
                    coord_texto = f"{parcela.centroide.y:.6f}, {parcela.centroide.x:.6f}"
                
                metadatos_data = [
                    ['📅 Fecha de captura:', idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'],
                    ['🛰️ Satélite:', idx.satelite_imagen or 'Sentinel-2'],
                    ['📏 Resolución espacial:', f"{idx.resolucion_imagen or 10} metros/píxel"],
                    ['☁️ Nubosidad:', f"{idx.nubosidad_imagen or 0:.1f}%"],
                    ['🌍 Coordenadas:', coord_texto],
                    ['🌡️ Temperatura promedio:', f"{idx.temperatura_promedio:.1f}°C" if idx.temperatura_promedio else 'N/D'],
                    ['💧 Precipitación total:', f"{idx.precipitacion_total:.1f} mm" if idx.precipitacion_total else 'N/D']
                ]
                
                tabla_metadatos = Table(metadatos_data, colWidths=[4*cm, 11*cm])
                tabla_metadatos.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), self.colores['gris_oscuro']),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                
                elements.append(tabla_metadatos)
                elements.append(Spacer(1, 0.5*cm))
                
                # === LAYOUT HORIZONTAL: 3 IMÁGENES LADO A LADO ===
                # Recolectar las 3 imágenes disponibles para este mes
                imagenes_mes = []
                
                # NDVI
                if idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path):
                    imagenes_encontradas += 1
                    imagenes_mes.append({
                        'tipo': 'NDVI',
                        'path': idx.imagen_ndvi.path,
                        'promedio': idx.ndvi_promedio or 0,
                        'minimo': idx.ndvi_minimo or 0,
                        'maximo': idx.ndvi_maximo or 0,
                        'color_badge': colors.HexColor('#4CAF50'),
                        'descripcion': 'Vigor Vegetal'
                    })
                
                # NDMI
                if idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path):
                    imagenes_encontradas += 1
                    imagenes_mes.append({
                        'tipo': 'NDMI',
                        'path': idx.imagen_ndmi.path,
                        'promedio': idx.ndmi_promedio or 0,
                        'minimo': idx.ndmi_minimo or 0,
                        'maximo': idx.ndmi_maximo or 0,
                        'color_badge': colors.HexColor('#2196F3'),
                        'descripcion': 'Humedad'
                    })
                
                # SAVI
                if idx.imagen_savi and os.path.exists(idx.imagen_savi.path):
                    imagenes_encontradas += 1
                    imagenes_mes.append({
                        'tipo': 'SAVI',
                        'path': idx.imagen_savi.path,
                        'promedio': idx.savi_promedio or 0,
                        'minimo': idx.savi_minimo or 0,
                        'maximo': idx.savi_maximo or 0,
                        'color_badge': colors.HexColor('#FF9800'),
                        'descripcion': 'Cobertura Suelo'
                    })
                
                # Crear tabla horizontal de 3 columnas
                if imagenes_mes:
                    celdas_imagenes = []
                    
                    for img_data in imagenes_mes:
                        try:
                            # Imagen satelital con tamaño reducido para evitar superposición
                            img = Image(img_data['path'], width=4.5*cm, height=4.5*cm, kind='proportional')
                            
                            # Badge de tipo de índice
                            badge = Paragraph(
                                f'<para align="center" backColor="{img_data["color_badge"]}" '
                                f'leftIndent="2" rightIndent="2" spaceAfter="3">'
                                f'<font size="9" color="white"><strong>{img_data["tipo"]}</strong></font>'
                                f'</para>',
                                self.estilos['TextoNormal']
                            )
                            
                            # Descripción
                            desc = Paragraph(
                                f'<para align="center"><font size="8" color="#666666">'
                                f'<i>{img_data["descripcion"]}</i></font></para>',
                                self.estilos['TextoNormal']
                            )
                            
                            # Valores estadísticos
                            valores = Paragraph(
                                f'<para align="center"><font size="7">'
                                f'<strong>Prom:</strong> {img_data["promedio"]:.3f}<br/>'
                                f'<font color="#999999">Min: {img_data["minimo"]:.3f} | Max: {img_data["maximo"]:.3f}</font>'
                                f'</font></para>',
                                self.estilos['TextoNormal']
                            )
                            
                            # === ANÁLISIS CUALITATIVO ===
                            evaluacion = self._evaluar_calidad_imagen(
                                tipo_indice=img_data['tipo'],
                                valor_promedio=img_data['promedio'],
                                valor_minimo=img_data['minimo'],
                                valor_maximo=img_data['maximo']
                            )
                            
                            badge_calidad = Paragraph(
                                f'<para align="center"><font size="7" color="{evaluacion["color"]}">'
                                f'<b>{evaluacion["icono"]} {evaluacion["etiqueta"]}</b>'
                                f'</font></para>',
                                self.estilos['TextoNormal']
                            )
                            
                            # Apilar verticalmente: badge + imagen + desc + valores + calidad
                            celda_contenido = [[badge], [img], [Spacer(1, 0.05*cm)], [desc], [Spacer(1, 0.05*cm)], [valores], [Spacer(1, 0.05*cm)], [badge_calidad]]
                            tabla_celda = Table(celda_contenido, colWidths=[5*cm])
                            tabla_celda.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 1),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                                ('TOPPADDING', (0, 0), (-1, -1), 1),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                            ]))
                            
                            celdas_imagenes.append(tabla_celda)
                            
                        except Exception as e:
                            logger.warning(f"Error procesando imagen {img_data['tipo']}: {e}")
                            continue
                    
                    # Crear tabla horizontal de 3 columnas con espaciado correcto
                    if celdas_imagenes:
                        # Rellenar con celdas vacías si faltan imágenes
                        while len(celdas_imagenes) < 3:
                            celda_vacia = Paragraph(
                                '<para align="center"><font size="10" color="#CCCCCC">─</font></para>',
                                self.estilos['TextoNormal']
                            )
                            celdas_imagenes.append(celda_vacia)
                        
                        tabla_horizontal = Table([celdas_imagenes], colWidths=[5*cm, 5*cm, 5*cm])
                        tabla_horizontal.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F0F0F0')),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                            ('LEFTPADDING', (0, 0), (-1, -1), 3),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                        ]))
                        
                        elements.append(tabla_horizontal)
                        elements.append(Spacer(1, 0.7*cm))
                        
                        # Análisis Gemini consolidado para el mes (si está disponible)
                        if hasattr(idx, 'analisis_gemini') and idx.analisis_gemini:
                            elements.extend(self._crear_analisis_gemini_mes(idx, parcela))
        
        # Si no se encontraron imágenes
        if imagenes_encontradas == 0:
            sin_imagenes = Paragraph(
                '<para alignment="center"><font color="#999999" size="11">'
                '<br/><br/><br/>'
                '<b>📭 No hay imágenes satelitales disponibles para este período</b><br/><br/>'
                '<i>Las imágenes se descargarán automáticamente y estarán disponibles en el sistema una vez procesadas.</i>'
                '<br/><br/><br/>'
                '</font></para>',
                self.estilos['TextoNormal']
            )
            tabla_sin_img = Table([[sin_imagenes]], colWidths=[15*cm])
            tabla_sin_img.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ffc107')),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            elements.append(tabla_sin_img)
        else:
            # === ANÁLISIS GLOBAL CONSOLIDADO ===
            elements.extend(self._crear_analisis_global_imagenes(parcela, indices, imagenes_encontradas))
            
            # Nota al final con resumen
            nota_final = Paragraph(
                f'<para alignment="right"><font size="9" color="#2E8B57">'
                f'<strong>✓ Total de imágenes analizadas: {imagenes_encontradas}</strong> | '
                f'Meses procesados: {meses_procesados}'
                f'</font></para>',
                self.estilos['TextoNormal']
            )
            elements.append(Spacer(1, 0.3*cm))
            elements.append(nota_final)
        
        return elements
    
    def _crear_analisis_global_imagenes(self, parcela: Parcela, indices: List[IndiceMensual], 
                                        total_imagenes: int) -> List:
        """
        Crea la sección de análisis global consolidado de todas las imágenes
        usando evaluación técnica basada en estadísticas y umbrales
        """
        elements = []
        
        # Separador visual fuerte
        from reportlab.platypus import HRFlowable
        elements.append(Spacer(1, 0.7*cm))
        elements.append(HRFlowable(
            width="100%", 
            thickness=3, 
            color=self.colores['verde_principal'],
            spaceAfter=0.7*cm,
            spaceBefore=0.3*cm
        ))
        
        # Título de la sección
        titulo_global = Paragraph(
            '🎯 <font size="14"><strong>Análisis Global Consolidado del Período</strong></font>',
            self.estilos['TituloSeccion']
        )
        elements.append(titulo_global)
        elements.append(Spacer(1, 0.5*cm))
        
        # Subtítulo explicativo
        subtitulo = Paragraph(
            '<font size="10"><i>Evaluación integral basada en todas las imágenes satelitales del período, '
            'con identificación de patrones espaciales y recomendaciones específicas por zona.</i></font>',
            self.estilos['TextoNormal']
        )
        elements.append(subtitulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Preparar datos para Gemini
        imagenes_datos = []
        
        for idx in indices:
            # NDVI
            if idx.imagen_ndvi and os.path.exists(idx.imagen_ndvi.path) and idx.ndvi_promedio:
                imagenes_datos.append({
                    'imagen_path': idx.imagen_ndvi.path,
                    'tipo_indice': 'NDVI',
                    'valor_promedio': idx.ndvi_promedio,
                    'mes': idx.periodo_texto,
                    'fecha': idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'
                })
            
            # NDMI
            if idx.imagen_ndmi and os.path.exists(idx.imagen_ndmi.path) and idx.ndmi_promedio:
                imagenes_datos.append({
                    'imagen_path': idx.imagen_ndmi.path,
                    'tipo_indice': 'NDMI',
                    'valor_promedio': idx.ndmi_promedio,
                    'mes': idx.periodo_texto,
                    'fecha': idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'
                })
            
            # SAVI
            if idx.imagen_savi and os.path.exists(idx.imagen_savi.path) and idx.savi_promedio:
                imagenes_datos.append({
                    'imagen_path': idx.imagen_savi.path,
                    'tipo_indice': 'SAVI',
                    'valor_promedio': idx.savi_promedio,
                    'mes': idx.periodo_texto,
                    'fecha': idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'
                })
        
        # Análisis consolidado eliminado - usando motor determinístico
        # Las imágenes se presentan con metadatos técnicos solamente
        
        return elements
    
    
    def _crear_analisis_gemini_mes(self, indice: IndiceMensual, parcela: Parcela) -> List:
        """
        Análisis técnico visual por mes - Motor determinístico
        """
        # Esta función ya no genera análisis con IA
        # El análisis visual se muestra directamente en las tarjetas de cada imagen
        return []
        
        # /01 NDVI - Vigor Vegetal
        if analisis_data.get('ndvi'):
            texto_limpio = limpiar_html_completo(analisis_data["ndvi"])
            
            header_ndvi = Paragraph(
                '<para leftIndent="10" spaceBefore="4" spaceAfter="4">'
                '<font size="10" color="white"><b>🌱 01. NDVI - VIGOR VEGETAL</b></font>'
                '</para>',
                self.estilos['TextoNormal']
            )
            
            contenido_ndvi = Paragraph(
                f'<para leftIndent="15" rightIndent="15" spaceBefore="12" spaceAfter="12" leading="16">'
                f'<font size="9.5" color="#2c3e50">{texto_limpio}</font>'
                f'</para>',
                self.estilos['TextoNormal']
            )
            
            tabla_ndvi = Table([[header_ndvi], [contenido_ndvi]], colWidths=[15.5*cm])
            tabla_ndvi.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#4CAF50')),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
                ('TOPPADDING', (0, 1), (0, 1), 0),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
                ('LEFTPADDING', (0, 1), (0, 1), 0),
                ('RIGHTPADDING', (0, 1), (0, 1), 0),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#4CAF50')),
                ('LINEBELOW', (0, 0), (0, 0), 1.5, colors.HexColor('#43A047')),
            ]))
            elements.append(tabla_ndvi)
            elements.append(Spacer(1, 0.4*cm))
        
        # /02 NDMI - Contenido de Humedad
        if analisis_data.get('ndmi'):
            texto_limpio = limpiar_html_completo(analisis_data["ndmi"])
            
            header_ndmi = Paragraph(
                '<para leftIndent="10" spaceBefore="4" spaceAfter="4">'
                '<font size="10" color="white"><b>💧 02. NDMI - CONTENIDO DE HUMEDAD</b></font>'
                '</para>',
                self.estilos['TextoNormal']
            )
            
            contenido_ndmi = Paragraph(
                f'<para leftIndent="15" rightIndent="15" spaceBefore="12" spaceAfter="12" leading="16">'
                f'<font size="9.5" color="#2c3e50">{texto_limpio}</font>'
                f'</para>',
                self.estilos['TextoNormal']
            )
            
            tabla_ndmi = Table([[header_ndmi], [contenido_ndmi]], colWidths=[15.5*cm])
            tabla_ndmi.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#2196F3')),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
                ('TOPPADDING', (0, 1), (0, 1), 0),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
                ('LEFTPADDING', (0, 1), (0, 1), 0),
                ('RIGHTPADDING', (0, 1), (0, 1), 0),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2196F3')),
                ('LINEBELOW', (0, 0), (0, 0), 1.5, colors.HexColor('#1E88E5')),
            ]))
            elements.append(tabla_ndmi)
            elements.append(Spacer(1, 0.4*cm))
        
        # /03 SAVI - Cobertura del Suelo
        if analisis_data.get('savi'):
            texto_limpio = limpiar_html_completo(analisis_data["savi"])
            
            header_savi = Paragraph(
                '<para leftIndent="10" spaceBefore="4" spaceAfter="4">'
                '<font size="10" color="white"><b>🌾 03. SAVI - COBERTURA DEL SUELO</b></font>'
                '</para>',
                self.estilos['TextoNormal']
            )
            
            contenido_savi = Paragraph(
                f'<para leftIndent="15" rightIndent="15" spaceBefore="12" spaceAfter="12" leading="16">'
                f'<font size="9.5" color="#2c3e50">{texto_limpio}</font>'
                f'</para>',
                self.estilos['TextoNormal']
            )
            
            tabla_savi = Table([[header_savi], [contenido_savi]], colWidths=[15.5*cm])
            tabla_savi.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#FF9800')),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
                ('TOPPADDING', (0, 1), (0, 1), 0),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
                ('LEFTPADDING', (0, 1), (0, 1), 0),
                ('RIGHTPADDING', (0, 1), (0, 1), 0),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#FF9800')),
                ('LINEBELOW', (0, 0), (0, 0), 1.5, colors.HexColor('#FB8C00')),
            ]))
            elements.append(tabla_savi)
            elements.append(Spacer(1, 0.4*cm))
        
        # /04 Recomendaciones PRIORITARIAS
        if analisis_data.get('recomendaciones'):
            texto_limpio = limpiar_html_completo(analisis_data['recomendaciones'])
            
            header_recom = Paragraph(
                '<para leftIndent="10" spaceBefore="4" spaceAfter="4">'
                '<font size="10" color="white"><b>⚡ 04. RECOMENDACIONES PRIORITARIAS</b></font>'
                '</para>',
                self.estilos['TextoNormal']
            )
            
            contenido_recom = Paragraph(
                f'<para leftIndent="15" rightIndent="15" spaceBefore="12" spaceAfter="12" leading="16">'
                f'<font size="9.5" color="#2c3e50"><b>{texto_limpio}</b></font>'
                f'</para>',
                self.estilos['TextoNormal']
            )
            
            tabla_recom = Table([[header_recom], [contenido_recom]], colWidths=[15.5*cm])
            tabla_recom.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#FF5722')),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#FFF8E1')),
                ('TOPPADDING', (0, 1), (0, 1), 0),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
                ('LEFTPADDING', (0, 1), (0, 1), 0),
                ('RIGHTPADDING', (0, 1), (0, 1), 0),
                ('BOX', (0, 0), (-1, -1), 2.5, colors.HexColor('#FF5722')),
                ('LINEBELOW', (0, 0), (0, 0), 2, colors.HexColor('#E64A19')),
            ]))
            elements.append(tabla_recom)
            elements.append(Spacer(1, 0.6*cm))
        
        return elements
    
    def _agregar_imagen_con_analisis(self, indice: IndiceMensual, tipo_indice: str, 
                                      imagen_path: str, descripcion: str, usar_gemini: bool = False) -> List:
        """
        Agrega una imagen satelital con su análisis visual específico usando Gemini AI
        
        Args:
            indice: IndiceMensual con los datos del mes
            tipo_indice: 'NDVI', 'NDMI', 'SAVI'
            imagen_path: Ruta a la imagen
            descripcion: Descripción del índice
            usar_gemini: Si usar Gemini AI para análisis visual (default: False para ahorrar tokens)
        """
        elements = []
        
        try:
            # === IMAGEN ===
            # Cargar y mostrar la imagen más grande para mejor visualización
            img = Image(imagen_path, width=14*cm, height=10*cm)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.2*cm))
            
            # === TÍTULO Y DESCRIPCIÓN ===
            titulo_imagen = Paragraph(
                f"<strong>{tipo_indice}</strong> - {descripcion}",
                self.estilos['PieImagen']
            )
            elements.append(titulo_imagen)
            elements.append(Spacer(1, 0.3*cm))
            
            # === VALORES NUMÉRICOS ===
            valor_promedio = None
            valor_minimo = None
            valor_maximo = None
            
            if tipo_indice == 'NDVI':
                valor_promedio = indice.ndvi_promedio
                valor_minimo = indice.ndvi_minimo
                valor_maximo = indice.ndvi_maximo
            elif tipo_indice == 'NDMI':
                valor_promedio = indice.ndmi_promedio
                valor_minimo = indice.ndmi_minimo
                valor_maximo = indice.ndmi_maximo
            elif tipo_indice == 'SAVI':
                valor_promedio = indice.savi_promedio
                valor_minimo = indice.savi_minimo
                valor_maximo = indice.savi_maximo
            
            if valor_promedio is not None:
                min_texto = f"{valor_minimo:.3f}" if valor_minimo is not None else "N/A"
                max_texto = f"{valor_maximo:.3f}" if valor_maximo is not None else "N/A"
                
                valores_texto = f"""
<font size="9" color="#2c3e50">
<strong>Valor promedio:</strong> {valor_promedio:.3f} | 
<strong>Mínimo:</strong> {min_texto} | 
<strong>Máximo:</strong> {max_texto}
</font>
"""
                valores = Paragraph(valores_texto, self.estilos['TextoNormal'])
                elements.append(valores)
                elements.append(Spacer(1, 0.3*cm))
            
            # El análisis visual ya está incluido en la tarjeta de evaluación de calidad
            
            elements.append(Spacer(1, 0.3*cm))
            
        except Exception as e:
            logger.error(f"❌ Error agregando imagen {tipo_indice} de {indice.periodo_texto}: {str(e)}")
            error_msg = Paragraph(
                f'<font color="red">Error cargando imagen {tipo_indice}</font>',
                self.estilos['TextoNormal']
            )
            elements.append(error_msg)
        
        return elements
    
    def _obtener_datos_mes_anterior(self, indice: IndiceMensual, tipo_indice: str) -> Optional[Dict]:
        """
        Obtiene datos del mes anterior para comparación temporal
        """
        try:
            if indice.mes == 1:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año - 1, mes=12
                ).first()
            else:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año, mes=indice.mes - 1
                ).first()
            
            if mes_anterior:
                valor_anterior = None
                if tipo_indice == 'NDVI':
                    valor_anterior = mes_anterior.ndvi_promedio
                elif tipo_indice == 'NDMI':
                    valor_anterior = mes_anterior.ndmi_promedio
                elif tipo_indice == 'SAVI':
                    valor_anterior = mes_anterior.savi_promedio
                
                if valor_anterior:
                    return {
                        'fecha': mes_anterior.fecha_imagen.strftime('%d/%m/%Y') if mes_anterior.fecha_imagen else 'N/A',
                        'tipo_indice': tipo_indice,
                        'valor': valor_anterior
                    }
        except Exception as e:
            logger.debug(f"No se pudo obtener datos del mes anterior: {str(e)}")
        
        return None
    
    def _generar_analisis_visual_imagen(self, indice: IndiceMensual, tipo_indice: str, 
                                        valor_promedio: float) -> str:
        """
        Genera un análisis visual específico basado en los valores del índice
        y el contexto temporal (comparación con mes anterior si está disponible)
        """
        if valor_promedio is None:
            return ""
        
        analisis_partes = []
        
        # === INTERPRETACIÓN DEL VALOR ===
        if tipo_indice == 'NDVI':
            if valor_promedio >= 0.7:
                interpretacion = "La imagen muestra <strong>vegetación muy vigorosa</strong> con tonos verdes intensos. "
                interpretacion += "Las áreas más oscuras (verdes) indican alta densidad de biomasa y excelente salud vegetal."
            elif valor_promedio >= 0.5:
                interpretacion = "La imagen muestra <strong>vegetación saludable</strong> con predominio de tonos verdes. "
                interpretacion += "Se observa buena cobertura vegetal con desarrollo normal del cultivo."
            elif valor_promedio >= 0.3:
                interpretacion = "La imagen muestra <strong>vegetación moderada</strong> con tonos amarillos-verdes. "
                interpretacion += "Posibles áreas con menor vigor vegetal o cultivo en etapa temprana."
            else:
                interpretacion = "La imagen muestra <strong>baja vegetación</strong> con tonos amarillos-marrones. "
                interpretacion += "Predominio de suelo desnudo o vegetación muy dispersa/estresada."
        
        elif tipo_indice == 'NDMI':
            if valor_promedio >= 0.2:
                interpretacion = "La imagen refleja <strong>alto contenido de humedad</strong> en la vegetación. "
                interpretacion += "Tonos azules-verdes indican buena hidratación de las plantas."
            elif valor_promedio >= 0.0:
                interpretacion = "La imagen muestra <strong>contenido moderado de humedad</strong>. "
                interpretacion += "Vegetación con niveles normales de agua."
            elif valor_promedio >= -0.2:
                interpretacion = "La imagen indica <strong>bajo contenido de humedad</strong>. "
                interpretacion += "Tonos cálidos sugieren estrés hídrico potencial o vegetación seca."
            else:
                interpretacion = "La imagen muestra <strong>muy baja humedad</strong> con tonos rojos-marrones. "
                interpretacion += "Vegetación severamente estresada o suelo desnudo."
        
        elif tipo_indice == 'SAVI':
            if valor_promedio >= 0.5:
                interpretacion = "La imagen muestra <strong>excelente cobertura vegetal</strong>. "
                interpretacion += "Mínima exposición de suelo desnudo visible."
            elif valor_promedio >= 0.3:
                interpretacion = "La imagen muestra <strong>buena cobertura vegetal</strong>. "
                interpretacion += "Vegetación bien establecida con algo de suelo visible."
            else:
                interpretacion = "La imagen muestra <strong>cobertura vegetal baja</strong>. "
                interpretacion += "Considerable exposición de suelo desnudo entre la vegetación."
        
        analisis_partes.append(interpretacion)
        
        # === ANÁLISIS ESPACIAL (si hay heterogeneidad) ===
        if indice.ndvi_maximo and indice.ndvi_minimo and tipo_indice == 'NDVI':
            rango = indice.ndvi_maximo - indice.ndvi_minimo
            if rango > 0.2:
                analisis_partes.append(
                    f"<br/><br/><strong>Variabilidad espacial:</strong> Se observa <strong>heterogeneidad significativa</strong> "
                    f"dentro de la parcela (rango: {rango:.3f}). Las áreas más claras pueden corresponder a zonas con "
                    f"menor vigor, posiblemente en las zonas periféricas o áreas con condiciones menos favorables."
                )
            else:
                analisis_partes.append(
                    "<br/><br/><strong>Uniformidad:</strong> La parcela muestra <strong>distribución relativamente uniforme</strong> "
                    "del índice, lo que indica condiciones homogéneas en la mayoría del área cultivada."
                )
        
        # === COMPARACIÓN TEMPORAL (buscar mes anterior) ===
        try:
            # Buscar el mes anterior
            if indice.mes == 1:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año - 1, mes=12
                ).first()
            else:
                mes_anterior = indice.parcela.indices_mensuales.filter(
                    año=indice.año, mes=indice.mes - 1
                ).first()
            
            if mes_anterior:
                valor_anterior = None
                if tipo_indice == 'NDVI':
                    valor_anterior = mes_anterior.ndvi_promedio
                elif tipo_indice == 'NDMI':
                    valor_anterior = mes_anterior.ndmi_promedio
                elif tipo_indice == 'SAVI':
                    valor_anterior = mes_anterior.savi_promedio
                
                if valor_anterior:
                    cambio = valor_promedio - valor_anterior
                    cambio_pct = (cambio / abs(valor_anterior)) * 100 if valor_anterior != 0 else 0
                    
                    if abs(cambio) > 0.05:  # Cambio significativo
                        if cambio > 0:
                            analisis_partes.append(
                                f"<br/><br/><strong>Cambio temporal:</strong> Comparado con {mes_anterior.periodo_texto}, "
                                f"se observa un <strong>incremento notable</strong> ({cambio:+.3f}, {cambio_pct:+.1f}%). "
                                f"Visualmente esto se traduce en mayor intensidad de color verde/azul en la imagen actual, "
                                f"indicando mejora en las condiciones de la vegetación."
                            )
                        else:
                            analisis_partes.append(
                                f"<br/><br/><strong>Cambio temporal:</strong> Comparado con {mes_anterior.periodo_texto}, "
                                f"se observa una <strong>disminución notable</strong> ({cambio:.3f}, {cambio_pct:.1f}%). "
                                f"Visualmente se aprecia un cambio hacia tonos más cálidos (amarillos/marrones), "
                                f"lo que sugiere reducción en vigor vegetal o contenido de humedad."
                            )
        except Exception as e:
            logger.debug(f"No se pudo comparar con mes anterior: {str(e)}")
        
        return "".join(analisis_partes)
    
    def _crear_tabla_datos(self, datos: List[Dict]) -> List:
        """Crea tabla con datos mensuales"""
        elements = []
        
        titulo = Paragraph("📋 Datos Mensuales Detallados", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Preparar datos de la tabla
        table_data = [['Período', 'NDVI', 'NDMI', 'SAVI', 'Temp (°C)', 'Precip (mm)']]
        
        for dato in datos:
            table_data.append([
                dato['periodo'],
                f"{dato.get('ndvi', 0):.3f}" if dato.get('ndvi') else 'N/D',
                f"{dato.get('ndmi', 0):.3f}" if dato.get('ndmi') else 'N/D',
                f"{dato.get('savi', 0):.3f}" if dato.get('savi') else 'N/D',
                f"{dato.get('temperatura', 0):.1f}" if dato.get('temperatura') else 'N/D',
                f"{dato.get('precipitacion', 0):.1f}" if dato.get('precipitacion') else 'N/D'
            ])
        
        # Crear tabla con estilo moderno difuminado
        tabla = Table(table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),  # Verde AgroTech
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Filas alternadas con verde muy claro (difuminado sutil)
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F8F4')]),
            # Bordes sutiles y difuminados
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#2E7D32')),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(tabla)
        
        return elements    
    def _crear_pagina_creditos(self) -> List:
        """Crea página final con créditos e información legal"""
        elements = []
        
        # Título
        titulo = Paragraph(
            '<para align="center"><font size="14" color="#2E7D32"><strong>Créditos e Información</strong></font></para>',
            self.estilos['TituloSeccion']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 1*cm))
        
        # Sección de tecnologías
        tecnologias = Paragraph(
            '<para align="left">'
            '<font size="10" color="#2c3e50"><strong>🛰️ Tecnologías Satelitales</strong></font><br/>'
            '<font size="9" color="#555555">'
            '• Imágenes: Sentinel-2 (ESA Copernicus Programme)<br/>'
            '• Resolución espacial: 10-20 metros/píxel<br/>'
            '• Índices espectrales: NDVI, NDMI, SAVI'
            '</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(tecnologias)
        elements.append(Spacer(1, 0.7*cm))
        
        # Sección de análisis IA
        ia_info = Paragraph(
            '<para align="left">'
            '<font size="10" color="#2c3e50"><strong>🤖 Análisis Inteligente</strong></font><br/>'
            '<font size="9" color="#555555">'
            '• Motor de IA: Google Gemini 2.0 Flash<br/>'
            '• Procesamiento: Análisis espacial y temporal de patrones de cultivo<br/>'
            '• Recomendaciones: Basadas en algoritmos científicos validados'
            '</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(ia_info)
        elements.append(Spacer(1, 0.7*cm))
        
        # Créditos de imágenes decorativas
        creditos_img = Paragraph(
            '<para align="left">'
            '<font size="10" color="#2c3e50"><strong>📸 Imágenes Decorativas</strong></font><br/>'
            '<font size="8" color="#777777">'
            '• Fotografía satelital: Unsplash (licencia libre)<br/>'
            '• Imágenes agrícolas: Unsplash Contributors<br/>'
            '• Todas las imágenes utilizadas bajo licencias de uso libre comercial'
            '</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(creditos_img)
        elements.append(Spacer(1, 1*cm))
        
        # Aviso legal
        aviso = Paragraph(
            '<para align="center">'
            '<font size="8" color="#999999">'
            '<i>Este informe fue generado automáticamente por AgroTech Sistema de Análisis Satelital. '
            'Los datos y recomendaciones son de carácter informativo y deben ser complementados con '
            'inspección de campo y criterio agronómico profesional.</i>'
            '</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(aviso)
        elements.append(Spacer(1, 1.5*cm))
        
        # Logo y fecha al final
        footer_creditos = Paragraph(
            '<para align="center">'
            '<font size="10" color="#2E7D32"><strong>agrotech</strong></font><br/>'
            f'<font size="8" color="#888888">Análisis Satelital de Precisión · {datetime.now().strftime("%Y")}</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(footer_creditos)
        
        # Imagen decorativa bottom si existe
        img_bottom_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'pdf_decorativas', 'cultivos_aereo.jpg')
        if os.path.exists(img_bottom_path):
            try:
                from reportlab.platypus import Flowable
                class ImagenDecorativaBottom(Flowable):
                    def __init__(self, width, height):
                        Flowable.__init__(self)
                        self.width = width
                        self.height = height
                    
                    def draw(self):
                        try:
                            self.canv.saveState()
                            self.canv.setFillAlpha(0.1)
                            self.canv.drawImage(img_bottom_path, 0, -2*cm, 
                                              width=self.width, height=4*cm, 
                                              preserveAspectRatio=True, mask='auto')
                            self.canv.restoreState()
                        except:
                            pass
                
                elements.append(Spacer(1, 1*cm))
                img_fondo = ImagenDecorativaBottom(17*cm, 4*cm)
                elements.append(img_fondo)
            except Exception as e:
                logger.warning(f"No se pudo agregar imagen decorativa bottom: {e}")
        
        return elements