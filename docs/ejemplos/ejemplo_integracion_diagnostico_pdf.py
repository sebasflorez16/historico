"""
EJEMPLO DE INTEGRACIÓN: Cerebro de Diagnóstico en Generador PDF
================================================================

Este archivo muestra EXACTAMENTE cómo integrar el diagnóstico unificado
en el archivo `informes/services/generador_pdf.py`.

NO ejecutar este archivo directamente - es solo un ejemplo de código.
"""

# ============================================================================
# UBICACIÓN EN generador_pdf.py: Método generar_informe() o similar
# ============================================================================

def ejemplo_integracion_en_generador_pdf(self):
    """
    Ejemplo de integración completa del diagnóstico unificado
    
    COPIAR estas secciones en el método correspondiente de generador_pdf.py
    """
    
    # ========================================================================
    # PASO 1: Importar las dependencias necesarias
    # ========================================================================
    
    # Al inicio del archivo generador_pdf.py:
    """
    from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
    from informes.helpers.diagnostico_pdf_helper import (
        agregar_seccion_diagnostico_unificado,
        generar_tabla_desglose_severidad
    )
    from pathlib import Path
    from django.conf import settings
    """
    
    # ========================================================================
    # PASO 2: Ejecutar el diagnóstico (después del análisis mensual)
    # ========================================================================
    
    # UBICACIÓN: Después de procesar todos los índices mensuales (NDVI, NDMI, SAVI)
    # pero ANTES de generar el PDF final
    
    """
    logger.info("🧠 Ejecutando diagnóstico unificado...")
    
    try:
        # Crear directorio de salida
        diagnostico_dir = Path(settings.MEDIA_ROOT) / 'diagnosticos' / f'parcela_{self.parcela.id}'
        diagnostico_dir.mkdir(parents=True, exist_ok=True)
        
        # Ejecutar diagnóstico
        diagnostico_unificado = ejecutar_diagnostico_unificado(
            datos_indices={
                'ndvi': self.ndvi_promedio_array,  # Array NumPy con promedio del período
                'ndmi': self.ndmi_promedio_array,  # Array NumPy con promedio del período
                'savi': self.savi_promedio_array   # Array NumPy con promedio del período
            },
            geo_transform=self.geo_transform,  # Del GeoTIFF de EOSDA
            area_parcela_ha=self.parcela.area_hectareas,
            output_dir=diagnostico_dir,
            tipo_informe=self.tipo_informe,  # 'produccion' o 'evaluacion'
            resolucion_m=10.0  # Sentinel-2
        )
        
        logger.info(f"✅ Diagnóstico completado: {len(diagnostico_unificado.zonas_criticas)} zonas detectadas")
        logger.info(f"   Eficiencia del lote: {diagnostico_unificado.eficiencia_lote:.1f}%")
        logger.info(f"   Área afectada total: {diagnostico_unificado.area_afectada_total:.2f} ha")
        
        # Guardar en variable de instancia para usar en el PDF
        self.diagnostico_unificado = diagnostico_unificado
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando diagnóstico unificado: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        self.diagnostico_unificado = None
    """
    
    # ========================================================================
    # PASO 3: OPCIÓN A - Integración automática (recomendado)
    # ========================================================================
    
    # UBICACIÓN: En el método que construye el story del PDF
    # DESPUÉS de la sección de análisis mensual
    
    """
    # ... (código existente del PDF) ...
    
    # Análisis mensual de índices (NDVI, NDMI, SAVI)
    story.append(PageBreak())
    story.append(Paragraph("ANÁLISIS MENSUAL DE ÍNDICES", self.estilos['Heading1']))
    # ... gráficos mensuales ...
    
    # === NUEVA SECCIÓN: DIAGNÓSTICO UNIFICADO ===
    if hasattr(self, 'diagnostico_unificado') and self.diagnostico_unificado:
        agregar_seccion_diagnostico_unificado(
            story=story,
            diagnostico=self.diagnostico_unificado,
            estilos=self.estilos,
            ubicacion='resumen'  # Solo el resumen en esta parte
        )
    
    # ... (más adelante en el PDF, antes de las recomendaciones finales) ...
    
    # === SECCIÓN DETALLE DEL DIAGNÓSTICO ===
    if hasattr(self, 'diagnostico_unificado') and self.diagnostico_unificado:
        agregar_seccion_diagnostico_unificado(
            story=story,
            diagnostico=self.diagnostico_unificado,
            estilos=self.estilos,
            ubicacion='detalle'  # Solo el detalle técnico
        )
    
    # ... (resto del PDF: recomendaciones, anexos, etc.) ...
    """
    
    # ========================================================================
    # PASO 3: OPCIÓN B - Integración manual (más control)
    # ========================================================================
    
    # Si prefieres agregar cada elemento manualmente para más control:
    
    """
    # === SECCIÓN RESUMEN EJECUTIVO ===
    story.append(PageBreak())
    story.append(Paragraph("DIAGNÓSTICO UNIFICADO", self.estilos['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    if hasattr(self, 'diagnostico_unificado') and self.diagnostico_unificado:
        diag = self.diagnostico_unificado
        
        # 1. Resumen ejecutivo
        story.append(Paragraph(diag.resumen_ejecutivo, self.estilos['BodyText']))
        story.append(Spacer(1, 0.3*inch))
        
        # 2. Tabla de desglose por severidad
        story.append(Paragraph("<b>Desglose de Áreas por Severidad</b>", self.estilos['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        
        tabla_severidad = generar_tabla_desglose_severidad(diag.desglose_severidad)
        story.append(tabla_severidad)
        story.append(Spacer(1, 0.3*inch))
        
        # 3. Mapa consolidado
        if os.path.exists(diag.mapa_diagnostico_path):
            story.append(Paragraph("<b>Mapa de Zonas Críticas</b>", self.estilos['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            img = Image(diag.mapa_diagnostico_path, width=6*inch, height=4.3*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph(
                "<i>Mapa consolidado con zonas clasificadas por severidad. "
                "Las zonas rojas requieren intervención inmediata.</i>",
                self.estilos['Caption']
            ))
            story.append(Spacer(1, 0.3*inch))
        
        # 4. Información de zona prioritaria (si existe)
        if diag.zona_prioritaria:
            story.append(Paragraph("<b>Zona Prioritaria</b>", self.estilos['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            zona = diag.zona_prioritaria
            lat, lon = zona.centroide_geo
            
            info_text = (
                f"<b>Tipo:</b> {zona.etiqueta_comercial}<br/>"
                f"<b>Área:</b> {zona.area_hectareas:.2f} ha<br/>"
                f"<b>Severidad:</b> {zona.severidad*100:.0f}%<br/>"
                f"<b>Coordenadas:</b> {lat:.6f}, {lon:.6f}<br/>"
                f"<b>Confianza:</b> {zona.confianza*100:.0f}%<br/><br/>"
                f"<b>Valores de Índices:</b><br/>"
                f"• NDVI: {zona.valores_indices['ndvi']:.3f}<br/>"
                f"• NDMI: {zona.valores_indices['ndmi']:.3f}<br/>"
                f"• SAVI: {zona.valores_indices['savi']:.3f}"
            )
            story.append(Paragraph(info_text, self.estilos['BodyText']))
            story.append(Spacer(1, 0.3*inch))
    
    # === MÁS ADELANTE: DIAGNÓSTICO TÉCNICO DETALLADO ===
    story.append(PageBreak())
    story.append(Paragraph("DIAGNÓSTICO TÉCNICO DETALLADO", self.estilos['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    if hasattr(self, 'diagnostico_unificado') and self.diagnostico_unificado:
        story.append(Paragraph(
            self.diagnostico_unificado.diagnostico_detallado,
            self.estilos['BodyText']
        ))
        story.append(Spacer(1, 0.3*inch))
    """
    
    # ========================================================================
    # PASO 4: Usar métricas en el contexto general del PDF
    # ========================================================================
    
    """
    from informes.helpers import obtener_resumen_metricas_diagnostico
    
    if hasattr(self, 'diagnostico_unificado') and self.diagnostico_unificado:
        metricas = obtener_resumen_metricas_diagnostico(self.diagnostico_unificado)
        
        # Usar en portada o resumen ejecutivo
        portada_context = {
            'eficiencia_lote': metricas['eficiencia_lote'],
            'num_zonas_criticas': metricas['num_zonas_criticas'],
            'area_critica': metricas['area_critica'],
            'tiene_zona_roja': metricas['area_critica'] > 0,
            # ... otros campos del contexto ...
        }
        
        # Ejemplo de uso en texto dinámico
        if metricas['tiene_zona_prioritaria']:
            texto_alerta = (
                f"⚠️ ALERTA: Se detectó una zona {metricas['zona_prioritaria_tipo']} "
                f"de {metricas['zona_prioritaria_area']:.2f} ha con severidad "
                f"{metricas['zona_prioritaria_severidad']*100:.0f}%"
            )
            story.append(Paragraph(texto_alerta, self.estilos['Alert']))
    """
    
    # ========================================================================
    # PASO 5: OPCIONAL - Exportación VRA bajo demanda
    # ========================================================================
    
    # IMPORTANTE: NO ejecutar automáticamente, solo cuando usuario lo solicite
    # Agregar en una vista separada (ej: exportar_vra_view)
    
    """
    from informes.motor_analisis.cerebro_diagnostico import generar_archivo_prescripcion_vra
    
    # En una vista de exportación:
    @login_required
    def exportar_vra_view(request, informe_id):
        try:
            informe = InformeGenerado.objects.get(id=informe_id)
            
            # El diagnostico debe estar guardado en el informe o regenerado
            diagnostico = # ... obtener diagnostico ...
            
            archivo_kml = generar_archivo_prescripcion_vra(
                diagnostico=diagnostico,
                parcela_nombre=informe.parcela.nombre,
                formato='kml'
            )
            
            if archivo_kml:
                with open(archivo_kml, 'rb') as f:
                    response = HttpResponse(
                        f.read(), 
                        content_type='application/vnd.google-earth.kml+xml'
                    )
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(archivo_kml)}"'
                    return response
            else:
                messages.error(request, "No hay zonas críticas suficientes para generar VRA")
                return redirect('informes:detalle_informe', informe_id=informe_id)
                
        except Exception as e:
            logger.error(f"Error exportando VRA: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
            return redirect('informes:dashboard')
    """
    
    pass


