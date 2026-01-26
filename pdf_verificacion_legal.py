"""
Extensión del generador de PDF para incluir verificación legal opcional
========================================================================

Este módulo agrega una sección completa de verificación legal al PDF
cuando la parcela tiene activada la opción incluir_verificacion_legal.

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from io import BytesIO
import os
from pathlib import Path


def agregar_seccion_verificacion_legal(story, resultado_verificacion, styles, parcela=None, verificador=None):
    """
    Agrega la sección completa de verificación legal al PDF
    
    Args:
        story: Lista de elementos del PDF (ReportLab story)
        resultado_verificacion: Objeto ResultadoVerificacion
        styles: Estilos del documento
        parcela: Objeto Parcela (opcional, para generar mapa)
        verificador: Objeto VerificadorRestriccionesLegales (NUEVO, para obtener fuentes hídricas)
    """
    
    # ===== TÍTULO DE LA SECCIÓN =====
    story.append(PageBreak())
    
    titulo_legal = Paragraph(
        "VERIFICACIÓN DE RESTRICCIONES LEGALES Y AMBIENTALES",
        styles['Heading1']
    )
    story.append(titulo_legal)
    story.append(Spacer(1, 0.2*inch))
    
    # ===== RESUMEN EJECUTIVO =====
    story.append(Paragraph("Resumen Ejecutivo", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    # NUEVO: Verificar si la verificación está incompleta
    advertencias = resultado_verificacion.advertencias
    verificacion_incompleta = any('no cargad' in adv.lower() for adv in advertencias) if advertencias else False
    
    # Obtener niveles de confianza
    niveles_confianza = resultado_verificacion.niveles_confianza if hasattr(resultado_verificacion, 'niveles_confianza') else None
    
    # Determinar color según cumplimiento
    if verificacion_incompleta:
        # VERIFICACIÓN INCOMPLETA - No concluir cumplimiento
        color_cumplimiento = '#fff3cd'  # Amarillo advertencia
        icono_cumplimiento = '⚠️'
        texto_cumplimiento = 'ANÁLISIS PRELIMINAR - DATOS INCOMPLETOS'
    elif resultado_verificacion.cumple_normativa:
        color_cumplimiento = '#d4edda'  # Verde claro
        icono_cumplimiento = '✅'
        texto_cumplimiento = 'SIN RIESGOS DETECTADOS (preliminar)'
    else:
        color_cumplimiento = '#fff3cd'  # Amarillo (NO rojo - es preliminar)
        icono_cumplimiento = '⚠️'
        texto_cumplimiento = f'RIESGO LEGAL POTENCIAL ({len(resultado_verificacion.restricciones_encontradas)} restricciones detectadas)'
    
    # NUEVO: Manejar área_cultivable como estructura o valor legacy
    if isinstance(resultado_verificacion.area_cultivable_ha, dict):
        # Nueva estructura
        area_cultivable_info = resultado_verificacion.area_cultivable_ha
        if area_cultivable_info['determinable']:
            texto_area_cultivable = f"{area_cultivable_info['valor_ha']:.2f} ha (preliminar)"
        else:
            texto_area_cultivable = "NO DETERMINABLE (datos incompletos)"
    else:
        # Valor legacy (compatibilidad)
        if verificacion_incompleta:
            texto_area_cultivable = "NO DETERMINABLE (datos incompletos)"
        else:
            texto_area_cultivable = f"{resultado_verificacion.area_cultivable_ha:.2f} ha (preliminar)"
    
    # Tabla de resumen
    datos_resumen = [
        ['Concepto', 'Valor'],
        ['Estado del Análisis', f'{icono_cumplimiento} {texto_cumplimiento}'],
        ['Área Total Registrada', f'{resultado_verificacion.area_total_ha:.2f} ha'],
        ['Área Cultivable Estimada', texto_area_cultivable],
        ['Área con Posible Afectación', f'{resultado_verificacion.area_restringida_ha:.2f} ha ({resultado_verificacion.porcentaje_restringido:.1f}%)'],
        ['Fecha del Análisis', resultado_verificacion.fecha_verificacion[:10]],
    ]
    
    tabla_resumen = Table(datos_resumen, colWidths=[3*inch, 3.5*inch])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(color_cumplimiento)),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#155724' if resultado_verificacion.cumple_normativa else '#721c24')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(tabla_resumen)
    story.append(Spacer(1, 0.3*inch))
    
    # NUEVO: Disclaimer si verificación incompleta
    if verificacion_incompleta:
        disclaimer_incompleto = """
        <b>⚠️ ADVERTENCIA IMPORTANTE:</b> Esta verificación está <b>INCOMPLETA</b> debido a que 
        no se pudieron cargar todas las capas geográficas oficiales necesarias. Los resultados 
        mostrados son <b>PARCIALES</b> y <b>NO PUEDEN</b> usarse para certificar cumplimiento 
        normativo total. Se recomienda:<br/><br/>
        1. Descargar manualmente los datos faltantes de fuentes oficiales<br/>
        2. Re-ejecutar la verificación con datos completos<br/>
        3. Consultar con la CAR regional para confirmación oficial<br/><br/>
        <b>Este informe NO debe usarse para decisiones legales o financieras críticas.</b>
        """
        
        style_advertencia = ParagraphStyle(
            'Advertencia',
            parent=styles['BodyText'],
            backColor=colors.HexColor('#fff3cd'),
            borderColor=colors.HexColor('#ffc107'),
            borderWidth=2,
            borderPadding=15,
            textColor=colors.HexColor('#856404'),
            fontSize=10
        )
        
        story.append(Paragraph(disclaimer_incompleto, style_advertencia))
        story.append(Spacer(1, 0.3*inch))
    
    # ===== MAPA DE RESTRICCIONES (NUEVO) =====
    if parcela and parcela.geometria:
        try:
            from generador_mapa_restricciones_legales import generar_mapa_restricciones_legales
            from datetime import datetime
            
            # Generar mapa
            temp_dir = Path('media/temp')
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # NUEVO: Preparar metadata y fuentes hídricas
            fuentes_hidricas_gdf = None
            metadata_fuente = None
            
            if verificador and hasattr(verificador, 'red_hidrica_cercana') and verificador.red_hidrica_cercana is not None:
                fuentes_hidricas_gdf = verificador.red_hidrica_cercana
                
                # Crear metadata
                metadata_fuente = {
                    'fuente': 'Datos oficiales gobierno Colombia',
                    'tipo_dato': 'Red hídrica',
                    'fecha': datetime.now().strftime('%d/%m/%Y'),
                    'autoridad': 'IGAC/IDEAM',
                    'precision': '±10m',
                    'num_elementos_cercanos': len(fuentes_hidricas_gdf)
                }
                
                # Detectar si son polígonos (datos incorrectos)
                tipos_geom = fuentes_hidricas_gdf.geometry.geom_type.unique()
                if any(t in ['Polygon', 'MultiPolygon'] for t in tipos_geom):
                    metadata_fuente['tipo_dato'] = 'Zonificación hidrográfica (⚠️ NO red de drenaje)'
                    metadata_fuente['fuente'] = 'datos.gov.co - Zonificación hidrográfica'
            
            mapa_path = generar_mapa_restricciones_legales(
                geometria_parcela=parcela.geometria,
                restricciones=resultado_verificacion.restricciones_encontradas,
                verificacion_completa={
                    'area_total_ha': resultado_verificacion.area_total_ha,
                    'area_cultivable_ha': resultado_verificacion.area_cultivable_ha,
                    'area_restringida_ha': resultado_verificacion.area_restringida_ha,
                    'cumple_normativa': resultado_verificacion.cumple_normativa
                },
                output_dir=temp_dir,
                parcela_nombre=parcela.nombre,
                fuentes_hidricas_gdf=fuentes_hidricas_gdf,  # NUEVO
                metadata_fuente=metadata_fuente  # NUEVO
            )
            
            if mapa_path and os.path.exists(mapa_path):
                # Agregar título del mapa
                story.append(Paragraph("Mapa de Restricciones Detectadas", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                # Insertar imagen del mapa
                img = Image(str(mapa_path), width=6.5*inch, height=4.88*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
                
                # Leyenda del mapa
                texto_mapa = """
                <i>El mapa muestra el polígono de la parcela (verde) y las restricciones 
                detectadas superpuestas. Las coordenadas GPS en las esquinas permiten 
                ubicar las zonas restringidas en campo con GPS o aplicaciones móviles.</i>
                """
                story.append(Paragraph(texto_mapa, styles['BodyText']))
                story.append(Spacer(1, 0.3*inch))
        except Exception as e:
            print(f"⚠️ No se pudo generar mapa de restricciones: {e}")
            # Continuar sin mapa
    
    # ===== DETALLE DE RESTRICCIONES =====
    if resultado_verificacion.restricciones_encontradas:
        story.append(Paragraph("Restricciones Identificadas", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Texto explicativo
        texto_intro = """
        La siguiente tabla detalla las restricciones legales y ambientales identificadas 
        en la parcela según la normativa colombiana vigente. Estas restricciones deben 
        ser respetadas para el cumplimiento de la legislación ambiental y para evitar 
        sanciones administrativas y económicas.
        """
        story.append(Paragraph(texto_intro, styles['BodyText']))
        story.append(Spacer(1, 0.15*inch))
        
        # Agrupar restricciones por tipo
        restricciones_por_tipo = {}
        for rest in resultado_verificacion.restricciones_encontradas:
            tipo = rest['tipo']
            if tipo not in restricciones_por_tipo:
                restricciones_por_tipo[tipo] = []
            restricciones_por_tipo[tipo].append(rest)
        
        # Mostrar cada grupo de restricciones
        for tipo, restricciones in restricciones_por_tipo.items():
            # Subtítulo del tipo
            tipo_titulo = tipo.replace('_', ' ').title()
            story.append(Paragraph(f"• {tipo_titulo}", styles['Heading3']))
            story.append(Spacer(1, 0.05*inch))
            
            # Tabla de restricciones del tipo
            datos_tabla = [['#', 'Descripción', 'Distancia', 'Área Afectada', 'Normativa']]  # ACTUALIZADO
            
            for i, rest in enumerate(restricciones, 1):
                nombre = rest.get('nombre', 'Sin nombre')
                area = f"{rest['area_afectada_ha']:.4f} ha"
                normativa = rest.get('normativa', 'N/A')
                severidad = rest.get('severidad', 'MEDIA')
                
                # NUEVO: Información adicional
                distancia_m = rest.get('distancia_real_m', None)
                tipo_geom = rest.get('tipo_geometria', None)
                longitud_m = rest.get('longitud_cauce_m', None)
                
                # Construir descripción detallada
                descripcion = nombre
                if 'retiro_minimo_m' in rest:
                    descripcion += f"\nRetiro: {rest['retiro_minimo_m']}m"
                if tipo_geom:
                    tipo_esp = {
                        'LineString': 'Línea',
                        'MultiLineString': 'Multi-línea',
                        'Polygon': '⚠️ Polígono',
                        'MultiPolygon': '⚠️ Multi-polígono'
                    }.get(tipo_geom, tipo_geom)
                    descripcion += f"\nTipo: {tipo_esp}"
                if longitud_m:
                    descripcion += f"\nLongitud: {longitud_m:.0f}m"
                
                # Distancia
                if distancia_m is not None:
                    if distancia_m == 0:
                        dist_texto = "0m\n(Intersecta)"
                    else:
                        dist_texto = f"{distancia_m:.1f}m"
                else:
                    dist_texto = "N/A"
                
                datos_tabla.append([
                    str(i),
                    descripcion,  # ACTUALIZADO: Más detallado
                    dist_texto,  # NUEVO
                    area,
                    normativa  # Removido severidad, agregado distancia
                ])
            
            tabla_restricciones = Table(
                datos_tabla,
                colWidths=[0.3*inch, 2.5*inch, 0.8*inch, 1.0*inch, 1.8*inch]  # AJUSTADO
            )
            
            tabla_restricciones.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#495057')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(tabla_restricciones)
            story.append(Spacer(1, 0.2*inch))
    
    else:
        # Sin restricciones
        story.append(Paragraph("Restricciones Identificadas", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        texto_sin_rest = """
        <b>✅ EXCELENTE:</b> No se identificaron restricciones legales ni ambientales 
        en esta parcela según la verificación realizada con las capas geográficas oficiales 
        disponibles (RUNAP, ANT, IDEAM, IGAC). La totalidad del área registrada puede 
        ser utilizada para actividades agrícolas productivas.
        """
        
        # Crear estilo con fondo verde
        style_exito = ParagraphStyle(
            'Exito',
            parent=styles['BodyText'],
            backColor=colors.HexColor('#d4edda'),
            borderColor=colors.HexColor('#c3e6cb'),
            borderWidth=1,
            borderPadding=10,
            textColor=colors.HexColor('#155724')
        )
        
        story.append(Paragraph(texto_sin_rest, style_exito))
        story.append(Spacer(1, 0.2*inch))
    
    # ===== MARCO LEGAL =====
    story.append(Paragraph("Marco Legal y Normativo", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    texto_marco = """
    Esta verificación se basa en la siguiente normativa ambiental colombiana vigente:
    <br/><br/>
    <b>• Decreto 2811 de 1974 (Código de Recursos Naturales):</b> Establece la protección 
    de áreas de especial importancia ecológica.<br/>
    <b>• Decreto 1541 de 1978 (Artículo 83):</b> Define las zonas de protección de cauces 
    y nacimientos de agua. Retiros mínimos de 30-100 metros según el tipo de fuente hídrica.<br/>
    <b>• Ley 99 de 1993:</b> Crea el Sistema Nacional Ambiental (SINA) y define áreas 
    protegidas bajo jurisdicción de las CAR.<br/>
    <b>• Ley 1930 de 2018:</b> Protección y delimitación de páramos.<br/>
    <b>• Decreto 2164 de 1995:</b> Protección de territorios de resguardos indígenas.<br/>
    <br/>
    <b>Sanciones por incumplimiento:</b> Multas de hasta 5.000 salarios mínimos mensuales 
    legales vigentes, cierre temporal o definitivo de la actividad, y responsabilidad penal 
    según la gravedad de la afectación ambiental.
    """
    
    story.append(Paragraph(texto_marco, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    # ===== FUENTES DE DATOS =====
    story.append(Paragraph("Fuentes de Datos Geográficos", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    texto_fuentes = """
    Esta verificación utiliza exclusivamente datos geográficos oficiales del gobierno colombiano:
    <br/><br/>
    <b>• RUNAP (Registro Único Nacional de Áreas Protegidas):</b> Parques Nacionales Naturales 
    y otras áreas protegidas del SINAP.<br/>
    <b>• ANT (Agencia Nacional de Tierras):</b> Límites oficiales de resguardos indígenas.<br/>
    <b>• IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales):</b> Delimitación 
    de páramos y red hidrográfica.<br/>
    <b>• IGAC (Instituto Geográfico Agustín Codazzi):</b> Red hidrográfica nacional detallada.<br/>
    <br/>
    <i>Nota: Esta verificación está sujeta a la disponibilidad y actualización de las fuentes 
    de datos oficiales. Se recomienda consultar con la autoridad ambiental regional (CAR) 
    para confirmación final antes de ejecutar proyectos de inversión.</i>
    """
    
    story.append(Paragraph(texto_fuentes, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    # ===== NIVELES DE CONFIANZA (NUEVO) =====
    if niveles_confianza:
        story.append(Paragraph("Niveles de Confianza de los Datos", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        texto_intro_confianza = """
        La calidad y confiabilidad de este análisis depende de la disponibilidad y tipo 
        de datos geográficos utilizados. A continuación se detallan los niveles de confianza 
        de cada capa analizada:
        """
        story.append(Paragraph(texto_intro_confianza, styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))
        
        # Crear tabla de niveles de confianza
        datos_confianza = [['Capa Geográfica', 'Estado', 'Tipo de Dato', 'Confianza', 'Observaciones']]
        
        mapeo_nombres = {
            'red_hidrica': 'Red Hídrica',
            'areas_protegidas': 'Áreas Protegidas (RUNAP)',
            'resguardos_indigenas': 'Resguardos Indígenas',
            'paramos': 'Páramos'
        }
        
        for capa_key, datos in niveles_confianza.items():
            nombre_capa = mapeo_nombres.get(capa_key, capa_key)
            estado = '✅ Cargada' if datos['cargada'] else '❌ No cargada'
            tipo_dato = datos.get('tipo_dato', 'N/A') if datos['tipo_dato'] else 'N/A'
            confianza = datos['confianza']
            razon = datos['razon']
            
            # Color según confianza
            color_conf = {
                'Alta': '🟢',
                'Media': '🟡',
                'Baja': '🟠',
                'Nula': '🔴'
            }.get(confianza, '')
            
            datos_confianza.append([
                nombre_capa,
                estado,
                tipo_dato,
                f'{color_conf} {confianza}',
                razon
            ])
        
        tabla_confianza = Table(
            datos_confianza,
            colWidths=[1.5*inch, 1.0*inch, 1.3*inch, 1.0*inch, 2.2*inch]
        )
        
        tabla_confianza.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(tabla_confianza)
        story.append(Spacer(1, 0.15*inch))
        
        # Nota importante sobre confianza
        nota_confianza = """
        <b>📌 Importante:</b> Las conclusiones de este análisis solo aplican a las capas 
        con nivel de confianza <b>Media</b> o <b>Alta</b>. Las capas con confianza Baja o Nula 
        requieren datos adicionales para generar conclusiones definitivas.
        """
        
        style_nota = ParagraphStyle(
            'NotaConfianza',
            parent=styles['BodyText'],
            backColor=colors.HexColor('#e7f3ff'),
            borderColor=colors.HexColor('#0056b3'),
            borderWidth=1,
            borderPadding=10,
            textColor=colors.HexColor('#004085'),
            fontSize=9
        )
        
        story.append(Paragraph(nota_confianza, style_nota))
        story.append(Spacer(1, 0.2*inch))
    
    # ===== METODOLOGÍA Y ALCANCE (NUEVO) =====
    story.append(Paragraph("Metodología y Alcance del Análisis", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    texto_metodologia = """
    <b>Naturaleza del informe:</b><br/>
    Este documento es un <b>análisis preliminar de riesgo legal y ambiental</b>, NO una 
    certificación, licencia o autorización. Su propósito es:<br/><br/>
    • Identificar alertas tempranas de posibles restricciones legales<br/>
    • Servir como filtro de riesgo previo a trámites oficiales<br/>
    • Facilitar la toma de decisiones informadas sobre inversiones<br/>
    • Ahorrar tiempo y recursos al identificar incompatibilidades obvias<br/><br/>
    
    <b>Este análisis NO sustituye:</b><br/>
    • Conceptos técnicos de la Corporación Autónoma Regional (CAR)<br/>
    • Permisos ambientales oficiales<br/>
    • Estudios de impacto ambiental<br/>
    • Certificaciones de uso del suelo<br/>
    • Asesoría legal especializada<br/><br/>
    
    <b>Limitaciones técnicas:</b><br/>
    • Los retiros hídricos son estimaciones preliminares (30-100m según tipo de fuente)<br/>
    • La clasificación automática de fuentes requiere validación CAR<br/>
    • Los porcentajes de afectación son aproximados según datos disponibles<br/>
    • Nuevas regulaciones o delimitaciones pueden no estar reflejadas<br/><br/>
    
    <b>⚖️ Uso recomendado:</b> Este informe debe usarse como herramienta de análisis 
    preliminar. Para decisiones legales, financieras o de inversión significativas, 
    se requiere validación oficial de la autoridad ambiental competente.
    """
    
    style_metodologia = ParagraphStyle(
        'Metodologia',
        parent=styles['BodyText'],
        fontSize=9,
        leading=11
    )
    
    story.append(Paragraph(texto_metodologia, style_metodologia))
    story.append(Spacer(1, 0.2*inch))
    
    # ===== ADVERTENCIAS =====
    if resultado_verificacion.advertencias:
        story.append(Paragraph("Advertencias", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        for adv in resultado_verificacion.advertencias:
            bullet = f"⚠️  {adv}"
            story.append(Paragraph(bullet, styles['BodyText']))
            story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # ===== RECOMENDACIONES =====
    story.append(Paragraph("Recomendaciones", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    if verificacion_incompleta:
        # NUEVO: Recomendaciones cuando la verificación está incompleta
        texto_recomendaciones = """
        <b>1. PRIORITARIO - Completar Verificación:</b> Se requiere obtener las capas 
        geográficas faltantes de fuentes oficiales (IGAC, IDEAM, ANT) para realizar un 
        análisis completo.<br/><br/>
        <b>2. Datos de Red Hídrica:</b> Si los datos actuales son de "zonificación hidrográfica", 
        es necesario descargar la red de drenaje lineal (LineStrings) del IGAC para cálculos 
        precisos de retiros.<br/><br/>
        <b>3. No Tomar Decisiones Definitivas:</b> NO basar decisiones de inversión o financieras 
        críticas en este análisis parcial. Completar verificación primero.<br/><br/>
        <b>4. Consulta CAR:</b> Para seguridad jurídica, solicitar concepto técnico de la 
        Corporación Autónoma Regional competente antes de ejecutar proyectos.
        """
    elif resultado_verificacion.cumple_normativa:
        texto_recomendaciones = """
        <b>1. Validación CAR:</b> Aunque no se detectaron riesgos en este análisis preliminar, 
        se recomienda obtener certificación oficial de la Corporación Autónoma Regional para 
        proyectos de inversión significativa.<br/><br/>
        <b>2. Monitoreo Periódico:</b> Las delimitaciones de áreas protegidas y páramos pueden 
        actualizarse. Se sugiere verificación anual.<br/><br/>
        <b>3. Buenas Prácticas Ambientales:</b> Implementar prácticas agrícolas sostenibles 
        que protejan fuentes hídricas cercanas como medida preventiva.<br/><br/>
        <b>4. Documentación:</b> Mantener respaldo de este análisis como evidencia de debida 
        diligencia ambiental.
        """
    else:
        # Manejar area_cultivable como estructura o valor
        if isinstance(resultado_verificacion.area_cultivable_ha, dict):
            area_cult_valor = resultado_verificacion.area_cultivable_ha.get('valor_ha', 0)
        else:
            area_cult_valor = resultado_verificacion.area_cultivable_ha
        
        texto_recomendaciones = """
        <b>1. ALERTA - Posible Afectación Detectada:</b> Se identificaron {0} restricciones 
        potenciales que podrían afectar {1:.2f} ha ({2:.1f}% del predio).<br/><br/>
        <b>2. Validación Urgente con CAR:</b> Se recomienda consultar con la Corporación Autónoma 
        Regional competente para validar estos hallazgos preliminares y obtener retiros oficiales.<br/><br/>
        <b>3. Análisis de Alternativas:</b> Evaluar con asesoría técnica si es posible ajustar 
        diseño del cultivo para respetar retiros preliminares identificados.<br/><br/>
        <b>4. No Proceder Sin Validación:</b> NO implementar decisiones definitivas basadas 
        únicamente en este análisis preliminar. Requiere confirmación oficial.<br/><br/>
        <b>⚠️ Precaución Financiera:</b> El incumplimiento de restricciones ambientales puede 
        afectar solicitudes de crédito y cobertura de seguros.
        """.format(
            len(resultado_verificacion.restricciones_encontradas),
            resultado_verificacion.area_restringida_ha,
            resultado_verificacion.porcentaje_restringido
        )
    
    story.append(Paragraph(texto_recomendaciones, styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))
    
    # ===== PIE DE SECCIÓN =====
    texto_pie = """
    <i>Este <b>análisis preliminar de riesgo legal y ambiental</b> es un servicio adicional opcional de 
    AgroTech Histórico basado en datos geográficos oficiales disponibles. NO constituye certificación legal, 
    licencia ambiental ni concepto técnico oficial. Su propósito es servir como <b>filtro de riesgo y alerta 
    temprana</b>. Para decisiones legales, financieras o de inversión significativas, se requiere validación 
    de la autoridad ambiental competente (CAR).</i>
    """
    
    style_pie = ParagraphStyle(
        'Pie',
        parent=styles['BodyText'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(texto_pie, style_pie))


def generar_mapa_restricciones(resultado_verificacion, parcela_geometria, output_path):
    """
    Genera un mapa visual mostrando las restricciones (FUTURO)
    
    Por ahora retorna None. En el futuro generará mapa con matplotlib/folium
    
    Args:
        resultado_verificacion: ResultadoVerificacion
        parcela_geometria: Geometría de la parcela
        output_path: Ruta donde guardar el mapa
    
    Returns:
        Path al mapa generado o None
    """
    # TODO: Implementar generación de mapa con matplotlib/folium
    # Mostrar parcela, restricciones, buffers, etc.
    return None
