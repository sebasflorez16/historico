# NUEVAS FUNCIONES PARA GENERADOR_PDF.PY
# Estas funciones se deben agregar a la clase GeneradorPDFProfesional

Para agregar después de la función `_crear_info_parcela` (línea ~1125):

```python
    def _agrupar_meses_en_bloques(self, indices: List[IndiceMensual]) -> Dict:
        """
        Agrupa los meses en bloques temporales basados en cambios significativos
        
        Criterios de agrupación:
        - Cambios en tendencia NDVI > 10%
        - Eventos climáticos extremos (sequía/exceso de lluvia)
        - Transiciones fenológicas detectadas automáticamente
        
        Returns:
            Dict con bloques agrupados, cada uno con análisis consolidado
        """
        if not indices:
            return {}
        
        bloques = []
        bloque_actual = {
            'indices': [],
            'fecha_inicio': None,
            'fecha_fin': None,
            'ndvi_promedio': [],
            'ndmi_promedio': [],
            'fase': '',
            'eventos_relevantes': []
        }
        
        for i, indice in enumerate(indices):
            # Agregar al bloque actual
            bloque_actual['indices'].append(indice)
            if indice.ndvi_promedio:
                bloque_actual['ndvi_promedio'].append(indice.ndvi_promedio)
            if indice.ndmi_promedio:
                bloque_actual['ndmi_promedio'].append(indice.ndmi_promedio)
            
            if not bloque_actual['fecha_inicio']:
                bloque_actual['fecha_inicio'] = date(indice.año, indice.mes, 1)
            bloque_actual['fecha_fin'] = date(indice.año, indice.mes, 1)
            
            # Detectar cambios significativos que justifiquen cerrar el bloque
            debe_cerrar_bloque = False
            
            if i < len(indices) - 1:
                siguiente = indices[i + 1]
                
                # Cambio en NDVI > 15%
                if indice.ndvi_promedio and siguiente.ndvi_promedio:
                    cambio_ndvi = abs(siguiente.ndvi_promedio - indice.ndvi_promedio) / indice.ndvi_promedio
                    if cambio_ndvi > 0.15:
                        debe_cerrar_bloque = True
                        bloque_actual['eventos_relevantes'].append(f"Cambio significativo en NDVI ({cambio_ndvi*100:.1f}%)")
                
                # Estrés hídrico detectado (NDMI < 0.2)
                if indice.ndmi_promedio and indice.ndmi_promedio < 0.2:
                    bloque_actual['eventos_relevantes'].append(f"Estrés hídrico detectado en {indice.periodo_texto}")
                
                # Cierre automático cada 3-4 meses
                if len(bloque_actual['indices']) >= 3:
                    debe_cerrar_bloque = True
            else:
                # Último índice: cerrar bloque
                debe_cerrar_bloque = True
            
            if debe_cerrar_bloque:
                # Clasificar fase fenológica
                ndvi_prom_bloque = sum(bloque_actual['ndvi_promedio']) / len(bloque_actual['ndvi_promedio']) if bloque_actual['ndvi_promedio'] else 0
                
                if ndvi_prom_bloque < 0.4:
                    bloque_actual['fase'] = 'Establecimiento/Emergencia'
                elif ndvi_prom_bloque < 0.65:
                    bloque_actual['fase'] = 'Crecimiento Activo'
                elif ndvi_prom_bloque < 0.75:
                    bloque_actual['fase'] = 'Desarrollo Pleno'
                else:
                    bloque_actual['fase'] = 'Maduración'
                
                bloques.append(bloque_actual.copy())
                
                # Resetear bloque
                bloque_actual = {
                    'indices': [],
                    'fecha_inicio': None,
                    'fecha_fin': None,
                    'ndvi_promedio': [],
                    'ndmi_promedio': [],
                    'fase': '',
                    'eventos_relevantes': []
                }
        
        return {'bloques': bloques, 'total_bloques': len(bloques)}
```

INSTRUCCIONES DE INTEGRACIÓN:
1. Las nuevas funciones _crear_seccion_narrativa_lote, _crear_seccion_zonas_diferenciales y _crear_seccion_impacto_productivo 
   se deben agregar después de _agrupar_meses_en_bloques
2. Luego modificar generar_informe_completo() para llamar a estas nuevas secciones en el orden correcto
3. La estructura debe quedar así en generar_informe_completo():
   - Portada
   - Metodología
   - Resumen Ejecutivo
   - **NUEVO: ¿Qué pasó en el lote?**
   - Info Parcela
   - **NUEVO: Zonas Diferenciales**
   - Análisis NDVI/NDMI/SAVI (con "En palabras simples")
   - Tendencias
   - **NUEVO: Impacto Productivo**
   - Recomendaciones (mejoradas)
   - Tabla datos
   - Créditos
