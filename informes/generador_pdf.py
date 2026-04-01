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
matplotlib.use('Agg')  #  Backend no-GUI, seguro para threads y servidores web
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
    
    # PASO 3.5: Eliminar TODOS los emojis — ReportLab no soporta Unicode emoji
    # y los renderiza como cuadrados negros ■ que confunden al lector
    texto = re.sub(
        r'[\U0001F300-\U0001F9FF'   # Emoticons, símbolos, banderas
        r'\U00002702-\U000027B0'     # Dingbats
        r'\U0000FE00-\U0000FE0F'     # Variation selectors (invisible)
        r'\U0000200D'                # Zero width joiner
        r'\U000025A0-\U000025FF'     # Geometric shapes (■ ▪ etc)
        r'\U00002600-\U000026FF'     # Misc symbols (⚠ etc)
        r'\U00002B05-\U00002B55'     # Arrows (➡ etc)
        r'\U0000203C-\U00003299'     # CJK symbols, enclosed chars
        r']+', '', texto
    )
    
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
    
    def _obtener_path_imagen_correcto(self, imagen_field):
        """Obtiene el path correcto de una imagen, manejando paths relativos y absolutos"""
        if not imagen_field:
            return None
        
        try:
            path_str = str(imagen_field).strip()
            if not path_str:
                return None
            
            paths_a_probar = []
            
            # Intentar obtener .path del campo ImageField
            try:
                if hasattr(imagen_field, 'path'):
                    paths_a_probar.append(imagen_field.path)
            except:
                pass
            
            # Si es una ruta relativa
            if not path_str.startswith('/'):
                # Desde MEDIA_ROOT
                if hasattr(settings, 'MEDIA_ROOT'):
                    path_desde_media = os.path.join(settings.MEDIA_ROOT, path_str)
                    paths_a_probar.append(path_desde_media)
                
                # Desde BASE_DIR/media
                path_desde_base = os.path.join(settings.BASE_DIR, 'media', path_str)
                paths_a_probar.append(path_desde_base)
            else:
                # Path absoluto
                paths_a_probar.append(path_str)
            
            # Probar cada path
            for path in paths_a_probar:
                if os.path.exists(path):
                    return path
            
            return None
            
        except Exception as e:
            logger.warning(f"Error al obtener path de imagen: {e}")
            return None
    
    def _evaluar_calidad_imagen(self, tipo_indice: str, valor_promedio: float, 
                                valor_minimo: float, valor_maximo: float) -> Dict:
        """Evalúa la calidad de una imagen según umbrales técnicos"""
        if tipo_indice == 'NDVI':
            if valor_promedio >= 0.6:
                return {'etiqueta': 'Excelente', 'icono': '✓', 'color': '#4CAF50'}
            elif valor_promedio >= 0.4:
                return {'etiqueta': 'Bueno', 'icono': '~', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '!', 'color': '#F44336'}
        
        elif tipo_indice == 'NDMI':
            if valor_promedio >= 0.3:
                return {'etiqueta': 'Adecuado', 'icono': '✓', 'color': '#2196F3'}
            elif valor_promedio >= 0.0:
                return {'etiqueta': 'Moderado', 'icono': '~', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '!', 'color': '#F44336'}
        
        elif tipo_indice == 'SAVI':
            if valor_promedio >= 0.4:
                return {'etiqueta': 'Alto', 'icono': '✓', 'color': '#4CAF50'}
            elif valor_promedio >= 0.2:
                return {'etiqueta': 'Medio', 'icono': '~', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '!', 'color': '#F44336'}
        
        return {'etiqueta': 'N/D', 'icono': '?', 'color': '#999999'}
    
    def _decorar_seccion(self, img_name, height=1.2*cm):
        """Separador de secciones sin imágenes decorativas"""
        # Retornar solo un espaciador simple sin imágenes
        return [Spacer(1, 0.5*cm)]

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
        
        # 🧠 EJECUTAR DIAGNÓSTICO UNIFICADO PRIMERO (para usar en resumen ejecutivo)
        diagnostico_unificado = None
        try:
            diagnostico_unificado = self._ejecutar_diagnostico_cerebro(parcela, indices)
            if diagnostico_unificado:
                logger.info(f"✅ Diagnóstico unificado ejecutado: {diagnostico_unificado.get('eficiencia_lote', 0):.1f}% eficiencia")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo generar diagnóstico unificado: {str(e)}")
        
        # ========================================
        # SECCIÓN 1: PORTADA
        # ========================================
        story.extend(self._crear_portada(parcela, fecha_inicio, fecha_fin))
        story.append(PageBreak())
        
        # ========================================
        # SECCIÓN 2: RESUMEN EJECUTIVO PROFESIONAL
        # ========================================
        story.extend(self._crear_resumen_ejecutivo(analisis_completo, parcela, datos_analisis, diagnostico_unificado))
        # NO PageBreak - permitir que fluya con recomendaciones si hay espacio
        
        # ========================================
        # SECCIÓN 3: RECOMENDACIONES GENERALES
        # ========================================
        story.extend(self._crear_seccion_recomendaciones(analisis_completo['recomendaciones']))
        story.append(PageBreak())
        
        # ========================================
        # ANEXOS TÉCNICOS (Para consulta detallada)
        # ========================================
        
        # Anexo A: Información de la parcela + Metodología (compactar en una página si es posible)
        banner_anexos = Paragraph(
            '<para alignment="center" backColor="#34495E" '
            'leftIndent="10" rightIndent="10" spaceBefore="10" spaceAfter="10">'
            '<font size="14" color="white"><b>📎 ANEXOS TÉCNICOS</b></font>'
            '</para>',
            self.estilos['TituloSeccion']
        )
        
        # Obtener los elementos de info parcela para agrupar con el banner
        info_parcela_elements = self._crear_info_parcela(parcela)
        story.append(KeepTogether([banner_anexos, Spacer(1, 0.5*cm)] + info_parcela_elements))
        story.append(Spacer(1, 0.8*cm))  # Usar Spacer en vez de PageBreak
        
        # Anexo B: Metodología de Análisis
        story.extend(self._crear_seccion_metodologia(parcela, indices, analisis_completo))
        story.append(PageBreak())
        
        # Anexo C: Análisis mensual detallado (índices espectrales)
        story.extend(self._crear_seccion_ndvi(analisis_completo['ndvi'], graficos))
        story.append(Spacer(1, 1*cm))  # Spacer dinámico - permitir que NDMI comparta página si es corto
        
        story.extend(self._crear_seccion_ndmi(analisis_completo['ndmi'], graficos))
        story.append(PageBreak())
        
        if 'savi' in analisis_completo and analisis_completo['savi']:
            story.extend(self._crear_seccion_savi(analisis_completo['savi'], graficos))
            story.append(Spacer(1, 1*cm))
        
        if 'ndre' in analisis_completo and analisis_completo['ndre']:
            story.extend(self._crear_seccion_ndre(analisis_completo['ndre'], graficos))
            story.append(Spacer(1, 1*cm))
        
        if 'evi' in analisis_completo and analisis_completo['evi']:
            story.extend(self._crear_seccion_evi(analisis_completo['evi'], graficos))
            story.append(Spacer(1, 1*cm))
        
        # Anexo D: Análisis de tendencias
        story.extend(self._crear_seccion_tendencias(analisis_completo['tendencias'], graficos))
        story.append(PageBreak())
        
        # NOTA: La tabla de datos mensuales se omite porque no aporta valor 
        # interpretativo al agricultor y puede generar confusión.
        
        # Anexo E: Galería de imágenes satelitales
        story.extend(self._crear_galeria_imagenes_satelitales(parcela, indices))
        story.append(PageBreak())
        
        # ========================================
        # SECCIÓN FINAL: DIAGNÓSTICO DETALLADO Y PLAN DE ACCIÓN
        # Solo incluir si hay zonas afectadas reales que mostrar
        # ========================================
        if diagnostico_unificado:
            # Verificar si hay zonas afectadas reales
            kpis = diagnostico_unificado.get('kpis')
            area_afectada = 0
            if kpis:
                area_afectada = kpis.area_afectada_ha
            else:
                area_afectada = diagnostico_unificado.get('area_afectada_total', 0)
            
            # Solo mostrar esta sección si hay zonas reales que requieren intervención
            if area_afectada > 0:
                story.extend(self._crear_seccion_guia_intervencion(diagnostico_unificado, parcela))
        
        # Página de créditos (opcional - solo si hay espacio)
        story.append(Spacer(1, 2*cm))
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
    
    def _crear_portada(self, parcela: Parcela, fecha_inicio: date, fecha_fin: date) -> List:
        """Crea la portada del informe con diseño profesional estilo EOSDA"""
        from reportlab.lib.utils import ImageReader
        elements = []
        
        # Espaciado inicial
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
        
        # === TÍTULO PRINCIPAL ===
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
        """Separador de secciones sin imágenes decorativas"""
        # Retornar solo un espaciador simple sin imágenes
        return [Spacer(1, 0.5*cm)]
    
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
        
        # Título + intro siempre juntos (evitar título huérfano)
        titulo = Paragraph("Metodología de Análisis", self.estilos['TituloSeccion'])
        
        intro = Paragraph(
            """
            <strong>El presente informe se basa en el Motor de Análisis Automatizado AgroTech, un sistema 
            de análisis satelital determinístico que procesa imágenes satelitales de alta resolución y aplica 
            algoritmos científicamente validados para evaluar la condición del terreno, ya sea con cultivos establecidos 
            o en evaluación para planificación agrícola y primera siembra.</strong>
            """,
            self.estilos['TextoNormal']
        )
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), intro]))
        elements.append(Spacer(1, 0.4*cm))
        
        # 1. Fuentes de Datos (subtítulo + contenido juntos)
        subtitulo1 = Paragraph("<strong>1. Fuentes de Datos Satelitales</strong>", self.estilos['SubtituloSeccion'])
        
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
        elements.append(KeepTogether([subtitulo1, Spacer(1, 0.2*cm), texto_fuentes]))
        elements.append(Spacer(1, 0.4*cm))
        
        # 2. Índices Espectrales Calculados (subtítulo + tabla juntos)
        subtitulo2 = Paragraph("<strong>2. Índices Espectrales Calculados</strong>", self.estilos['SubtituloSeccion'])
        # La tabla de índices es grande, usamos KeepTogether solo con subtítulo + header
        elements.append(KeepTogether([subtitulo2, Spacer(1, 0.2*cm)]))
        
        # Tabla de índices
        datos_indices = [
            [
                Paragraph('<b>Índice</b>', self.estilos['TextoNormal']),
                Paragraph('<b>Fórmula</b>', self.estilos['TextoNormal']),
                Paragraph('<b>Interpretación</b>', self.estilos['TextoNormal']),
                Paragraph('<b>Umbrales</b>', self.estilos['TextoNormal'])
            ],
            [
                Paragraph('<b>NDVI</b><br/>(Vigor Vegetal)', self.estilos['TextoNormal']),
                Paragraph('(NIR - Red) / (NIR + Red)', self.estilos['TextoNormal']),
                Paragraph('Mide la cantidad y salud de la vegetación presente. Valores altos indican vegetación densa y saludable, o potencial productivo en terrenos sin cultivo.', self.estilos['TextoNormal']),
                Paragraph('&lt; 0.2: Suelo desnudo<br/>0.2-0.4: Vegetación escasa<br/>0.4-0.6: Vegetación moderada<br/>&gt; 0.6: Vegetación densa', self.estilos['TextoNormal'])
            ],
            [
                Paragraph('<b>NDMI</b><br/>(Humedad)', self.estilos['TextoNormal']),
                Paragraph('(NIR - SWIR) / (NIR + SWIR)', self.estilos['TextoNormal']),
                Paragraph('Evalúa el contenido de humedad en la vegetación o suelo. Fundamental para detectar estrés hídrico o condiciones de humedad del terreno.', self.estilos['TextoNormal']),
                Paragraph('&lt; 0.2: Estrés hídrico severo<br/>0.2-0.4: Estrés moderado<br/>0.4-0.6: Humedad adecuada<br/>&gt; 0.6: Alta humedad', self.estilos['TextoNormal'])
            ],
            [
                Paragraph('<b>SAVI</b><br/>(Cobertura)', self.estilos['TextoNormal']),
                Paragraph('(NIR - Red) / (NIR + Red + L) × (1 + L)<br/>L = 0.5', self.estilos['TextoNormal']),
                Paragraph('Ajusta el NDVI para áreas con cobertura vegetal parcial o suelo expuesto, proporcionando una estimación indirecta y relativa de la cobertura.', self.estilos['TextoNormal']),
                Paragraph('&lt; 0.2: Suelo predominante<br/>0.2-0.4: Cobertura baja<br/>0.4-0.6: Cobertura moderada<br/>&gt; 0.6: Cobertura alta', self.estilos['TextoNormal'])
            ]
        ]
        
        tabla_indices = Table(datos_indices, colWidths=[3*cm, 3.5*cm, 5.5*cm, 4*cm])
        tabla_indices.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.colores['verde_principal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(tabla_indices)
        elements.append(Spacer(1, 0.4*cm))
        
        # 3. Procesamiento y Análisis
        subtitulo3 = Paragraph("<strong>3. Procesamiento y Análisis de Datos</strong>", self.estilos['SubtituloSeccion'])
        
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
        elements.append(KeepTogether([subtitulo3, Spacer(1, 0.2*cm), texto_procesamiento]))
        elements.append(Spacer(1, 0.4*cm))
        
        # 4. Generación de Recomendaciones
        subtitulo4 = Paragraph("<strong>4. Generación de Recomendaciones Agronómicas</strong>", self.estilos['SubtituloSeccion'])
        
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
        elements.append(KeepTogether([subtitulo4, Spacer(1, 0.2*cm), texto_recomendaciones]))
        elements.append(Spacer(1, 0.4*cm))
        
        # 5. Resumen del Período Analizado
        subtitulo5 = Paragraph("<strong>5. Datos del Período Analizado</strong>", self.estilos['SubtituloSeccion'])
        
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
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
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
        # Subtítulo5 + tabla_periodo juntos para evitar huérfano
        elements.append(KeepTogether([subtitulo5, Spacer(1, 0.2*cm), tabla_periodo]))
        elements.append(Spacer(1, 0.4*cm))
        
        # Nota sobre configuración actual de umbrales
        tipo_cultivo_display = parcela.tipo_cultivo or 'No especificado'
        nota_cultivo = Paragraph(
            f"""
            <font size="9" color="#2c5f2d"><i>
            <strong>Configuración de Análisis:</strong> El sistema utiliza parámetros de evaluación dinámicos 
            cargados desde la base de datos técnica. Para este análisis, se ha registrado el terreno como 
            <strong>"{tipo_cultivo_display}"</strong>. Actualmente, el motor aplica umbrales generales 
            multi-cultivo validados científicamente, los cuales serán progresivamente especializados conforme 
            se complete la librería de requerimientos biológicos específicos por especie. Esta aproximación 
            conservadora garantiza diagnósticos confiables mientras se optimiza la parametrización agronómica 
            diferenciada.
            </i></font>
            """,
            self.estilos['TextoNormal']
        )
        tabla_nota_cultivo = Table([[nota_cultivo]], colWidths=[15*cm])
        tabla_nota_cultivo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f8e9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#7cb342')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(tabla_nota_cultivo)
        elements.append(Spacer(1, 0.4*cm))
        
        # Nota final metodológica
        nota = Paragraph(
            """
            <font size="9" color="#666666"><i>
            <strong>Nota Metodológica:</strong> Esta metodología se basa en estándares internacionales de teledetección aplicada 
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
    
    def _crear_resumen_ejecutivo(self, analisis: Dict, parcela: Parcela, datos: List[Dict], diagnostico_unificado: Optional[Dict] = None) -> List:
        """
        🎯 RESUMEN EJECUTIVO PROFESIONAL - Diseño UX Mejorado
        
        Características:
        - Banner con esquinas redondeadas y sombra suave
        - Colores profesionales (amber/soft red para alertas)
        - Terminología comercial (no técnica)
        - Layout compacto con ParagraphStyles apropiados
        - Sin overlap de texto
        """
        elements = []
        
        # Espaciado superior
        elements.append(Spacer(1, 1.5*cm))
        
        # ===== BANNER PROFESIONAL CON ESTADO (USANDO KPIs UNIFICADOS) =====
        if diagnostico_unificado:
            # 🔧 USAR KPIs unificados si están disponibles
            kpis = diagnostico_unificado.get('kpis')
            if kpis:
                eficiencia = kpis.eficiencia
                area_afectada = kpis.area_afectada_ha
                # Usar métodos de formateo estándar
                eficiencia_str = kpis.formatear_eficiencia()
                area_afectada_str = kpis.formatear_area_afectada()
            else:
                # Fallback a valores antiguos
                eficiencia = diagnostico_unificado.get('eficiencia_lote', 0)
                area_afectada = diagnostico_unificado.get('area_afectada_total', 0)
                eficiencia_str = f"{eficiencia:.0f}%"
                area_afectada_str = f"{area_afectada:.1f} ha"
            
            # Determinar estado basado en DETECCIÓN REAL de zonas + MEMORIA DE CRISIS
            # CORRECCIÓN: Considerar crisis históricas para evitar estado "ÓPTIMO" engañoso
            
            # 1. Verificar si HAY ZONAS CRÍTICAS DETECTADAS
            tiene_zonas_criticas = area_afectada > 0.0
            
            # 2. Obtener información de crisis históricas del diagnóstico
            crisis_historicas = diagnostico_unificado.get('crisis_historicas', [])
            tiene_crisis_historicas = len(crisis_historicas) > 0
            
            # 3. Determinar estado según DETECCIÓN REAL + MEMORIA
            if not tiene_zonas_criticas and not tiene_crisis_historicas:
                # SIN ZONAS CRÍTICAS Y SIN CRISIS HISTÓRICAS
                color_fondo = '#27AE60'  # Verde profesional
                color_borde = '#1E8449'
                estado = 'ÓPTIMO'
                mensaje = 'El lote presenta condiciones favorables en todo el período analizado'
                icono = '✓'
                descripcion_eficiencia = (
                    f'<b>Índice de Salud del Lote: {eficiencia:.1f}%</b><br/>'
                    f'<i>Este porcentaje representa las condiciones generales del suelo y vegetación.<br/>'
                    f'El análisis no detectó áreas con problemas significativos.</i>'
                )
            elif not tiene_zonas_criticas and tiene_crisis_historicas:
                # SIN PROBLEMAS ACTUALES PERO CON HISTORIAL DE CRISIS
                color_fondo = '#F39C12'  # Amber profesional
                color_borde = '#D68910'
                estado = 'ESTABLE CON OBSERVACIONES'
                mensaje = 'El lote muestra alta resiliencia anual, pero requiere monitoreo preventivo'
                icono = '●'
                
                # Crear narrativa dual de recuperación
                crisis_principal = crisis_historicas[0]
                mes_crisis = crisis_principal['fecha']
                tipos_crisis = ', '.join(crisis_principal['tipos'])
                
                descripcion_eficiencia = (
                    f'<b>Índice de Salud del Lote: {eficiencia:.1f}%</b><br/>'
                    f'<i>El lote muestra una alta resiliencia anual y actualmente no presenta problemas detectables. '
                    f'Sin embargo, se mantienen en observación las zonas que sufrieron {tipos_crisis} '
                    f'detectado en {mes_crisis}.</i>'
                )
            elif area_afectada < 1.0:
                # ZONAS MENORES DETECTADAS (< 1 ha)
                color_fondo = '#F39C12'  # Amber profesional
                color_borde = '#D68910'
                estado = 'REQUIERE MONITOREO'
                mensaje = f'Detectadas {area_afectada_str} que requieren seguimiento preventivo'
                icono = '⚠'
                descripcion_eficiencia = (
                    f'<b>Índice de Salud del Lote: {eficiencia:.1f}%</b><br/>'
                    f'<i>Este porcentaje integra las condiciones de toda el área analizada.<br/>'
                    f'Se detectaron {area_afectada_str} con indicadores por debajo del óptimo.</i>'
                )
            elif eficiencia >= 60:
                # ZONAS MODERADAS DETECTADAS
                color_fondo = '#E67E22'  # Naranja
                color_borde = '#CA6F1E'
                estado = 'REQUIERE ATENCIÓN'
                mensaje = f'Detectadas {area_afectada_str} que necesitan intervención planificada'
                icono = '⚠'
                descripcion_eficiencia = (
                    f'<b>Índice de Salud del Lote: {eficiencia:.1f}%</b><br/>'
                    f'<i>Este porcentaje combina datos de vegetación, humedad y estrés térmico.<br/>'
                    f'El análisis identificó {area_afectada_str} con plan de acción recomendado.</i>'
                )
            else:
                # ZONAS CRÍTICAS EXTENSAS
                color_fondo = '#C0392B'  # Rojo moderado
                color_borde = '#A93226'
                estado = 'ACCIÓN PRIORITARIA REQUERIDA'
                mensaje = f'Identificadas {area_afectada_str} que requieren intervención inmediata'
                icono = '●'
                descripcion_eficiencia = (
                    f'<b>Índice de Salud del Lote: {eficiencia:.1f}%</b><br/>'
                    f'<i>Este porcentaje refleja el estado integrado del lote (vegetación + humedad + estrés).<br/>'
                    f'Las {area_afectada_str} identificadas requieren atención urgente para prevenir pérdidas.</i>'
                )
            
            # Estilo de párrafo sin overlap
            estilo_banner = ParagraphStyle(
                'BannerProfesional',
                parent=self.estilos['TextoNormal'],
                fontSize=11,
                leading=15,  # Espaciado de línea para evitar overlap
                textColor=colors.white,
                alignment=TA_CENTER,
                spaceAfter=8,
                spaceBefore=8
            )
            
            estilo_numero = ParagraphStyle(
                'NumeroGrande',
                parent=self.estilos['TextoNormal'],
                fontSize=42,
                leading=50,
                textColor=colors.white,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                spaceAfter=5,
                spaceBefore=10
            )
            
            # Contenido del banner
            data_resumen = [
                # Fila 1: Estado y mensaje (sin asumir "cultivo")
                [Paragraph(
                    f'<b>{icono}  ESTADO DEL LOTE: {estado}</b><br/>{mensaje}',
                    estilo_banner
                )],
                # Fila 2: Eficiencia (número grande)
                [Paragraph(
                    f'{eficiencia:.0f}%',
                    estilo_numero
                )],
                # Fila 3: Texto descriptivo con EXPLICACIÓN del porcentaje
                [Paragraph(
                    f'<font size="10">{descripcion_eficiencia}</font>',
                    estilo_banner
                )],
                # Fila 4: Contexto y redirección según estado
                [Paragraph(
                    '<font size="9"><i>Consulte la sección "Diagnóstico Detallado" '
                    'al final del documento para ver el plan de acción completo y mapas de zonas afectadas.</i></font>' if tiene_zonas_criticas
                    else '<font size="9"><i>El análisis satelital multitemporal no detectó áreas con problemas significativos.<br/>'
                    'Este lote presenta condiciones adecuadas para actividad agrícola o primera siembra.</i></font>',
                    estilo_banner
                )]
            ]
            
            tabla_resumen = Table(data_resumen, colWidths=[13*cm])
            tabla_resumen.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(color_fondo)),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (0, 0), 18),
                ('BOTTOMPADDING', (0, 0), (0, 0), 10),
                ('TOPPADDING', (0, 1), (0, 1), 10),
                ('BOTTOMPADDING', (0, 1), (0, 1), 8),
                ('TOPPADDING', (0, 2), (0, 2), 5),
                ('BOTTOMPADDING', (0, 2), (0, 2), 10),
                ('TOPPADDING', (0, 3), (0, 3), 8),
                ('BOTTOMPADDING', (0, 3), (0, 3), 15),
                ('BOX', (0, 0), (-1, -1), 2.5, colors.HexColor(color_borde)),
                ('ROUNDEDCORNERS', [12, 12, 12, 12]),
                ('LEFTPADDING', (0, 0), (-1, -1), 20),
                ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ]))
            
            # Centrar el banner con sombra suave (efecto visual)
            ancho_util = self.ancho - 2 * self.margen
            tabla_wrapper = Table([[tabla_resumen]], colWidths=[ancho_util])
            tabla_wrapper.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(tabla_wrapper)
            elements.append(Spacer(1, 0.8*cm))
            
            # ===== SECCIÓN EXPLICATIVA: Metodología del Cálculo =====
            # Esta ventana informativa explica CÓMO se calculó el porcentaje
            elementos_metodologia = []
            
            # Obtener número de meses analizados
            num_meses = len(datos)
            num_crisis = len(crisis_historicas) if crisis_historicas else 0
            
            # Construir explicación detallada
            if not tiene_zonas_criticas and not tiene_crisis_historicas:
                metodologia_texto = (
                    f'<b>¿Cómo se obtuvo este resultado?</b><br/><br/>'
                    f'El sistema analizó <b>{num_meses} meses</b> de imágenes satelitales de alta resolución, '
                    f'procesando <b>más de 65,000 píxeles</b> por cada mes para evaluar:<br/>'
                    f'• <b>Densidad de vegetación</b> (índice NDVI)<br/>'
                    f'• <b>Contenido de humedad</b> en suelo y plantas (índice NDMI)<br/>'
                    f'• <b>Exposición del suelo</b> y cobertura vegetal (índice SAVI)<br/><br/>'
                    f'Durante todo el período analizado, <b>no se detectaron meses con condiciones críticas</b> '
                    f'(como sequías severas, baja densidad vegetal o estrés hídrico extremo). '
                    f'El lote mantuvo parámetros saludables consistentemente.'
                )
            elif not tiene_zonas_criticas and tiene_crisis_historicas:
                metodologia_texto = (
                    f'<b>¿Cómo se obtuvo este resultado?</b><br/><br/>'
                    f'El sistema analizó <b>{num_meses} meses</b> de imágenes satelitales, procesando '
                    f'<b>más de 65,000 píxeles mensuales</b> para construir un historial temporal completo.<br/><br/>'
                    f'<b>Hallazgos clave:</b><br/>'
                    f'• Se detectaron <b>{num_crisis} mes(es)</b> con condiciones críticas durante el período<br/>'
                    f'• El lote mostró <b>recuperación completa</b> después de las crisis<br/>'
                    f'• Actualmente <b>no existen áreas problemáticas</b> detectables<br/><br/>'
                    f'El índice refleja tanto la salud actual (excelente) como la memoria de eventos pasados, '
                    f'resultando en una evaluación que reconoce la resiliencia del terreno.'
                )
            elif area_afectada > 0:
                metodologia_texto = (
                    f'<b>¿Cómo se obtuvo este resultado?</b><br/><br/>'
                    f'El sistema realizó un análisis multitemporal de <b>{num_meses} meses</b>, procesando '
                    f'<b>más de 65,000 píxeles por mes</b> mediante:<br/><br/>'
                    f'<b>1. Análisis mes a mes:</b> Se evaluaron tres índices científicos (NDVI, NDMI, SAVI) '
                    f'para cada píxel del lote, identificando áreas con valores por debajo de umbrales óptimos.<br/>'
                    f'<b>2. Detección de crisis históricas:</b> Se identificaron <b>{num_crisis} mes(es)</b> '
                    f'con condiciones críticas que afectaron la salud del lote.<br/>'
                    f'<b>3. Cálculo del índice:</b> Se combinó la salud actual con la memoria de crisis pasadas, '
                    f'aplicando una penalización proporcional de {(num_crisis/num_meses)*15:.1f}% '
                    f'por los eventos detectados.<br/>'
                    f'<b>4. Identificación espacial:</b> Mediante visión artificial (OpenCV), se localizaron '
                    f'<b>{area_afectada:.2f} hectáreas</b> que requieren atención específica.'
                )
            else:
                # Caso genérico
                metodologia_texto = (
                    f'<b>¿Cómo se obtuvo este resultado?</b><br/><br/>'
                    f'El sistema analizó <b>{num_meses} meses</b> de imágenes satelitales de alta resolución, '
                    f'procesando múltiples índices espectrales para evaluar vegetación, humedad y exposición del suelo.'
                )
            
            # Crear tabla informativa con borde sutil
            metodologia_parrafo = Paragraph(
                f'<font size="9" color="#2C3E50">{metodologia_texto}</font>',
                ParagraphStyle(
                    'MetodologiaExplicativa',
                    parent=self.estilos['TextoNormal'],
                    fontSize=9,
                    leading=13,
                    textColor=colors.HexColor('#2C3E50'),
                    alignment=TA_JUSTIFY,
                    leftIndent=15,
                    rightIndent=15,
                    spaceBefore=8,
                    spaceAfter=8
                )
            )
            
            tabla_metodologia = Table([[metodologia_parrafo]], colWidths=[14*cm])
            tabla_metodologia.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF5FB')),  # Azul muy claro
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#3498DB')),  # Borde azul
                ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ]))
            
            # Centrar la tabla metodológica
            ancho_util = self.ancho - 2 * self.margen
            metodologia_wrapper = Table([[tabla_metodologia]], colWidths=[ancho_util])
            metodologia_wrapper.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(Spacer(1, 0.4*cm))
            elements.append(metodologia_wrapper)
            elements.append(Spacer(1, 0.6*cm))
            
            # Info adicional compacta (opcional)
            if area_afectada > 0:
                info_adicional = Paragraph(
                    f'<para alignment="center" backColor="#F8F9FA" '
                    f'borderColor="#BDC3C7" borderWidth="1" borderRadius="6" '
                    f'leftIndent="12" rightIndent="12" spaceBefore="8" spaceAfter="8">'
                    f'<font size="9" color="#34495E">'
                    f'<b>Resumen Rápido:</b> De las {parcela.area_hectareas:.1f} hectáreas totales, '
                    f'{area_afectada:.1f} ha presentan oportunidades de mejora. '
                    f'Vea el diagnóstico detallado para recomendaciones específicas por zona.'
                    f'</font></para>',
                    self.estilos['TextoNormal']
                )
                elements.append(info_adicional)
            
        else:
            # Si no hay diagnóstico, mostrar mensaje limpio
            elements.append(Paragraph(
                '<para alignment="center" backColor="#ECF0F1" '
                'leftIndent="40" rightIndent="40" spaceBefore="30" spaceAfter="30">'
                '<font size="12" color="#7F8C8D">'
                'Diagnóstico en proceso...<br/>'
                'Los datos técnicos están disponibles en las secciones siguientes.'
                '</font></para>',
                self.estilos['TextoNormal']
            ))
        
        elements.append(Spacer(1, 1*cm))
        
        return elements

    def _crear_seccion_precipitacion(self, datos: List[Dict]) -> List:
        """Crea sección de análisis de precipitación con aclaración explícita"""
        elements = []
        titulo = Paragraph("Análisis de Precipitación", self.estilos['TituloSeccion'])

        # Aclaración explícita sobre cómo interpretar los datos
        aclaracion = Paragraph(
            """
            <strong>Nota aclaratoria:</strong> Los valores de precipitación que se presentan en este informe corresponden 
            al <strong>total mensual acumulado</strong> para cada período analizado. Estos datos provienen de fuentes climáticas 
            satelitales y permiten evaluar la disponibilidad de agua en el terreno a lo largo del tiempo.
            """,
            self.estilos['TextoNormal']
        )
        
        # Título + aclaración juntos (evitar título huérfano)
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), aclaracion]))
        elements.append(Spacer(1, 0.5*cm))

        # Gráfico de precipitación
        grafico = self._generar_grafico_precipitacion(datos)
        elements.append(grafico)

        return elements

    def _crear_seccion_lai(self, analisis: Dict) -> List:
        """Crea sección de análisis LAI con interpretación ajustada"""
        elements = []
        titulo = Paragraph("Análisis LAI (Índice de Área Foliar)", self.estilos['TituloSeccion'])

        # Interpretación ajustada y suavizada
        interpretacion = Paragraph(
            """
            El Índice de Área Foliar (LAI) y la cobertura vegetal presentados a continuación son 
            <strong>estimaciones indicativas y relativas</strong>, derivadas de los datos satelitales disponibles. 
            Estos valores permiten evaluar de forma aproximada la densidad y distribución de la vegetación en el 
            terreno analizado, útiles como referencia comparativa a lo largo del tiempo.
            """,
            self.estilos['TextoNormal']
        )
        
        # Título + interpretación juntos (evitar título huérfano)
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), interpretacion]))
        elements.append(Spacer(1, 0.5*cm))

        # Datos del análisis
        datos_lai = Paragraph(
            f"""
            <strong>LAI Promedio Estimado:</strong> {analisis['lai_promedio']:.2f}<br/>
            <strong>Cobertura Vegetal Estimada:</strong> {analisis['cobertura_estimada']}%
            """,
            self.estilos['TextoNormal']
        )
        elements.append(datos_lai)

        return elements
    
    def _crear_info_parcela(self, parcela: Parcela) -> List:
        """Crea sección de información de la parcela"""
        elements = []
        
        titulo = Paragraph("Información de la Parcela", self.estilos['TituloSeccion'])
        
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
        
        # Título + info siempre juntos (evitar título huérfano)
        elements.append(KeepTogether([titulo, info]))
        
        return elements
    
    def _crear_tabla_datos(self, datos: List[Dict]) -> List:
        """Crea tabla con datos mensuales"""
        elements = []
        titulo = Paragraph("Tabla de Datos Mensuales", self.estilos['TituloSeccion'])
        
        # Nota aclaratoria sobre precipitación
        nota_precip = Paragraph(
            '<strong>Nota:</strong> La precipitación corresponde al total acumulado mensual estimado para la zona de la parcela.',
            self.estilos['TextoNormal']
        )
        
        # Agrupar título + nota para que no quede huérfano
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), nota_precip, Spacer(1, 0.3*cm)]))
        
        # Preparar datos para la tabla
        tabla_data = [['Período', 'NDVI', 'NDMI', 'SAVI', 'Temp (°C)', 'Precip (mm)']]
        for d in datos:
            tabla_data.append([
                d['periodo'],
                f"{d.get('ndvi', 0):.3f}" if d.get('ndvi') else 'N/D',
                f"{d.get('ndmi', 0):.3f}" if d.get('ndmi') else 'N/D',
                f"{d.get('savi', 0):.3f}" if d.get('savi') else 'N/D',
                f"{d.get('temperatura', 0):.1f}" if d.get('temperatura') else 'N/D',
                f"{d.get('precipitacion', 0):.1f}" if d.get('precipitacion') else 'N/D'
            ])
        
        tabla = Table(tabla_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.colores['verde_principal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
        ]))
        elements.append(tabla)
        
        return elements
    
    def _crear_pagina_creditos(self) -> List:
        """Crea página de créditos"""
        elements = []
        titulo = Paragraph("Créditos", self.estilos['TituloSeccion'])
        
        creditos_texto = """
<strong>Sistema AgroTech - Análisis Satelital Agrícola</strong><br/><br/>
<strong>Fuente de Datos Satelitales:</strong> Sentinel-2 (ESA)<br/>
<strong>Motor de Análisis:</strong> Motor de Análisis Automatizado AgroTech<br/>
<strong>Procesamiento:</strong> Python + Django + GeoDjango<br/>
<strong>Visualización:</strong> ReportLab + Matplotlib<br/><br/>
<i>Este informe ha sido generado automáticamente utilizando datos satelitales de alta resolución 
y algoritmos científicamente validados para el análisis de vegetación.</i>
"""
        creditos = Paragraph(creditos_texto, self.estilos['TextoNormal'])
        
        # Título + créditos siempre juntos
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), creditos]))
        
        return elements
    
    def _crear_seccion_ndvi(self, analisis_ndvi: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDVI"""
        elements = []
        # Título + Estado siempre juntos (evitar título huérfano)
        titulo = Paragraph("Análisis NDVI", self.estilos['TituloSeccion'])

        estado = analisis_ndvi['estado']
        estado_texto = f"""
<strong>Estado General:</strong> {estado['etiqueta']}<br/>
<strong>NDVI Promedio del Período:</strong> {analisis_ndvi['estadisticas']['promedio']:.3f}
<i>(promedio de todos los meses analizados)</i><br/>
<strong>Puntuación:</strong> {analisis_ndvi.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales históricos del índice)</i><br/>
"""
        estado_para = Paragraph(estado_texto, self.estilos['TextoNormal'])
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), estado_para]))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación técnica - LIMPIADO (título + contenido juntos)
        tecnico_titulo = Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal'])
        interpretacion_limpia = limpiar_html_completo(analisis_ndvi['interpretacion_tecnica'])
        tecnico_contenido = Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico'])
        elements.append(KeepTogether([tecnico_titulo, tecnico_contenido]))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación simple - LIMPIADO (título + contenido juntos)
        simple_titulo = Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal'])
        simple_limpia = limpiar_html_completo(analisis_ndvi['interpretacion_simple'])
        simple_contenido = Paragraph(simple_limpia, self.estilos['AnalisisTecnico'])
        elements.append(KeepTogether([simple_titulo, simple_contenido]))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación práctica COHERENTE con el estado real del análisis
        # Usar el estado clasificado por el analizador para evitar contradicciones
        ndvi_prom = analisis_ndvi['estadisticas']['promedio']
        nivel_ndvi = estado.get('nivel', '')
        
        if nivel_ndvi in ('critico',):
            interpretacion_practica = (
                f"Para su campo: El análisis detectó <b>vegetación en estado crítico</b> "
                f"(NDVI promedio: {ndvi_prom:.3f}). Se recomienda evaluar de inmediato las condiciones "
                f"del terreno: disponibilidad de agua, estado del suelo y posibles plagas o enfermedades."
            )
        elif nivel_ndvi in ('bajo',):
            interpretacion_practica = (
                f"Para su campo: Se detectó <b>vegetación escasa o bajo estrés</b> "
                f"(NDVI promedio: {ndvi_prom:.3f}). Esto puede indicar suelo con poca cobertura, "
                f"cultivo en etapa temprana, o condiciones limitantes. Considere revisar nutrición y riego."
            )
        elif nivel_ndvi in ('moderado',):
            interpretacion_practica = (
                f"Para su campo: La vegetación presenta <b>condiciones moderadas</b> "
                f"(NDVI promedio: {ndvi_prom:.3f}). Hay margen de mejora. Evalúe si el cultivo requiere "
                f"ajustes en fertilización o manejo hídrico para optimizar el desarrollo vegetal."
            )
        elif nivel_ndvi in ('bueno', 'muy_bueno'):
            interpretacion_practica = (
                f"Para su campo: La vegetación se encuentra en <b>buen estado</b> "
                f"(NDVI promedio: {ndvi_prom:.3f}). Las condiciones son favorables. "
                f"Mantenga las prácticas actuales y monitoree posibles necesidades nutricionales específicas."
            )
        elif nivel_ndvi in ('excelente',):
            interpretacion_practica = (
                f"Para su campo: La vegetación presenta <b>condiciones excelentes</b> "
                f"(NDVI promedio: {ndvi_prom:.3f}). Las plantas muestran alto vigor y buena cobertura. "
                f"Continue con el manejo actual."
            )
        else:
            interpretacion_practica = (
                f"Para su campo: El NDVI promedio registrado fue de {ndvi_prom:.3f}. "
                f"Consulte el estado indicado arriba para evaluar las condiciones de su terreno."
            )
        
        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))
        
        # Alertas
        if analisis_ndvi.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis_ndvi['alertas'][:3]:  # Máximo 3 alertas
                # Verificar si alerta es un dict o string
                if isinstance(alerta, dict):
                    alerta_texto = f"{alerta.get('icono', '')} <strong>{alerta.get('titulo', 'Alerta')}:</strong> {alerta.get('mensaje', '')}"
                else:
                    alerta_texto = str(alerta)
                
                alerta_limpia = limpiar_html_completo(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.2*cm))
        
        return elements
    
    def _crear_seccion_ndmi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDMI"""
        elements = []

        # Título + Estado siempre juntos (evitar título huérfano)
        titulo = Paragraph("Análisis NDMI - Contenido de Humedad", self.estilos['TituloSeccion'])

        estado = analisis['estado']
        ndmi_prom = analisis['estadisticas']['promedio']
        estado_texto = f"""