# ============================================================================
# CHECKLIST DE INTEGRACIÓN
# ============================================================================

"""
CHECKLIST PARA INTEGRAR EN PRODUCCIÓN:
======================================

[ ] 1. Importar dependencias al inicio de generador_pdf.py:
    - ejecutar_diagnostico_unificado
    - agregar_seccion_diagnostico_unificado
    - generar_tabla_desglose_severidad

[ ] 2. Asegurar que existan arrays promedio de índices:
    - self.ndvi_promedio_array
    - self.ndmi_promedio_array
    - self.savi_promedio_array

[ ] 3. Ejecutar diagnóstico después del análisis mensual:
    - Llamar ejecutar_diagnostico_unificado()
    - Guardar resultado en self.diagnostico_unificado

[ ] 4. Agregar sección resumen al PDF:
    - Después de análisis mensual
    - Usar agregar_seccion_diagnostico_unificado(..., ubicacion='resumen')

[ ] 5. Agregar sección detalle al PDF:
    - Antes de recomendaciones finales
    - Usar agregar_seccion_diagnostico_unificado(..., ubicacion='detalle')

[ ] 6. OPCIONAL - Implementar vista de exportación VRA:
    - Solo si el cliente usa maquinaria VRA
    - Crear botón en interfaz web
    - Implementar vista exportar_vra_view()

[ ] 7. Probar con parcela real:
    - Generar informe completo
    - Verificar que aparezcan todas las secciones
    - Validar que el mapa se muestre correctamente
    - Confirmar que las narrativas sean coherentes

[ ] 8. Validar en producción:
    - Revisar logs para errores
    - Verificar rendimiento (tiempo de ejecución)
    - Confirmar que los archivos se guarden correctamente
"""

