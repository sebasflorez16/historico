# MÉTODOS DE FASE B - Mapas Avanzados
# Agregar ANTES del método _generar_mapa_parcela (línea 871)

def _generar_mapa_contexto_regional(self, parcela: Parcela, departamento: str = "Casanare") -> BytesIO:
    """
    B1: Genera mapa de CONTEXTO REGIONAL
    Vista amplia del departamento con punto marcando ubicación de la parcela
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Convertir geometría de la parcela
    if hasattr(parcela.geometria, 'wkt'):
        parcela_geom = wkt.loads(parcela.geometria.wkt)
    else:
        parcela_geom = shape(parcela.geometria)
    
    parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
    
    # Obtener bbox del departamento
    dept_info = DEPARTAMENTOS_INFO.get(departamento, {})
    bbox = dept_info.get('bbox', None)
    
    if bbox:
        ax.set_xlim(bbox[0], bbox[2])
        ax.set_ylim(bbox[1], bbox[3])
        
        # Rectángulo del departamento
        from matplotlib.patches import Rectangle
        rect = Rectangle(
            (bbox[0], bbox[1]), bbox[2] - bbox[0], bbox[3] - bbox[1],
            linewidth=3, edgecolor='darkgreen', facecolor='lightgreen',
            alpha=0.2, label=f'{departamento} (región)'
        )
        ax.add_patch(rect)
    
    # Marcar parcela con estrella roja
    centroide = parcela_gdf.geometry.centroid.iloc[0]
    ax.plot(centroide.x, centroide.y, marker='*', color='red', markersize=25,
            markeredgecolor='darkred', markeredgewidth=2, label='Ubicación Parcela', zorder=100)
    
    # Círculo alrededor
    from matplotlib.patches import Circle
    circulo = Circle((centroide.x, centroide.y), 0.05, linewidth=2, edgecolor='red',
                    facecolor='none', linestyle='--', alpha=0.8, zorder=99)
    ax.add_patch(circulo)
    
    ax.set_title(f'Contexto Regional - {departamento}\\nUbicación de {parcela.nombre}',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitud', fontsize=10)
    ax.set_ylabel('Latitud', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    
    plt.tight_layout()
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    return img_buffer

def _generar_mapa_silueta(self, parcela: Parcela) -> BytesIO:
    """
    B2: Genera mapa de SILUETA LIMPIA
    Solo polígono de la parcela sin capas superpuestas
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Convertir geometría
    if hasattr(parcela.geometria, 'wkt'):
        parcela_geom = wkt.loads(parcela.geometria.wkt)
    else:
        parcela_geom = shape(parcela.geometria)
    
    parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
    
    # Dibujar SOLO la parcela
    parcela_gdf.plot(ax=ax, facecolor='#90EE90', edgecolor='darkgreen',
                    linewidth=3, alpha=0.6)
    
    # Fondo limpio blanco
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    # Título minimalista
    ax.set_title(f'{parcela.nombre}\\nÁrea: {parcela.area_hectareas:.2f} ha',
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitud', fontsize=10)
    ax.set_ylabel('Latitud', fontsize=10)
    
    # Grid sutil
    ax.grid(True, alpha=0.2, linestyle=':', color='gray')
    
    plt.tight_layout()
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close(fig)
    return img_buffer

def _agregar_escala_grafica(self, ax, parcela_gdf):
    """
    B3: Agrega ESCALA GRÁFICA al mapa
    Barra de escala con medidas en km/m adaptativa según zoom
    """
    from matplotlib.patches import Rectangle
    from matplotlib.lines import Line2D
    
    # Calcular escala apropiada según tamaño de la parcela
    bounds = parcela_gdf.total_bounds
    ancho_mapa = bounds[2] - bounds[0]  # En grados
    
    # Convertir a metros aproximados (1 grado ≈ 111 km en Colombia)
    ancho_km = ancho_mapa * 111
    
    # Determinar longitud de la barra (redondeada)
    if ancho_km < 1:
        long_barra_m = 100  # 100 metros
        texto_escala = '100 m'
        long_barra_grados = long_barra_m / 111000
    elif ancho_km < 5:
        long_barra_m = 500
        texto_escala = '500 m'
        long_barra_grados = long_barra_m / 111000
    elif ancho_km < 10:
        long_barra_km = 1
        texto_escala = '1 km'
        long_barra_grados = long_barra_km / 111
    else:
        long_barra_km = 5
        texto_escala = '5 km'
        long_barra_grados = long_barra_km / 111
    
    # Posición de la barra (esquina inferior derecha)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    x_inicio = xlim[1] - (xlim[1] - xlim[0]) * 0.25
    y_base = ylim[0] + (ylim[1] - ylim[0]) * 0.05
    
    # Dibujar barra de escala (blanco y negro alternado)
    segmentos = 4
    for i in range(segmentos):
        color = 'black' if i % 2 == 0 else 'white'
        rect = Rectangle(
            (x_inicio + i * long_barra_grados / segmentos, y_base),
            long_barra_grados / segmentos,
            (ylim[1] - ylim[0]) * 0.015,
            facecolor=color,
            edgecolor='black',
            linewidth=1,
            zorder=200
        )
        ax.add_patch(rect)
    
    # Texto de la escala
    ax.text(
        x_inicio + long_barra_grados / 2,
        y_base - (ylim[1] - ylim[0]) * 0.02,
        texto_escala,
        fontsize=9,
        fontweight='bold',
        ha='center',
        va='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=1),
        zorder=201
    )
