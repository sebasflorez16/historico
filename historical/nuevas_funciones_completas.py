# NUEVAS FUNCIONES PARA GENERADOR_PDF.PY
# Este archivo contiene las funciones que se deben agregar

# Ya agregada: _agrupar_meses_en_bloques

FUNCION_NARRATIVA = '''
    def _crear_seccion_narrativa_lote(self, bloques_info: Dict, parcela: Parcela, analisis_completo: Dict) -> List:
        """
        Crea la sección narrativa '¿Qué pasó en el lote durante el período analizado?'
        
        Objetivo: Explicar en lenguaje simple y narrativo los eventos principales
        del período, agrupados por bloques temporales significativos.
        """
        elements = []
        
        # Título de la sección
        titulo = Paragraph("¿Qué pasó en el lote durante el período analizado?", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        bloques = bloques_info.get('bloques', [])
        
        if not bloques:
            elements.append(Paragraph("No hay suficientes datos para generar un análisis narrativo.", self.estilos['TextoNormal']))
            return elements
        
        # Introducción temporal
        fecha_inicio = bloques[0]['fecha_inicio']
        fecha_fin = bloques[-1]['fecha_fin']
        meses_totales = (fecha_fin.year - fecha_inicio.year) * 12 + (fecha_fin.month - fecha_inicio.month) + 1
        
        intro_texto = f"""
Durante el período de <strong>{meses_totales} meses</strong> analizado (desde {fecha_inicio.strftime('%B %Y')} hasta {fecha_fin.strftime('%B %Y')}), 
el lote <strong>{parcela.nombre}</strong> de <strong>{parcela.area_hectareas:.1f} hectáreas</strong> con cultivo de <strong>{parcela.tipo_cultivo or 'cultivo agrícola'}</strong> 
pasó por <strong>{len(bloques)} fases diferenciadas</strong> de desarrollo.
"""
        elements.append(Paragraph(intro_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Análisis por bloques
        for idx, bloque in enumerate(bloques, 1):
            # Título del bloque
            bloque_titulo = f"<strong>Fase {idx}: {bloque['fase']}</strong> ({bloque['fecha_inicio'].strftime('%b %Y')} - {bloque['fecha_fin'].strftime('%b %Y')})"
            elements.append(Paragraph(bloque_titulo, self.estilos['SubtituloSeccion']))
            elements.append(Spacer(1, 0.3*cm))
            
            # Estadísticas del bloque
            ndvi_prom = sum(bloque['ndvi_promedio']) / len(bloque['ndvi_promedio']) if bloque['ndvi_promedio'] else 0
            ndmi_prom = sum(bloque['ndmi_promedio']) / len(bloque['ndmi_promedio']) if bloque['ndmi_promedio'] else 0
            ndvi_min = min(bloque['ndvi_promedio']) if bloque['ndvi_promedio'] else 0
            ndvi_max = max(bloque['ndvi_promedio']) if bloque['ndvi_promedio'] else 0
            
            # Interpretación narrativa según la fase
            if bloque['fase'] == 'Establecimiento/Emergencia':
                narracion = f"""
El cultivo inició su desarrollo con un <strong>índice de vegetación promedio de {ndvi_prom:.2f}</strong>, 
lo cual es esperado para esta fase temprana. Los valores variaron entre {ndvi_min:.2f} y {ndvi_max:.2f}, 
indicando una <strong>germinación uniforme</strong> en el lote.
"""
            elif bloque['fase'] == 'Crecimiento Activo':
                narracion = f"""
Durante esta fase, el cultivo mostró un <strong>desarrollo vigoroso</strong> con un índice promedio de <strong>{ndvi_prom:.2f}</strong>.
El contenido de humedad en las plantas fue de <strong>{ndmi_prom:.2f}</strong>, lo que indica 
{"condiciones hídricas adecuadas" if ndmi_prom > 0.3 else "estrés hídrico moderado que requiere atención"}.
"""
            elif bloque['fase'] == 'Desarrollo Pleno':
                narracion = f"""
El cultivo alcanzó su <strong>máximo desarrollo vegetativo</strong> con un índice de {ndvi_prom:.2f}.
Esta fase representa el <strong>punto óptimo</strong> de cobertura vegetal y actividad fotosintética.
"""
            else:  # Maduración
                narracion = f"""
En esta fase final, el cultivo presentó un índice de vegetación de {ndvi_prom:.2f}, consistente con el 
proceso de <strong>maduración fisiológica</strong> y preparación para la cosecha.
"""
            
            elements.append(Paragraph(narracion, self.estilos['TextoNormal']))
            
            # Eventos relevantes del bloque
            if bloque['eventos_relevantes']:
                elements.append(Spacer(1, 0.2*cm))
                elements.append(Paragraph("<strong>Eventos destacados:</strong>", self.estilos['TextoNormal']))
                for evento in bloque['eventos_relevantes']:
                    elements.append(Paragraph(f"• {evento}", self.estilos['TextoNormal']))
            
            elements.append(Spacer(1, 0.4*cm))
        
        # Resultado final
        ndvi_final = bloques[-1]['ndvi_promedio'][-1] if bloques[-1]['ndvi_promedio'] else 0
        ndvi_inicial = bloques[0]['ndvi_promedio'][0] if bloques[0]['ndvi_promedio'] else 0
        cambio_total = ((ndvi_final - ndvi_inicial) / ndvi_inicial * 100) if ndvi_inicial > 0 else 0
        
        if cambio_total > 0:
            tendencia = "positiva"
            interpretacion = "crecimiento exitoso"
        elif cambio_total < -10:
            tendencia = "negativa"
            interpretacion = "deterioro que requiere atención"
        else:
            tendencia = "estable"
            interpretacion = "estabilización del cultivo"
        
        conclusion = f"""
<strong>Conclusión del período:</strong> Al finalizar los {meses_totales} meses analizados, el cultivo mostró una 
<strong>tendencia {tendencia}</strong> con un cambio total del <strong>{abs(cambio_total):.1f}%</strong> en el índice de vegetación, 
lo que indica un {interpretacion}.
"""
        elements.append(Paragraph(conclusion, self.estilos['TextoNormal']))
        
        return elements
'''

print("✅ Archivo con nuevas funciones creado")
print(f"Longitud de FUNCION_NARRATIVA: {len(FUNCION_NARRATIVA)} caracteres")
