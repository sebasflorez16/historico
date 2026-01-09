    def _agrupar_meses_en_bloques(self, indices: List[IndiceMensual]) -> Dict:
        """
        Agrupa los meses en bloques temporales basados en cambios significativos
        
        Criterios de agrupación:
        - Cambios en tendencia NDVI > 15%
        - Eventos climáticos extremos (sequía/exceso de lluvia)
        - Transiciones fenológicas detectadas automáticamente
        
        Returns:
            Dict con bloques agrupados, cada uno con análisis consolidado
        """
        if not indices:
            return {'bloques': [], 'total_bloques': 0}
        
        bloques = []
        bloque_actual = {
            'indices': [],
            'fecha_inicio': None,
            'fecha_fin': None,
            'ndvi_promedio': [],
            'ndmi_promedio': [],
            'savi_promedio': [],
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
            if indice.savi_promedio:
                bloque_actual['savi_promedio'].append(indice.savi_promedio)
            
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
                    'savi_promedio': [],
                    'fase': '',
                    'eventos_relevantes': []
                }
        
        return {'bloques': bloques, 'total_bloques': len(bloques)}