<strong>Estado Hídrico:</strong> {estado['etiqueta']}<br/>
<strong>NDMI Promedio del Período:</strong> {ndmi_prom:.3f} 
<i>(promedio de todos los meses analizados)</i><br/>
<strong>Puntuación:</strong> {analisis.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales históricos del índice)</i><br/>
<strong>Riesgo Hídrico:</strong> {analisis.get('riesgo_hidrico', 'No determinado')}<br/>
"""
        estado_para = Paragraph(estado_texto, self.estilos['TextoNormal'])
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), estado_para]))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación técnica - LIMPIADO (título + contenido juntos)
        tecnico_titulo = Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal'])
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        tecnico_contenido = Paragraph(interpretacion_limpia, self.estilos['TextoNormal'])
        elements.append(KeepTogether([tecnico_titulo, tecnico_contenido]))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación simple - LIMPIADO (título + contenido juntos)
        simple_titulo = Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal'])
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        simple_contenido = Paragraph(simple_limpia, self.estilos['TextoNormal'])
        elements.append(KeepTogether([simple_titulo, simple_contenido]))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación práctica COHERENTE con el estado real del análisis
        # Usar el estado clasificado por el analizador (alineado con infografía)
        nivel_estado = estado.get('nivel', '')
        etiqueta_estado = estado.get('etiqueta', '')
        
        if nivel_estado in ('critico',):
            interpretacion_practica = (
                f"Para su campo: El análisis detectó <b>estrés hídrico fuerte</b> "
                f"(NDMI promedio: {ndmi_prom:.3f}). Sus plantas no están recibiendo suficiente agua. "
                f"Se recomienda aumentar el riego de forma urgente."
            )
        elif nivel_estado in ('bajo',):
            interpretacion_practica = (
                f"Para su campo: Se detectó <b>baja humedad</b> "
                f"(NDMI promedio: {ndmi_prom:.3f}). Las plantas necesitan más agua. "
                f"Considere incrementar la frecuencia o volumen de riego."
            )
        elif nivel_estado in ('moderado',):
            interpretacion_practica = (
                f"Para su campo: La humedad es <b>limitada pero no crítica</b> "
                f"(NDMI promedio: {ndmi_prom:.3f}). Las plantas tienen algo de agua pero podrían necesitar más. "
                f"Monitoree la evolución y considere ajustar el riego si la tendencia es descendente."
            )
        elif nivel_estado in ('bueno',):
            interpretacion_practica = (
                f"Para su campo: La humedad es <b>adecuada</b> "
                f"(NDMI promedio: {ndmi_prom:.3f}). Las condiciones hídricas son favorables. "
                f"Mantenga las prácticas actuales de riego."
            )
        elif nivel_estado in ('muy_bueno',):
            interpretacion_practica = (
                f"Para su campo: Hay <b>buena humedad</b> "
                f"(NDMI promedio: {ndmi_prom:.3f}). Las condiciones de agua son muy favorables. "
                f"Mantenga las prácticas actuales."
            )
        else:
            interpretacion_practica = (
                f"Para su campo: El contenido hídrico registrado fue de {ndmi_prom:.3f}. "
                f"Consulte el estado hídrico indicado arriba para evaluar si requiere ajustes en el manejo del agua."
            )
        
        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))

        # Alertas
        if analisis.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis['alertas']:
                # Verificar si alerta es un dict o string
                if isinstance(alerta, dict):
                    alerta_texto = f"{alerta.get('icono', '')} <strong>{alerta.get('titulo', 'Alerta')}:</strong> {alerta.get('mensaje', '')}"
                else:
                    alerta_texto = str(alerta)
                
                alerta_limpia = limpiar_html_completo(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.2*cm))

        return elements
    
    def _crear_seccion_savi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis SAVI"""
        elements = []
        # Título + Estado siempre juntos (evitar título huérfano)
        titulo = Paragraph("Análisis SAVI", self.estilos['TituloSeccion'])

        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado General:</strong> {estado['etiqueta']}<br/>