# ============================================================================
# NOTAS IMPORTANTES
# ============================================================================

"""
⚠️ IMPORTANTE:

1. ARRAYS PROMEDIO:
   Asegúrate de que los arrays ndvi_promedio_array, ndmi_promedio_array y 
   savi_promedio_array sean NumPy arrays con la misma forma (shape).
   
   Ejemplo de cálculo:
   ndvi_promedio_array = np.mean([ndvi_mes1, ndvi_mes2, ndvi_mes3], axis=0)

2. GEO_TRANSFORM:
   El geo_transform debe venir del GeoTIFF de EOSDA. Es una tupla de 6 elementos:
   (top_left_x, pixel_width, rotation_x, top_left_y, rotation_y, pixel_height)

3. TIPO_INFORME:
   Puede ser 'produccion' o 'evaluacion'. Esto cambia el lenguaje de las narrativas:
   - 'produccion': Enfocado en rentabilidad y rendimiento
   - 'evaluacion': Enfocado en aptitud de suelo y limitantes

4. RENDIMIENTO:
   El diagnóstico toma ~2-3 segundos para un raster de 100x100.
   Para parcelas muy grandes (>500x500), considera:
   - Hacer downsampling del raster
   - Ejecutar en background task (Celery)
   - Cachear el resultado

5. COMPATIBILIDAD:
   El sistema NO interfiere con los mapas mensuales existentes.
   El mapa consolidado es ADICIONAL, no reemplaza nada.

6. EXPORTACIÓN VRA:
   NO se ejecuta automáticamente. Es una funcionalidad opcional
   que debe ser invocada explícitamente por el usuario.
"""

if __name__ == '__main__':
    print(__doc__)
    print("\n⚠️ Este es un archivo de EJEMPLO.")
    print("No ejecutar directamente - copiar código a generador_pdf.py")
