"""
🎯 Método para generar mapa de intervención limpio
Código para insertar en cerebro_diagnostico.py después de _generar_mapa_diagnostico
"""

def _generar_mapa_intervencion_limpio(
    self,
    ndvi: np.ndarray,
    zonas_por_severidad: Dict[str, List[ZonaCritica]],
    zona_prioritaria: Optional[ZonaCritica],
    output_dir: Path
) -> Path:
    """
    🎯 NUEVO: Genera mapa de intervención limpio para uso en campo
    
    Características:
    - Fondo en escala de grises (eliminando ruido visual de índices)
    - Contornos gruesos y claros con código de colores
    - Numeración de zonas por prioridad
    - Sin decoraciones complejas, enfocado en acción
    
    Args:
        ndvi: Array NDVI base (para fondo)
        zonas_por_severidad: Zonas agrupadas por nivel
        zona_prioritaria: Zona de máxima prioridad
        output_dir: Directorio de salida
        
    Returns:
        Path al mapa generado
    """
    logger.info("🗺️ Generando mapa de intervención limpio...")
    
    fig, ax = plt.subplots(figsize=(14, 11), dpi=120)
    
    # ===== FONDO LIMPIO EN ESCALA DE GRISES =====
    # Normalizar NDVI a 0-1 para visualización
    ndvi_normalizado = np.clip((ndvi + 1) / 2, 0, 1)  # De [-1,1] a [0,1]
    
    # Convertir a escala de grises (sin verde que confunda)
    fondo_gris = np.stack([ndvi_normalizado] * 3, axis=-1)  # RGB igual = gris
    
    # Ajustar contraste suave (evitar que zonas oscuras sean muy oscuras)
    fondo_gris = np.clip(fondo_gris * 0.7 + 0.2, 0, 1)
    
    ax.imshow(fondo_gris, cmap='gray', alpha=0.6, origin='upper')
    
    # ===== DIBUJAR CONTORNOS POR SEVERIDAD =====
    num_zona_total = 1
    
    for nivel in ['critica', 'moderada', 'leve']:
        zonas = zonas_por_severidad.get(nivel, [])
        if not zonas:
            continue
        
        config = self.NIVELES_SEVERIDAD[nivel]
        color = config['color']
        
        # Grosor según nivel (críticas más gruesas)
        linewidth = {
            'critica': 5.0,
            'moderada': 4.0,
            'leve': 3.0
        }[nivel]
        
        for zona in zonas:
            # Obtener la máscara del cluster
            x_min, y_min, x_max, y_max = zona.bbox
            
            # Dibujar rectángulo grueso con el color del nivel
            from matplotlib.patches import Rectangle, Polygon
            rect = Rectangle(
                (x_min, y_min),
                x_max - x_min,
                y_max - y_min,
                linewidth=linewidth,
                edgecolor=color,
                facecolor=color,
                alpha=0.2,
                zorder=20
            )
            ax.add_patch(rect)
            
            # ===== NUMERACIÓN Y ETIQUETA =====
            cx, cy = zona.centroide_pixel
            
            # Círculo numerado
            from matplotlib.patches import Circle
            circle = Circle(
                (cx, cy),
                radius=max(ndvi.shape) * 0.025,
                facecolor='white',
                edgecolor=color,
                linewidth=3,
                zorder=30
            )
            ax.add_patch(circle)
            
            # Número de la zona
            ax.text(
                cx, cy,
                str(num_zona_total),
                fontsize=14,
                fontweight='bold',
                color='black',
                ha='center',
                va='center',
                zorder=31
            )
            
            # Etiqueta tipo de problema (arriba del círculo)
            etiqueta_corta = zona.etiqueta_comercial.split('/')[0]  # Solo primera parte
            ax.text(
                cx, cy - max(ndvi.shape) * 0.045,
                etiqueta_corta,
                fontsize=9,
                fontweight='bold',
                color=color,
                ha='center',
                va='bottom',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor=color),
                zorder=32
            )
            
            num_zona_total += 1
    
    # ===== MARCADOR ESPECIAL ZONA PRIORITARIA =====
    if zona_prioritaria:
        cx, cy = zona_prioritaria.centroide_pixel
        
        # Doble círculo para resaltar
        for radius_mult, lw in [(0.055, 5), (0.045, 3)]:
            circle_priority = Circle(
                (cx, cy),
                radius=max(ndvi.shape) * radius_mult,
                facecolor='none',
                edgecolor='#FF0000',
                linewidth=lw,
                linestyle='--',
                zorder=40
            )
            ax.add_patch(circle_priority)
        
        # Etiqueta "PRIORIDAD 1"
        ax.text(
            cx, cy + max(ndvi.shape) * 0.08,
            '⚠️ PRIORIDAD 1',
            fontsize=12,
            fontweight='bold',
            color='white',
            ha='center',
            va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FF0000', alpha=0.95, edgecolor='white', linewidth=2),
            zorder=41
        )
    
    # ===== TÍTULO Y LEYENDA SIMPLES =====
    ax.set_title(
        'MAPA DE ZONAS DE INTERVENCIÓN\n(Numeradas por prioridad)',
        fontsize=15,
        fontweight='bold',
        pad=15,
        color='#2C3E50'
    )
    
    # Leyenda compacta
    leyenda_patches = []
    for nivel in ['critica', 'moderada', 'leve']:
        config = self.NIVELES_SEVERIDAD[nivel]
        num_zonas = len(zonas_por_severidad[nivel])
        if num_zonas > 0:
            etiqueta_simple = {
                'critica': f'🔴 Crítica ({num_zonas} zonas)',
                'moderada': f'⚠️ Moderada ({num_zonas} zonas)',
                'leve': f'⚡ Leve ({num_zonas} zonas)'
            }[nivel]
            
            patch = mpatches.Patch(color=config['color'], label=etiqueta_simple)
            leyenda_patches.append(patch)
    
    if leyenda_patches:
        ax.legend(
            handles=leyenda_patches,
            loc='upper left',
            fontsize=10,
            framealpha=0.95,
            edgecolor='black',
            title='Código de Colores'
        )
    
    # Remover ejes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Guardar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f'mapa_intervencion_limpio_{timestamp}.png'
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='white')
    plt.close(fig)
    
    logger.info(f"✅ Mapa de intervención limpio guardado: {output_path}")
    
    return output_path