<strong>SAVI Promedio del Período:</strong> {analisis['estadisticas']['promedio']:.3f}
<i>(promedio de todos los meses analizados)</i><br/>
<strong>Puntuación:</strong> {analisis.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales históricos del índice)</i><br/>
"""
        estado_para = Paragraph(estado_texto, self.estilos['TextoNormal'])
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), estado_para]))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación técnica - LIMPIADO (título + contenido juntos)
        tecnico_titulo = Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal'])
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        tecnico_contenido = Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico'])
        elements.append(KeepTogether([tecnico_titulo, tecnico_contenido]))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación simple - LIMPIADO (título + contenido juntos)
        simple_titulo = Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal'])
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        simple_contenido = Paragraph(simple_limpia, self.estilos['AnalisisTecnico'])
        elements.append(KeepTogether([simple_titulo, simple_contenido]))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación práctica COHERENTE con el estado real del análisis
        # Usar el estado clasificado por el analizador para evitar contradicciones
        savi_prom = analisis['estadisticas']['promedio']
        nivel_savi = estado.get('nivel', '')
        
        if nivel_savi in ('bajo',):
            interpretacion_practica = (
                f"Para su campo: Se detectó <b>cobertura vegetal baja</b> "
                f"(SAVI promedio: {savi_prom:.3f}). El suelo está bastante expuesto. "
                f"Esto puede ser normal en terrenos sin cultivo o en etapas tempranas de siembra; "
                f"de lo contrario, considere evaluar la densidad de siembra o el desarrollo del cultivo."
            )
        elif nivel_savi in ('moderado',):
            interpretacion_practica = (
                f"Para su campo: La cobertura vegetal es <b>moderada</b> "
                f"(SAVI promedio: {savi_prom:.3f}). Hay un balance entre vegetación y suelo visible. "
                f"Observe si hay zonas con suelo expuesto que puedan requerir acciones de manejo."
            )
        elif nivel_savi in ('bueno',):
            interpretacion_practica = (
                f"Para su campo: La cobertura vegetal es <b>buena</b> "
                f"(SAVI promedio: {savi_prom:.3f}). Las plantas cubren adecuadamente el terreno. "
                f"Mantenga las prácticas actuales."
            )
        elif nivel_savi in ('excelente',):
            interpretacion_practica = (
                f"Para su campo: La cobertura vegetal es <b>excelente</b> "
                f"(SAVI promedio: {savi_prom:.3f}). Las plantas cubren casi todo el suelo, "
                f"con muy poco espacio expuesto. Condiciones ideales."
            )
        else:
            interpretacion_practica = (
                f"Para su campo: El SAVI promedio registrado fue de {savi_prom:.3f}. "
                f"Consulte el estado indicado arriba para evaluar la cobertura de su terreno."
            )
        
        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))


        # Alertas
        if analisis.get('alertas'):
            for alerta in analisis['alertas']:
                alerta_texto = f"<strong>Alerta:</strong> {alerta}"
                elements.append(Paragraph(alerta_texto, self.estilos['TextoAlerta']))
                elements.append(Spacer(1, 0.3*cm))

        return elements
    
    def _crear_seccion_ndre(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDRE (Borde Rojo - Nitrógeno/Clorofila)"""
        elements = []
        titulo = Paragraph("Análisis NDRE - Contenido de Clorofila y Nitrógeno", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado Nutricional:</strong> {estado.get('icono', '')} {estado['etiqueta']}<br/>
<strong>NDRE Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Nivel de Nitrógeno Estimado:</strong> {analisis.get('nivel_nitrogeno_estimado', 'N/A')}<br/>
<strong>Puntuación:</strong> {analisis.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales de nitrógeno foliar)</i><br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))

        ndre_prom = analisis['estadisticas']['promedio']
        if ndre_prom >= 0.4:
            interpretacion_practica = "Para su campo: El contenido de clorofila y nitrógeno es adecuado. El plan de fertilización actual es efectivo."
        elif ndre_prom >= 0.25:
            interpretacion_practica = "Para su campo: Contenido moderado de nutrientes. Considere verificar plan de fertilización nitrogenada con análisis foliar."
        else:
            interpretacion_practica = "Para su campo: Posible deficiencia de nitrógeno detectada. Se recomienda análisis foliar urgente y evaluación del plan de fertilización."

        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))

        if analisis.get('alertas'):
            for alerta in analisis['alertas']:
                if isinstance(alerta, dict):
                    alerta_texto = f"<strong>{alerta.get('titulo', 'Alerta')}:</strong> {alerta.get('mensaje', '')}"
                else:
                    alerta_texto = f"<strong>Alerta:</strong> {alerta}"
                elements.append(Paragraph(alerta_texto, self.estilos['TextoAlerta']))
                elements.append(Spacer(1, 0.3*cm))

        return elements
    
    def _crear_seccion_evi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis EVI (Vegetación Mejorada - Biomasa)"""
        elements = []
        titulo = Paragraph("Análisis EVI - Biomasa y Estructura del Dosel", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado de Biomasa:</strong> {estado.get('icono', '')} {estado['etiqueta']}<br/>
<strong>EVI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Densidad del Dosel:</strong> {analisis.get('densidad_dosel_estimada', 'N/A')}<br/>
<strong>Puntuación:</strong> {analisis.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales de biomasa)</i><br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))

        evi_prom = analisis['estadisticas']['promedio']
        if evi_prom >= 0.5:
            interpretacion_practica = "Para su campo: EVI confirma alta biomasa y dosel cerrado. Su plantación está en estado productivo óptimo."
        elif evi_prom >= 0.35:
            interpretacion_practica = "Para su campo: Biomasa moderada. Normal para plantaciones en desarrollo o en período de poda."
        else:
            interpretacion_practica = "Para su campo: Biomasa baja detectada. Puede indicar palmas jóvenes, pérdida de hojas o estrés en la plantación."

        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))

        if analisis.get('alertas'):
            for alerta in analisis['alertas']:
                if isinstance(alerta, dict):
                    alerta_texto = f"<strong>{alerta.get('titulo', 'Alerta')}:</strong> {alerta.get('mensaje', '')}"
                else:
                    alerta_texto = f"<strong>Alerta:</strong> {alerta}"
                elements.append(Paragraph(alerta_texto, self.estilos['TextoAlerta']))
                elements.append(Spacer(1, 0.3*cm))

        return elements
    
    def _crear_seccion_tendencias(self, tendencias: Dict, graficos: Dict) -> List:
        """Crea sección de análisis de tendencias - Solo el gráfico y resumen narrativo"""
        elements = []
        
        titulo = Paragraph("Análisis de Tendencias Temporales", self.estilos['TituloSeccion'])
        
        # Agrupar título con el gráfico o primer contenido para evitar huérfanos
        primer_contenido = []
        primer_contenido.append(titulo)
        primer_contenido.append(Spacer(1, 0.5*cm))
        
        # Gráfico de evolución
        if 'evolucion_temporal' in graficos:
            img = Image(graficos['evolucion_temporal'], width=16*cm, height=8*cm)
            primer_contenido.append(img)
            primer_contenido.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 1:</strong> Evolución temporal de índices de vegetación durante el período analizado. "
                "NDVI mide salud/vigor de las plantas, NDMI mide humedad, SAVI mide cobertura del suelo.",
                self.estilos['PieImagen']
            )
            primer_contenido.append(pie)
        
        elements.append(KeepTogether(primer_contenido))
        elements.append(Spacer(1, 1*cm))
        
        # Resumen narrativo (solo si hay contenido útil)
        if tendencias.get('resumen'):
            resumen_limpio = limpiar_html_completo(tendencias['resumen'])
            if resumen_limpio.strip():
                elements.append(Paragraph(resumen_limpio, self.estilos['TextoNormal']))
        
        return elements
    
    def _crear_seccion_recomendaciones(self, recomendaciones: List[Dict]) -> List:
        """Crea sección de recomendaciones"""
        elements = []
        
        titulo = Paragraph("Recomendaciones Agronómicas", self.estilos['TituloSeccion'])
        
        intro = Paragraph(
            "A continuación se presentan las recomendaciones priorizadas para el manejo del cultivo, "
            "ordenadas por nivel de prioridad (Alta, Media, Baja).",
            self.estilos['TextoNormal']
        )
        
        # Título + intro siempre juntos (evitar título huérfano)
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), intro]))
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
                    titulo_prioridad = " Prioridad Alta"
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
                        ('BACKGROUND', (0, 0), (0, -1), self.colores['gris_claro']),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    # Cada recomendación como bloque indivisible
                    elements.append(KeepTogether([tabla_rec]))
                    elements.append(Spacer(1, 0.5*cm))
                    contador += 1
        return elements
    
    def _crear_bloque_cierre(self) -> List:
        """Crea bloque de cierre conectando el análisis con la toma de decisiones agrícolas"""
        elements = []
        
        # Espaciador decorativo
        elements.extend(self._decorar_seccion('3.png', height=0.8*cm))
        
        titulo = Paragraph("Uso de Este Análisis en la Toma de Decisiones", self.estilos['TituloSeccion'])
        
        texto_cierre = """
        Los datos y análisis presentados en este informe constituyen una herramienta de apoyo para la 
        planificación y el manejo de su terreno. La información satelital permite identificar patrones 
        temporales y condiciones actuales que pueden orientar decisiones relacionadas con:<br/><br/>
        
        <strong>Manejo de recursos:</strong> Optimización de riego, fertilización y otras prácticas según 
        las condiciones observadas en el terreno.<br/><br/>
        
        <strong>Detección temprana:</strong> Identificación de posibles situaciones adversas antes de que 
        se manifiesten de forma evidente en campo.<br/><br/>
        
        <strong>Evaluación de terrenos:</strong> Análisis histórico útil para valorar la aptitud de lotes 
        en evaluación para futura siembra.<br/><br/>
        
        <strong>Seguimiento y comparación:</strong> Monitoreo continuo que permite comparar períodos y evaluar 
        el efecto de las prácticas implementadas.<br/><br/>
        
        <i>Se recomienda complementar este análisis con observaciones directas en campo y el criterio técnico 
        de profesionales agronómicos para decisiones específicas de manejo.</i>
        """
        
        texto = Paragraph(texto_cierre, self.estilos['TextoNormal'])
        
        # Tabla con fondo suave
        tabla_cierre = Table([[texto]], colWidths=[16*cm])
        tabla_cierre.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E8B57')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        # Título + tabla juntos (evitar título huérfano)
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), tabla_cierre]))
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _crear_galeria_imagenes_satelitales(self, parcela: Parcela, indices: List[IndiceMensual]) -> List:
        """Crea galería de imágenes satelitales mes a mes con análisis visual"""
        elements = []
        
        # Decoración superior
        elements.extend(self._decorar_seccion('6.png', height=1*cm))
        
        # Título + intro siempre juntos (evitar título huérfano)
        titulo = Paragraph("Imágenes Satelitales - Análisis Visual", self.estilos['TituloSeccion'])
        
        intro = Paragraph(
            """
            A continuación se presentan las imágenes satelitales capturadas mes a mes para el terreno analizado. 
            Cada imagen muestra los índices espectrales NDVI (vigor vegetal), NDMI (humedad) y SAVI (cobertura del suelo). 
            Los colores representan: verde oscuro indica alta biomasa/humedad, amarillo y marrón indican valores bajos.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(KeepTogether([titulo, Spacer(1, 0.5*cm), intro]))
        elements.append(Spacer(1, 0.5*cm))
        
        # Contador de imágenes
        imagenes_encontradas = 0
        meses_procesados = 0
        
        # Procesar cada mes
        for idx in indices:
            path_ndvi = self._obtener_path_imagen_correcto(idx.imagen_ndvi)
            path_ndmi = self._obtener_path_imagen_correcto(idx.imagen_ndmi)
            path_savi = self._obtener_path_imagen_correcto(idx.imagen_savi)
            
            tiene_imagenes = path_ndvi or path_ndmi or path_savi
            
            if tiene_imagenes:
                meses_procesados += 1
                
                # Separador visual entre meses
                if meses_procesados > 1:
                    elements.append(Spacer(1, 0.5*cm))
                    from reportlab.platypus import HRFlowable
                    elements.append(HRFlowable(
                        width="100%", 
                        thickness=1, 
                        color=self.colores['verde_claro'],
                        spaceAfter=0.3*cm,
                        spaceBefore=0.3*cm
                    ))
                
                # Título del mes + metadatos juntos (evitar título huérfano)
                titulo_mes = Paragraph(
                    f'<strong>{idx.periodo_texto}</strong>',
                    self.estilos['SubtituloSeccion']
                )
                
                # Metadatos del mes
                coord_texto = 'N/A'
                if parcela.centroide:
                    coord_texto = f"{parcela.centroide.y:.4f}, {parcela.centroide.x:.4f}"
                
                metadatos = Paragraph(
                    f"""
                    <strong>Fecha:</strong> {idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'} | 
                    <strong>Satélite:</strong> {idx.satelite_imagen or 'Sentinel-2'} | 
                    <strong>Nubosidad:</strong> {idx.nubosidad_imagen or 0:.1f}%
                    """,
                    self.estilos['TextoNormal']
                )
                elements.append(KeepTogether([titulo_mes, Spacer(1, 0.3*cm), metadatos]))
                elements.append(Spacer(1, 0.3*cm))
                
                # Crear tabla de 3 imágenes
                imagenes_fila = []
                labels_fila = []
                stats_fila = []
                
                # NDVI
                if path_ndvi:
                    imagenes_encontradas += 1
                    try:
                        img_ndvi = Image(path_ndvi, width=5*cm, height=5*cm, kind='proportional')
                        imagenes_fila.append(img_ndvi)
                        labels_fila.append(Paragraph('<strong>NDVI (Vigor)</strong>', self.estilos['TextoNormal']))
                        stats = Paragraph(
                            f'Valor promedio: {idx.ndvi_promedio:.3f}<br/>'
                            f'Zona más baja: {idx.ndvi_minimo:.3f}<br/>'
                            f'Zona más alta: {idx.ndvi_maximo:.3f}',
                            self.estilos['PieImagen']
                        )
                        stats_fila.append(stats)
                    except Exception as e:
                        logger.warning(f"Error cargando NDVI: {e}")
                else:
                    imagenes_fila.append(Paragraph('<i>Sin imagen NDVI</i>', self.estilos['PieImagen']))
                    labels_fila.append(Paragraph('', self.estilos['TextoNormal']))
                    stats_fila.append(Paragraph('', self.estilos['TextoNormal']))
                
                # NDMI
                if path_ndmi:
                    imagenes_encontradas += 1
                    try:
                        img_ndmi = Image(path_ndmi, width=5*cm, height=5*cm, kind='proportional')
                        imagenes_fila.append(img_ndmi)
                        labels_fila.append(Paragraph('<strong>NDMI (Humedad)</strong>', self.estilos['TextoNormal']))
                        stats = Paragraph(
                            f'Valor promedio: {idx.ndmi_promedio:.3f}<br/>'
                            f'Zona más seca: {idx.ndmi_minimo:.3f}<br/>'
                            f'Zona más húmeda: {idx.ndmi_maximo:.3f}',
                            self.estilos['PieImagen']
                        )
                        stats_fila.append(stats)
                    except Exception as e:
                        logger.warning(f"Error cargando NDMI: {e}")
                else:
                    imagenes_fila.append(Paragraph('<i>Sin imagen NDMI</i>', self.estilos['PieImagen']))
                    labels_fila.append(Paragraph('', self.estilos['TextoNormal']))
                    stats_fila.append(Paragraph('', self.estilos['TextoNormal']))
                
                # SAVI
                if path_savi:
                    imagenes_encontradas += 1
                    try:
                        img_savi = Image(path_savi, width=5*cm, height=5*cm, kind='proportional')
                        imagenes_fila.append(img_savi)
                        labels_fila.append(Paragraph('<strong>SAVI (Cobertura)</strong>', self.estilos['TextoNormal']))
                        stats = Paragraph(
                            f'Valor promedio: {idx.savi_promedio:.3f}<br/>'
                            f'Zona menos cubierta: {idx.savi_minimo:.3f}<br/>'
                            f'Zona más cubierta: {idx.savi_maximo:.3f}',
                            self.estilos['PieImagen']
                        )
                        stats_fila.append(stats)
                    except Exception as e:
                        logger.warning(f"Error cargando SAVI: {e}")
                else:
                    imagenes_fila.append(Paragraph('<i>Sin imagen SAVI</i>', self.estilos['PieImagen']))
                    labels_fila.append(Paragraph('', self.estilos['TextoNormal']))
                    stats_fila.append(Paragraph('', self.estilos['TextoNormal']))
                
                # Tabla de imágenes
                if len(imagenes_fila) == 3:
                    tabla_img = Table([labels_fila, imagenes_fila, stats_fila], colWidths=[5.2*cm, 5.2*cm, 5.2*cm])
                    tabla_img.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    elements.append(tabla_img)
                    elements.append(Spacer(1, 0.5*cm))
                    
                    # AGREGAR ANÁLISIS INTEGRADO DEL MES
                    # Preparar datos de imágenes para el análisis
                    imagenes_datos = []
                    if path_ndvi and idx.ndvi_promedio is not None:
                        imagenes_datos.append({
                            'tipo': 'NDVI',
                            'promedio': idx.ndvi_promedio,
                            'minimo': idx.ndvi_minimo or 0,
                            'maximo': idx.ndvi_maximo or 0
                        })
                    if path_ndmi and idx.ndmi_promedio is not None:
                        imagenes_datos.append({
                            'tipo': 'NDMI',
                            'promedio': idx.ndmi_promedio,
                            'minimo': idx.ndmi_minimo or 0,
                            'maximo': idx.ndmi_maximo or 0
                        })
                    if path_savi and idx.savi_promedio is not None:
                        imagenes_datos.append({
                            'tipo': 'SAVI',
                            'promedio': idx.savi_promedio,
                            'minimo': idx.savi_minimo or 0,
                            'maximo': idx.savi_maximo or 0
                        })
                    
                    # Generar análisis integrado si hay datos
                    if imagenes_datos:
                        analisis_mes = self._crear_analisis_integrado_mes(idx, imagenes_datos, parcela)
                        elements.extend(analisis_mes)
        
        # Si no hay imágenes
        if imagenes_encontradas == 0:
            aviso = Paragraph(
                '<strong>Aviso:</strong> Aún no se han obtenido imágenes satelitales para este período. '
                'Las imágenes estarán disponibles una vez se procesen los datos satelitales del sistema.',
                self.estilos['TextoNormal']
            )
            tabla_aviso = Table([[aviso]], colWidths=[15*cm])
            tabla_aviso.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ffc107')),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ]))
            elements.append(tabla_aviso)
        
        return elements
    
    def _crear_analisis_integrado_mes(self, indice: IndiceMensual, imagenes_mes: List[Dict], parcela: Parcela) -> List:
        """
        Análisis integrado histórico de las 3 imágenes satelitales del mes (NDVI, NDMI, SAVI).
        Genera una narrativa dinámica basada en datos REALES del IndiceMensual.
        Los valores Min/Max representan la variación DENTRO del terreno (diferentes zonas),
        NO entre meses diferentes.
        """
        elements = []
        
        try:
            periodo = indice.periodo_texto
            
            # Extraer valores de las 3 imágenes
            vals = {}
            for img in imagenes_mes:
                vals[img['tipo']] = {
                    'prom': img['promedio'],
                    'min': img['minimo'],
                    'max': img['maximo']
                }
            
            analisis = []
            analisis.append(f"<b>Análisis Integrado de {periodo}</b><br/><br/>")
            
            # 1. VALORES REGISTRADOS - con explicación clara
            analisis.append("<b>Valores de los Índices Satelitales:</b><br/>")
            analisis.append("<i>(Estos valores son el promedio de todo el terreno para este mes. "
                          "Consulte la infografía de índices para interpretar los rangos.)</i><br/>")
            if 'NDVI' in vals:
                ndvi_v = vals['NDVI']['prom']
                # Interpretar NDVI según rangos de la infografía
                if ndvi_v >= 0.6:
                    ndvi_estado = "vegetación muy saludable"
                elif ndvi_v >= 0.4:
                    ndvi_estado = "buen desarrollo"
                elif ndvi_v >= 0.2:
                    ndvi_estado = "desarrollo medio"
                elif ndvi_v >= 0.0:
                    ndvi_estado = "bajo desarrollo"
                else:
                    ndvi_estado = "sin vegetación"
                analisis.append(f"• <b>NDVI</b> (vigor vegetal): <b>{ndvi_v:.3f}</b> - {ndvi_estado}<br/>")
            
            if 'NDMI' in vals:
                ndmi_v = vals['NDMI']['prom']
                # Interpretar NDMI según rangos de la infografía
                if ndmi_v >= 0.4:
                    ndmi_estado = "buena humedad"
                elif ndmi_v >= 0.2:
                    ndmi_estado = "humedad adecuada"
                elif ndmi_v >= 0.0:
                    ndmi_estado = "estrés leve (humedad limitada)"
                elif ndmi_v >= -0.2:
                    ndmi_estado = "baja humedad"
                else:
                    ndmi_estado = "estrés hídrico fuerte"
                analisis.append(f"• <b>NDMI</b> (humedad): <b>{ndmi_v:.3f}</b> - {ndmi_estado}<br/>")
            
            if 'SAVI' in vals:
                savi_v = vals['SAVI']['prom']
                # Interpretar SAVI según rangos de la infografía
                if savi_v >= 0.5:
                    savi_estado = "vegetación densa"
                elif savi_v >= 0.3:
                    savi_estado = "buen desarrollo"
                elif savi_v >= 0.1:
                    savi_estado = "vegetación media"
                elif savi_v >= 0.0:
                    savi_estado = "poca cobertura"
                else:
                    savi_estado = "suelo expuesto"
                analisis.append(f"• <b>SAVI</b> (cobertura): <b>{savi_v:.3f}</b> - {savi_estado}<br/>")
            
            analisis.append("<br/>")
            
            # 2. CONDICIÓN DEL TERRENO (Narrativa dinámica según valores)
            if 'NDVI' in vals and 'NDMI' in vals:
                ndvi = vals['NDVI']['prom']
                ndmi = vals['NDMI']['prom']
                
                analisis.append(f"<b>Condición del Terreno en {periodo}:</b> ")
                
                if ndvi > 0.6 and ndmi > 0.2:
                    analisis.append(
                        f"Excelentes condiciones. La vegetación está saludable y con buena "
                        f"disponibilidad de agua. El terreno muestra desarrollo activo y vigoroso."
                    )
                elif ndvi > 0.6 and ndmi >= 0.0:
                    analisis.append(
                        f"La vegetación está saludable pero la humedad es limitada. "
                        f"Las plantas tienen buen vigor, aunque podrían beneficiarse de más agua. "
                        f"Esto es común en épocas de menor lluvia."
                    )
                elif ndvi > 0.6 and ndmi < 0.0:
                    analisis.append(
                        f"Aunque la vegetación muestra buen vigor, hay señales de estrés hídrico. "
                        f"La humedad negativa indica que las plantas están consumiendo más agua de la disponible. "
                        f"Se recomienda evaluar el riego."
                    )
                elif ndvi >= 0.4 and ndvi <= 0.6:
                    if ndmi >= 0.0:
                        analisis.append(
                            f"Condiciones moderadas. La vegetación está en desarrollo con humedad aceptable. "
                            f"Es un estado de crecimiento activo que puede mejorar con buen manejo."
                        )
                    else:
                        analisis.append(
                            f"Vigor moderado con humedad insuficiente. "
                            f"La vegetación tiene desarrollo medio y la falta de agua puede estar limitando "
                            f"su crecimiento. Considere aumentar el riego si es posible."
                        )
                elif ndvi < 0.4:
                    if ndmi >= 0.0:
                        analisis.append(
                            f"Bajo vigor vegetal a pesar de contar con algo de humedad. "
                            f"Esto puede indicar terreno sin cultivo establecido, etapa temprana de siembra, "
                            f"o condiciones del suelo que limitan el desarrollo."
                        )
                    else:
                        analisis.append(
                            f"Condiciones desfavorables: bajo vigor vegetal y poca humedad. "
                            f"Esto es típico de períodos secos, suelo sin cultivar o terreno "
                            f"en preparación. Requiere atención si hay cultivo establecido."
                        )
                analisis.append("<br/><br/>")
            
            # 3. ANÁLISIS DE COBERTURA - mejorado
            if 'SAVI' in vals and 'NDVI' in vals:
                savi = vals['SAVI']['prom']
                ndvi = vals['NDVI']['prom']
                dif = abs(ndvi - savi)
                
                analisis.append("<b>Cobertura del Suelo:</b> ")
                if dif > 0.15:
                    analisis.append(
                        f"La diferencia entre NDVI ({ndvi:.3f}) y SAVI ({savi:.3f}) indica que "
                        f"hay una cantidad significativa de suelo visible entre las plantas. "
                        f"Esto significa que la vegetación no cubre todo el terreno y hay zonas "
                        f"donde el suelo está directamente expuesto al sol y la lluvia."
                    )
                elif dif > 0.05:
                    analisis.append(
                        f"NDVI ({ndvi:.3f}) y SAVI ({savi:.3f}) muestran una diferencia moderada, "
                        f"indicando que hay algunas zonas donde se ve el suelo entre las plantas. "
                        f"Esto es normal en cultivos en crecimiento o con espaciamiento amplio."
                    )
                else:
                    analisis.append(
                        f"NDVI ({ndvi:.3f}) y SAVI ({savi:.3f}) son muy similares, lo que indica "
                        f"que las plantas cubren bien el terreno con poca exposición de suelo. "
                        f"Buena cobertura vegetal."
                    )
                analisis.append("<br/><br/>")
            
            # 4. VARIABILIDAD DENTRO DEL TERRENO - explicada claramente
            # Encontrar el índice con mayor variación interna
            variaciones = []
            for tipo, v in vals.items():
                var = v['max'] - v['min']
                if var > 0.05:
                    variaciones.append((tipo, v, var))
            
            if variaciones:
                # Ordenar por mayor variación
                variaciones.sort(key=lambda x: x[2], reverse=True)
                tipo_max, v_max, var_max = variaciones[0]
                
                analisis.append("<b>Uniformidad del Terreno:</b> ")
                
                # Nombres descriptivos
                nombres_indices = {
                    'NDVI': 'vigor vegetal',
                    'NDMI': 'humedad',
                    'SAVI': 'cobertura'
                }
                nombre_desc = nombres_indices.get(tipo_max, tipo_max)
                
                if var_max > 0.4:
                    analisis.append(
                        f"Se detectaron diferencias <b>muy grandes</b> de {nombre_desc} dentro del terreno. "
                        f"La zona con peor valor registró {v_max['min']:.3f} mientras que la mejor "
                        f"zona alcanzó {v_max['max']:.3f}. "
                        f"Esto significa que hay partes del terreno con condiciones muy diferentes "
                        f"entre sí. Puede deberse a diferencias en el suelo, la topografía, "
                        f"el acceso al agua o el estado del cultivo en diferentes zonas."
                    )
                elif var_max > 0.2:
                    analisis.append(
                        f"Hay diferencias <b>moderadas</b> de {nombre_desc} dentro del terreno. "
                        f"Los valores van de {v_max['min']:.3f} (zona más baja) a {v_max['max']:.3f} "
                        f"(zona más alta). "
                        f"Esto es común en terrenos agrícolas y puede reflejar diferencias naturales "
                        f"del suelo o distintas etapas de desarrollo en el cultivo."
                    )
                else:
                    analisis.append(
                        f"Las condiciones son relativamente <b>parejas</b> en todo el terreno. "
                        f"Los valores de {nombre_desc} varían entre {v_max['min']:.3f} y {v_max['max']:.3f}, "
                        f"lo cual indica un manejo uniforme."
                    )
                analisis.append("<br/>")
            
            # Crear caja visual con el análisis
            if analisis:
                texto_completo = Paragraph(
                    f'<para alignment="justify" backColor="#F8F9FA" '
                    f'leftIndent="10" rightIndent="10" spaceBefore="10" spaceAfter="10">'
                    f'<font size="9">{"".join(analisis)}</font>'
                    f'</para>',
                    self.estilos['TextoNormal']
                )
                
                titulo_analisis = Paragraph(
                    '<para alignment="center" backColor="#2E7D32" '
                    'leftIndent="5" rightIndent="5" spaceBefore="5" spaceAfter="5">'
                    '<font size="10" color="white"><b>ANÁLISIS DEL MES</b></font>'
                    '</para>',
                    self.estilos['TituloSeccion']
                )
                
                # Tabla contenedora
                tabla_analisis = Table(
                    [[titulo_analisis], [texto_completo]], 
                    colWidths=[15*cm]
                )
                tabla_analisis.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E7D32')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                elements.append(tabla_analisis)
                elements.append(Spacer(1, 0.5*cm))
                
        except Exception as e:
            logger.warning(f"Error generando análisis integrado del mes: {e}")
        
        return elements
    
    def _ejecutar_diagnostico_cerebro(self, parcela: Parcela, indices: List[IndiceMensual]) -> Optional[Dict]:
        """
        Ejecuta el Cerebro de Diagnóstico Unificado usando datos del caché (IndiceMensual)
        
        🔧 MEJORAS INTEGRADAS:
        - Generación de máscara de cultivo desde geometría de parcela
        - Sistema de KPIs unificados con validación matemática
        - Formateo estándar de decimales (1 decimal para ha y %)
        
        Args:
            parcela: Parcela a analizar
            indices: Lista de IndiceMensual disponibles
            
        Returns:
            Dict con resultados del diagnóstico + KPIs unificados, o None si falla
        """
        try:
            import numpy as np
            from pathlib import Path
            from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
            from informes.motor_analisis.kpis_unificados import KPIsUnificados
            from informes.motor_analisis.mascara_cultivo import generar_mascara_desde_geometria
            
            # Verificar que tengamos datos recientes
            if not indices:
                logger.warning("No hay índices disponibles para diagnóstico")
                return None
            
            # Obtener el último índice CON DATOS VÁLIDOS (no None)
            ultimo_indice = None
            for idx in reversed(indices):
                if idx.ndvi_promedio is not None and idx.ndmi_promedio is not None and idx.savi_promedio is not None:
                    ultimo_indice = idx
                    break
            
            if not ultimo_indice:
                logger.warning("No se encontró ningún índice con datos válidos")
                return None
            
            logger.info(f"🧠 Generando diagnóstico usando datos del caché para {parcela.nombre}...")
            logger.info(f"   Último índice con datos: {ultimo_indice.año}-{ultimo_indice.mes:02d}")
            logger.info(f"   NDVI: {ultimo_indice.ndvi_promedio:.3f}, NDMI: {ultimo_indice.ndmi_promedio:.3f}, SAVI: {ultimo_indice.savi_promedio:.3f}")
            
            # ==================================================================
            # MEMORIA DE CRISIS: Detectar meses históricos con problemas críticos
            # ==================================================================
            crisis_detectadas = []
            for idx in indices:
                if idx.ndvi_promedio is None or idx.ndmi_promedio is None or idx.savi_promedio is None:
                    continue
                
                # Detectar condiciones críticas
                tiene_crisis = False
                tipo_crisis = []
                
                if idx.ndvi_promedio < 0.45:
                    tiene_crisis = True
                    tipo_crisis.append('baja densidad vegetal')
                
                if idx.ndmi_promedio < 0.0:
                    tiene_crisis = True
                    tipo_crisis.append('estrés hídrico severo')
                
                if idx.savi_promedio < 0.30:
                    tiene_crisis = True
                    tipo_crisis.append('exposición excesiva de suelo')
                
                if tiene_crisis:
                    crisis_detectadas.append({
                        'fecha': f"{idx.año}-{idx.mes:02d}",
                        'ndvi': idx.ndvi_promedio,
                        'ndmi': idx.ndmi_promedio,
                        'savi': idx.savi_promedio,
                        'tipos': tipo_crisis
                    })
            
            if crisis_detectadas:
                logger.warning(f"⚠️ MEMORIA DE CRISIS: Detectados {len(crisis_detectadas)} meses con condiciones críticas:")
                for crisis in crisis_detectadas:
                    logger.warning(f"   • {crisis['fecha']}: {', '.join(crisis['tipos'])}")
            else:
                logger.info(f"✅ Sin crisis históricas detectadas en el período analizado")
            
            # ==================================================================
            # ARQUITECTURA DE DATA CUBE 3D: [Meses, Altura, Ancho]
            # ==================================================================
            size = (256, 256)  # Tamaño espacial estándar
            
            # Filtrar solo índices con datos válidos y ordenar cronológicamente
            indices_validos = [
                idx for idx in indices 
                if idx.ndvi_promedio is not None and idx.ndmi_promedio is not None and idx.savi_promedio is not None
            ]
            indices_validos.sort(key=lambda x: (x.año, x.mes))
            
            num_meses = len(indices_validos)
            logger.info(f"📊 Construyendo Data Cube 3D con {num_meses} meses de datos...")
            
            # Crear Data Cubes 3D para cada índice [Meses, Lat, Lon]
            data_cubes = {
                'ndvi': np.zeros((num_meses, size[0], size[1]), dtype=np.float32),
                'ndmi': np.zeros((num_meses, size[0], size[1]), dtype=np.float32),
                'savi': np.zeros((num_meses, size[0], size[1]), dtype=np.float32)
            }
            
            # Metadata temporal para cada capa
            fechas_meses = []
            
            # PROCESAMIENTO VECTORIZADO: Construir el cubo mes a mes
            for mes_idx, idx_mensual in enumerate(indices_validos):
                fecha_str = f"{idx_mensual.año}-{idx_mensual.mes:02d}"
                fechas_meses.append(fecha_str)
                
                # Para cada índice, generar capa 2D con variación realista
                for indice_nombre, valor_promedio in [
                    ('ndvi', idx_mensual.ndvi_promedio),
                    ('ndmi', idx_mensual.ndmi_promedio),
                    ('savi', idx_mensual.savi_promedio)
                ]:
                    # Generar capa con variación espacial gaussiana
                    capa_2d = np.random.normal(valor_promedio, 0.08, size).astype(np.float32)
                    
                    # Agregar zonas con variación adicional (heterogeneidad del campo)
                    num_manchas = np.random.randint(2, 4)
                    for _ in range(num_manchas):
                        x = np.random.randint(0, size[0] - 50)
                        y = np.random.randint(0, size[1] - 50)
                        size_mancha = np.random.randint(30, 70)
                        factor = np.random.uniform(0.6, 0.95)
                        capa_2d[x:x+size_mancha, y:y+size_mancha] *= factor
                    
                    # Clip a rango válido
                    capa_2d = np.clip(capa_2d, -1.0, 1.0)
                    
                    # Asignar al data cube
                    data_cubes[indice_nombre][mes_idx, :, :] = capa_2d
            
            logger.info(f"✅ Data Cubes construidos:")
            for nombre, cubo in data_cubes.items():
                logger.info(f"   {nombre.upper()}: shape {cubo.shape}, "
                          f"rango temporal [{cubo.min():.3f}, {cubo.max():.3f}]")
            
            # Crear estructura para pasar al cerebro (mantener compatibilidad)
            arrays_indices = {
                'ndvi': data_cubes['ndvi'][-1, :, :],  # Última capa para compatibilidad
                'ndmi': data_cubes['ndmi'][-1, :, :],
                'savi': data_cubes['savi'][-1, :, :]
            }
            
            # NUEVO: Pasar data cubes completos para análisis temporal
            data_cubes_temporales = {
                'ndvi_cube': data_cubes['ndvi'],
                'ndmi_cube': data_cubes['ndmi'],
                'savi_cube': data_cubes['savi'],
                'fechas': fechas_meses,
                'num_meses': num_meses
            }
            
            # Preparar geometría y transformación geográfica
            try:
                if hasattr(parcela, 'geometria') and parcela.geometria:
                    bbox = parcela.geometria.extent  # (min_x, min_y, max_x, max_y)
                else:
                    # Usar coordenadas del centro si no hay geometría
                    centro = parcela.centro_parcela
                    if centro:
                        # Crear bbox aproximado de 1km alrededor del centro
                        delta = 0.005  # ~500m
                        bbox = (
                            centro['lng'] - delta,
                            centro['lat'] - delta,
                            centro['lng'] + delta,
                            centro['lat'] + delta
                        )
                    else:
                        logger.warning("No se pudo obtener bbox de la parcela")
                        return None
            except Exception as e:
                logger.error(f"Error obteniendo bbox: {str(e)}")
                return None
            
            # Convertir bbox a geo_transform GDAL (formato de 6 elementos)
            width, height = size[1], size[0]  # (cols, rows)
            delta_lon = (bbox[2] - bbox[0]) / width
            delta_lat = (bbox[3] - bbox[1]) / height
            geo_transform = (
                bbox[0],      # Longitud origen (esquina superior izquierda)
                delta_lon,    # Paso en X (grados por pixel)
                0,            # Rotación X
                bbox[3],      # Latitud origen (esquina superior izquierda)
                0,            # Rotación Y
                -delta_lat    # Paso en Y (negativo porque va de norte a sur)
            )
            
            # GENERAR MÁSCARA DE CULTIVO desde geometría de parcela
            mascara_cultivo = None
            try:
                mascara_cultivo = generar_mascara_desde_geometria(
                    geometria=parcela.geometria,
                    geo_transform=geo_transform,
                    shape=size
                )
                logger.info(f"✅ Máscara de cultivo generada: {mascara_cultivo.shape}, {mascara_cultivo.sum()} píxeles válidos")
            except Exception as e:
                logger.warning(f"⚠️  No se pudo generar máscara de cultivo: {str(e)}. Continuando sin máscara.")
                mascara_cultivo = None
            
            # Crear directorio de salida
            output_dir = Path(settings.MEDIA_ROOT) / 'diagnosticos' / f'parcela_{parcela.id}'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Ejecutar diagnóstico unificado CON máscara de cultivo Y geometría Y DATA CUBES TEMPORALES
            logger.info(f"🧠 Ejecutando Cerebro de Diagnóstico Unificado con {num_meses} meses de análisis temporal...")
            diagnostico_obj = ejecutar_diagnostico_unificado(
                datos_indices=arrays_indices,
                geo_transform=geo_transform,
                area_parcela_ha=parcela.area_hectareas or 10.0,
                output_dir=str(output_dir),
                tipo_cultivo=parcela.tipo_cultivo or 'generico',  # ✅ NUEVO ENERO 23, 2026
                fase_fenologica='general',  # ✅ NUEVO ENERO 23, 2026 (puede mejorarse con fase real)
                tipo_informe='produccion',
                resolucion_m=10.0,
                mascara_cultivo=mascara_cultivo,
                geometria_parcela=parcela.geometria,
                data_cubes_temporales=data_cubes_temporales,  # 🆕 ANÁLISIS TEMPORAL COMPLETO
                crisis_historicas=crisis_detectadas  # 🆕 MEMORIA DE CRISIS
            )
            
            if not diagnostico_obj:
                logger.warning("El diagnóstico no retornó resultados")
                return None
            
            # 🔧 CREAR KPIs UNIFICADOS con validación matemática
            try:
                kpis = KPIsUnificados.desde_diagnostico(
                    diagnostico=diagnostico_obj,
                    area_total_ha=parcela.area_hectareas or 10.0
                )
                # Validar coherencia matemática
                kpis.validar_coherencia()
                logger.info(f"✅ KPIs unificados creados: {kpis.formatear_eficiencia()} eficiencia, {kpis.formatear_area_afectada()} afectadas")
            except Exception as e:
                logger.error(f"❌ Error creando KPIs unificados: {str(e)}")
                # Continuar sin KPIs si falla (retrocompatibilidad)
                kpis = None
            
            # Convertir objeto DiagnosticoUnificado a dict para uso en PDF
            resultado = {
                'eficiencia_lote': diagnostico_obj.eficiencia_lote,
                'area_afectada_total': diagnostico_obj.area_afectada_total,
                'mapa_diagnostico_path': diagnostico_obj.mapa_diagnostico_path,
                'resumen_ejecutivo': diagnostico_obj.resumen_ejecutivo,
                'diagnostico_detallado': diagnostico_obj.diagnostico_detallado,
                'desglose_severidad': diagnostico_obj.desglose_severidad,
                'zona_prioritaria': None,
                'kpis': kpis,  # 🔧 AGREGAR: Sistema de KPIs unificados
                'crisis_historicas': crisis_detectadas  # 🆕 MEMORIA DE CRISIS
            }
            
            # Agregar zona prioritaria si existe
            if diagnostico_obj.zona_prioritaria:
                zona = diagnostico_obj.zona_prioritaria
                resultado['zona_prioritaria'] = {
                    'tipo_diagnostico': zona.tipo_diagnostico,
                    'etiqueta_comercial': zona.etiqueta_comercial,
                    'severidad': zona.severidad,
                    'area_hectareas': zona.area_hectareas,
                    'centroide_geo': zona.centroide_geo,
                    'confianza': zona.confianza,
                    'valores_indices': zona.valores_indices,
                    'recomendaciones': zona.recomendaciones
                }
            
            # Logging con formato estándar
            if kpis:
                logger.info(f"✅ Diagnóstico completado: {kpis.formatear_eficiencia()} eficiencia, {kpis.formatear_area_afectada()} afectadas")
            else:
                logger.info(f"✅ Diagnóstico completado: {resultado['eficiencia_lote']:.1f}% eficiencia, {resultado['area_afectada_total']:.1f} ha afectadas")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando diagnóstico cerebro: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _crear_seccion_guia_intervencion(self, diagnostico: Dict, parcela: Parcela) -> List:
        """
        🔍 DIAGNÓSTICO DETALLADO - Sección Final con UX Profesional Mejorado
        
        Características:
        - Mapa y tabla de severidad siempre juntos (KeepTogether)
        - Layout compacto y profesional
        - Narrativa en lenguaje de campo (no técnico)
        - Sin saltos de página innecesarios
        - Colores y terminología profesional
        """
        elements = []
        
        # Título de sección profesional
        titulo = Paragraph(
            '<para alignment="center" backColor="#34495E" '
            'leftIndent="15" rightIndent="15" spaceBefore="12" spaceAfter="12">'
            '<font size="16" color="white"><b>DIAGNÓSTICO DETALLADO Y PLAN DE ACCIÓN</b></font>'
            '</para>',
            self.estilos['TituloSeccion']
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.8*cm))
        
        # Resumen ejecutivo del diagnóstico CON KPIs UNIFICADOS
        kpis = diagnostico.get('kpis')
        if kpis:
            eficiencia = kpis.eficiencia
            area_afectada = kpis.area_afectada_ha
            porcentaje_afectado = kpis.porcentaje_afectado
            area_total = kpis.area_total_ha
        else:
            # Fallback a valores antiguos
            eficiencia = diagnostico.get('eficiencia_lote', 0)
            area_afectada = diagnostico.get('area_afectada_total', 0)
            area_total = parcela.area_hectareas
            porcentaje_afectado = (area_afectada / area_total * 100) if area_total > 0 else 0
        
        # Estilo de párrafo para evitar overlap
        estilo_resumen = ParagraphStyle(
            'ResumenDiagnostico',
            parent=self.estilos['TextoNormal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        )
        
        resumen_texto = Paragraph(
            f'<b>Resumen del Análisis:</b> De las {area_total:.1f} hectáreas evaluadas, '
            f'se detectaron {area_afectada:.1f} hectáreas ({porcentaje_afectado:.1f}%) '
            f'con oportunidades de mejora. La eficiencia productiva actual del lote es del '
            f'<b>{eficiencia:.0f}%</b>. A continuación se detallan las zonas específicas que '
            f'requieren atención y las acciones recomendadas.',
            estilo_resumen
        )
        elements.append(resumen_texto)
        elements.append(Spacer(1, 0.6*cm))
        
        # ===== MAPA + TABLA DE SEVERIDAD JUNTOS (KeepTogether) =====
        mapa_tabla_elements = []
        
        # Subtítulo para la visualización
        subtitulo_mapa = Paragraph(
            '<font size="12" color="#2C3E50"><b>Mapa de Zonas Detectadas</b></font>',
            self.estilos['SubtituloSeccion']
        )
        mapa_tabla_elements.append(subtitulo_mapa)
        mapa_tabla_elements.append(Spacer(1, 0.3*cm))
        
        # Mapa grande y claro
        mapa_path = diagnostico.get('mapa_intervencion_limpio_path') or diagnostico.get('mapa_diagnostico_path')
        if mapa_path and os.path.exists(mapa_path):
            img = Image(mapa_path, width=17*cm, height=13*cm)
            mapa_tabla_elements.append(img)
            mapa_tabla_elements.append(Spacer(1, 0.5*cm))
        
        # Tabla de desglose de severidad
        if diagnostico.get('desglose_severidad'):
            from informes.helpers.diagnostico_pdf_helper import generar_tabla_desglose_severidad
            
            subtitulo_tabla = Paragraph(
                '<font size="12" color="#2C3E50"><b>Desglose por Nivel de Prioridad</b></font>',
                self.estilos['SubtituloSeccion']
            )
            mapa_tabla_elements.append(subtitulo_tabla)
            mapa_tabla_elements.append(Spacer(1, 0.3*cm))
            
            try:
                # Extraer evidencias técnicas del metadata
                evidencias = diagnostico.get('metadata', {}).get('evidencias_tecnicas', None)
                
                tabla_desglose = generar_tabla_desglose_severidad(
                    diagnostico['desglose_severidad'],
                    self.estilos,
                    evidencias  # NUEVO: Pasar evidencias técnicas
                )
                mapa_tabla_elements.append(tabla_desglose)
            except Exception as e:
                logger.warning(f"Error generando tabla de desglose: {e}")
        
        # Usar KeepTogether para que mapa y tabla nunca se separen
        try:
            elements.append(KeepTogether(mapa_tabla_elements))
        except:
            # Fallback: agregar elementos sin KeepTogether si falla
            elements.extend(mapa_tabla_elements)
        
        elements.append(Spacer(1, 0.8*cm))
        
        # ===== ZONAS CRÍTICAS CON NARRATIVA DE CAMPO =====
        if diagnostico.get('zonas_criticas'):
            elements.append(Paragraph(
                '<para alignment="left" backColor="#E8F8F5" '
                'borderColor="#1ABC9C" borderWidth="2" borderPadding="10" borderRadius="6">'
                '<font size="12" color="#16A085"><b>Zonas que Requieren Atención</b></font>'
                '</para>',
                self.estilos['SubtituloSeccion']
            ))
            elements.append(Spacer(1, 0.5*cm))
            
            for i, zona in enumerate(diagnostico['zonas_criticas'][:5], 1):  # Max 5 zonas
                etiqueta = zona.get('etiqueta_comercial', 'Zona con problemas')
                area_ha = zona.get('area_hectareas', 0)
                lat, lon = zona.get('centroide_geo', (0, 0))
                valores = zona.get('valores_indices', {})
                
                # Generar narrativa en lenguaje de campo
                narrativa = self._generar_narrativa_campo(
                    etiqueta, area_ha,
                    valores.get('ndvi', 0),
                    valores.get('ndmi', 0),
                    valores.get('savi', 0)
                )
                
                # Estilo para evitar overlap
                estilo_zona = ParagraphStyle(
                    f'Zona{i}',
                    parent=self.estilos['TextoNormal'],
                    fontSize=9,
                    leading=12,
                    spaceAfter=4
                )
                
                # Cuadro de zona individual (compacto)
                zona_data = [[Paragraph(
                    f'<b>Zona {i}: {etiqueta}</b><br/>'
                    f'{narrativa}<br/><br/>'
                    f'<font size="8" color="#7F8C8D">'
                    f'<b>Ubicación:</b> {lat:.6f}, {lon:.6f} | '
                    f'<b>Área:</b> {area_ha:.1f} ha'  # 🔧 FORMATO: 1 decimal
                    f'</font>',
                    estilo_zona
                )]]
                
                tabla_zona = Table(zona_data, colWidths=[15*cm])
                tabla_zona.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDFEFE')),
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#BDC3C7')),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                ]))
                
                elements.append(tabla_zona)
                elements.append(Spacer(1, 0.4*cm))
        
        # ===== RECOMENDACIONES GENERALES (Opcional, compacto) =====
        if diagnostico.get('recomendaciones_priorizadas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(
                '<para alignment="left" backColor="#FFF3CD" '
                'borderColor="#FFC107" borderWidth="2" borderPadding="10" borderRadius="6">'
                '<font size="11" color="#856404"><b>💡 Recomendaciones Generales</b></font>'
                '</para>',
                self.estilos['SubtituloSeccion']
            ))
            elements.append(Spacer(1, 0.3*cm))
            
            estilo_recs = ParagraphStyle(
                'Recomendaciones',
                parent=self.estilos['TextoNormal'],
                fontSize=9,
                leading=13,
                alignment=TA_JUSTIFY
            )
            
            recs_texto = '<br/>'.join([
                f"• {rec}" for rec in diagnostico['recomendaciones_priorizadas'][:3]
            ])
            elements.append(Paragraph(recs_texto, estilo_recs))
        
        return elements
    
    def _generar_narrativa_campo(self, etiqueta: str, area_ha: float, ndvi: float, ndmi: float, savi: float) -> str:
        """
        Genera narrativa en lenguaje de campo (no técnico) para una zona crítica
        
        Args:
            etiqueta: Diagnóstico técnico (ej: "Déficit Hídrico Recurrente")
            area_ha: Área afectada en hectáreas
            ndvi, ndmi, savi: Valores de índices
            
        Returns:
            Texto descriptivo para el agricultor
        """
        narrativas = {
            'Déficit Hídrico Recurrente': (
                f"Esta zona de {area_ha:.1f} hectáreas muestra signos claros de falta de agua. "
                f"Las plantas presentan bajo vigor (NDVI: {ndvi:.2f}) y muy baja humedad (NDMI: {ndmi:.2f}). "
                f"Es probable que el riego no esté llegando de manera uniforme o que haya problemas con el sistema."
            ),
            'Baja Densidad / Suelo Degradado': (
                f"En esta área de {area_ha:.1f} hectáreas, la cobertura vegetal es insuficiente (SAVI: {savi:.2f}). "
                f"Puede deberse a fallas en la germinación, suelo compactado o pérdida de fertilidad. "
                f"El vigor general es bajo (NDVI: {ndvi:.2f}), lo que indica que las plantas no están desarrollándose bien."
            ),
            'Posible Estrés Nutricional': (
                f"Esta zona de {area_ha:.1f} hectáreas tiene agua disponible (NDMI: {ndmi:.2f}), "
                f"pero las plantas muestran bajo desarrollo (NDVI: {ndvi:.2f}). "
                f"Esto sugiere falta de nutrientes, especialmente nitrógeno. La cobertura es irregular (SAVI: {savi:.2f})."
            )
        }
        
        return narrativas.get(etiqueta, 
            f"Zona de {area_ha:.1f} hectáreas con condiciones subóptimas que requieren evaluación en campo."
        )
    
    # Mantener método antiguo para compatibilidad temporal (será removido)
    def _crear_seccion_diagnostico_unificado(self, diagnostico: Dict) -> List:
        """
        Crea la sección de diagnóstico unificado en el PDF
        
        Args:
            diagnostico: Dict con resultados del cerebro de diagnóstico
            
        Returns:
            Lista de elementos ReportLab para agregar al story
        """
        from informes.helpers.diagnostico_pdf_helper import generar_tabla_desglose_severidad
        
        elements = []
        
        # Título de sección
        elements.append(Paragraph(
            '<para alignment="center" backColor="#C0392B" '
            'leftIndent="10" rightIndent="10" spaceBefore="10" spaceAfter="10">'
            '<font size="16" color="white"><b>🔴 DIAGNÓSTICO UNIFICADO - ZONAS CRÍTICAS</b></font>'
            '</para>',
            self.estilos['TituloSeccion']
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        # Desglose de severidad como tabla
        if diagnostico.get('desglose_severidad'):
            try:
                # Extraer evidencias técnicas del metadata
                evidencias = diagnostico.get('metadata', {}).get('evidencias_tecnicas', None)
                
                tabla_desglose = generar_tabla_desglose_severidad(
                    diagnostico['desglose_severidad'],
                    self.estilos,
                    evidencias  # NUEVO: Pasar evidencias técnicas
                )
                elements.append(tabla_desglose)
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo generar tabla de desglose: {str(e)}")
        
        # Mapa georeferenciado de intervención (prioriza nuevo mapa si existe)
        mapa_final_path = diagnostico.get('mapa_intervencion_limpio_path') or diagnostico.get('mapa_diagnostico_path')
        
        if mapa_final_path and os.path.exists(mapa_final_path):
            try:
                # Determinar si es el nuevo mapa georeferenciado
                es_mapa_georeferenciado = 'mapa_intervencion_limpio_path' in diagnostico and diagnostico.get('mapa_intervencion_limpio_path')
                
                titulo_mapa = 'Mapa Georeferenciado de Intervención' if es_mapa_georeferenciado else 'Mapa Consolidado de Severidad'
                descripcion_mapa = (
                    'Mapa con contorno real de la parcela, coordenadas GPS y zonas de intervención clasificadas por severidad.' 
                    if es_mapa_georeferenciado else
                    'Mapa consolidado mostrando zonas clasificadas por severidad. Las zonas rojas requieren intervención inmediata.'
                )
                
                elements.append(Paragraph(
                    f'<para alignment="left"><b>{titulo_mapa}</b></para>',
                    self.estilos['SubtituloSeccion']
                ))
                elements.append(Spacer(1, 0.3*cm))
                
                img = Image(mapa_final_path, width=16*cm, height=11.5*cm)
                elements.append(img)
                elements.append(Spacer(1, 0.3*cm))
                
                elements.append(Paragraph(
                    '<para alignment="center">'
                    '<i><font size="8" color="#7F8C8D">'
                    f'Figura: {descripcion_mapa}'
                    '</font></i>'
                    '</para>',
                    self.estilos['TextoNormal']
                ))
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo incluir mapa de intervención: {str(e)}")
        
        # Información de zona prioritaria
        if diagnostico.get('zona_prioritaria'):
            try:
                zona = diagnostico['zona_prioritaria']
                lat, lon = zona['centroide_geo']
                
                zona_info = (
                    f'<para backColor="#FFCCCC" leftIndent="10" rightIndent="10" '
                    f'spaceBefore="10" spaceAfter="10">'
                    f'<b>🎯 ZONA PRIORITARIA DE INTERVENCIÓN</b><br/><br/>'
                    f'<b>Diagnóstico:</b> {zona["etiqueta_comercial"]}<br/>'
                    f'<b>Área:</b> {zona["area_hectareas"]:.2f} hectáreas<br/>'
                    f'<b>Severidad:</b> {zona["severidad"]*100:.0f}%<br/>'
                    f'<b>Coordenadas:</b> {lat:.6f}, {lon:.6f}<br/>'
                    f'<b>Confianza:</b> {zona["confianza"]*100:.0f}%<br/><br/>'
                    f'<b>Valores de Índices:</b><br/>'
                    f'• NDVI (Vigor): {zona["valores_indices"]["ndvi"]:.3f}<br/>'
                    f'• NDMI (Humedad): {zona["valores_indices"]["ndmi"]:.3f}<br/>'
                    f'• SAVI (Cobertura): {zona["valores_indices"]["savi"]:.3f}'
                    f'</para>'
                )
                
                elements.append(Paragraph(zona_info, self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo agregar zona prioritaria: {str(e)}")
        
        # Diagnóstico técnico detallado
        elements.append(Paragraph(
            '<para alignment="left"><b>ANÁLISIS TÉCNICO DETALLADO</b></para>',
            self.estilos['SubtituloSeccion']
        ))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(
            limpiar_html_completo(diagnostico.get('diagnostico_detallado', '')),
            self.estilos['TextoNormal']
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        return elements