/**
 * 🎨 Motor de Filtros de Visualización
 * Gestiona filtros CSS/Canvas para mejorar la visualización (brillo, contraste, saturación)
 * 
 * @module FilterEngine
 * @author AgroTech Team
 * @version 1.0.0
 */

class FilterEngine {
    constructor(player) {
        this.player = player;
        
        // Valores de filtros (en porcentaje)
        this.filters = {
            brightness: 100,    // 50-150
            contrast: 100,      // 50-150
            saturate: 100,      // 0-200
            grayscale: 0        // 0-100
        };
        
        // Valores por defecto para reset
        this.defaults = { ...this.filters };
        
        console.log('FilterEngine inicializado');
    }
    
    /**
     * Inicializa el motor de filtros
     */
    init() {
        this.createFilterControls();
        this.applyFilters(); // Aplicar filtros iniciales
    }
    
    /**
     * Crea controles de filtros en la UI
     */
    createFilterControls() {
        // Buscar panel de configuración
        let configPanel = document.getElementById('timeline-config-panel');
        
        if (!configPanel) {
            // Crear panel si no existe
            const container = document.querySelector('.timeline-container');
            if (!container) return;
            
            configPanel = document.createElement('div');
            configPanel.id = 'timeline-config-panel';
            configPanel.className = 'timeline-config-panel collapsed';
            configPanel.innerHTML = `
                <button id="toggle-config-panel" class="btn btn-sm config-toggle">
                    <i class="bi bi-gear"></i> Configuración
                </button>
                <div class="config-content">
                    <h6>⚙️ Configuración del Timeline</h6>
                </div>
            `;
            container.appendChild(configPanel);
            
            // Toggle panel
            document.getElementById('toggle-config-panel').addEventListener('click', () => {
                configPanel.classList.toggle('collapsed');
            });
        }
        
        // Agregar sección de filtros
        const configContent = configPanel.querySelector('.config-content');
        if (!configContent) return;
        
        const filterSection = document.createElement('div');
        filterSection.className = 'config-section';
        filterSection.id = 'filter-config';
        filterSection.innerHTML = `
            <h6>🎨 Filtros de Visualización</h6>
            
            <div class="filter-group">
                <label>
                    <i class="bi bi-brightness-high"></i> Brillo
                </label>
                <div class="slider-group">
                    <input type="range" id="filter-brightness" 
                           min="50" max="150" step="5" value="${this.filters.brightness}">
                    <span id="brightness-value">${this.filters.brightness}%</span>
                </div>
            </div>
            
            <div class="filter-group">
                <label>
                    <i class="bi bi-circle-half"></i> Contraste
                </label>
                <div class="slider-group">
                    <input type="range" id="filter-contrast" 
                           min="50" max="150" step="5" value="${this.filters.contrast}">
                    <span id="contrast-value">${this.filters.contrast}%</span>
                </div>
            </div>
            
            <div class="filter-group">
                <label>
                    <i class="bi bi-palette"></i> Saturación
                </label>
                <div class="slider-group">
                    <input type="range" id="filter-saturate" 
                           min="0" max="200" step="10" value="${this.filters.saturate}">
                    <span id="saturate-value">${this.filters.saturate}%</span>
                </div>
            </div>
            
            <div class="filter-group">
                <label>
                    <i class="bi bi-circle"></i> Escala de grises
                </label>
                <div class="slider-group">
                    <input type="range" id="filter-grayscale" 
                           min="0" max="100" step="10" value="${this.filters.grayscale}">
                    <span id="grayscale-value">${this.filters.grayscale}%</span>
                </div>
            </div>
            
            <div class="filter-actions">
                <button id="reset-filters" class="btn btn-sm btn-outline-secondary">
                    <i class="bi bi-arrow-counterclockwise"></i> Resetear filtros
                </button>
            </div>
        `;
        
        configContent.appendChild(filterSection);
        
        // Event listeners
        this.setupFilterEventListeners();
    }
    
    /**
     * Configura event listeners para controles de filtros
     */
    setupFilterEventListeners() {
        // Brillo
        const brightnessSlider = document.getElementById('filter-brightness');
        const brightnessValue = document.getElementById('brightness-value');
        if (brightnessSlider && brightnessValue) {
            brightnessSlider.addEventListener('input', (e) => {
                this.filters.brightness = parseInt(e.target.value);
                brightnessValue.textContent = `${this.filters.brightness}%`;
                this.applyFilters();
            });
        }
        
        // Contraste
        const contrastSlider = document.getElementById('filter-contrast');
        const contrastValue = document.getElementById('contrast-value');
        if (contrastSlider && contrastValue) {
            contrastSlider.addEventListener('input', (e) => {
                this.filters.contrast = parseInt(e.target.value);
                contrastValue.textContent = `${this.filters.contrast}%`;
                this.applyFilters();
            });
        }
        
        // Saturación
        const saturateSlider = document.getElementById('filter-saturate');
        const saturateValue = document.getElementById('saturate-value');
        if (saturateSlider && saturateValue) {
            saturateSlider.addEventListener('input', (e) => {
                this.filters.saturate = parseInt(e.target.value);
                saturateValue.textContent = `${this.filters.saturate}%`;
                this.applyFilters();
            });
        }
        
        // Escala de grises
        const grayscaleSlider = document.getElementById('filter-grayscale');
        const grayscaleValue = document.getElementById('grayscale-value');
        if (grayscaleSlider && grayscaleValue) {
            grayscaleSlider.addEventListener('input', (e) => {
                this.filters.grayscale = parseInt(e.target.value);
                grayscaleValue.textContent = `${this.filters.grayscale}%`;
                this.applyFilters();
            });
        }
        
        // Botón reset
        const resetBtn = document.getElementById('reset-filters');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }
    }
    
    /**
     * Aplica los filtros CSS al canvas
     */
    applyFilters() {
        const canvas = this.player.canvas;
        if (!canvas) return;
        
        const filterString = this.getFilterString();
        canvas.style.filter = filterString;
        
        console.log(`Filtros aplicados: ${filterString}`);
    }
    
    /**
     * Genera el string CSS de filtros
     * @returns {string} String CSS con filtros
     */
    getFilterString() {
        const parts = [];
        
        if (this.filters.brightness !== 100) {
            parts.push(`brightness(${this.filters.brightness}%)`);
        }
        
        if (this.filters.contrast !== 100) {
            parts.push(`contrast(${this.filters.contrast}%)`);
        }
        
        if (this.filters.saturate !== 100) {
            parts.push(`saturate(${this.filters.saturate}%)`);
        }
        
        if (this.filters.grayscale > 0) {
            parts.push(`grayscale(${this.filters.grayscale}%)`);
        }
        
        return parts.length > 0 ? parts.join(' ') : 'none';
    }
    
    /**
     * Resetea todos los filtros a valores por defecto
     */
    resetFilters() {
        console.log('Reseteando filtros...');
        
        // Restaurar valores
        this.filters = { ...this.defaults };
        
        // Actualizar sliders
        const sliders = {
            'filter-brightness': this.filters.brightness,
            'filter-contrast': this.filters.contrast,
            'filter-saturate': this.filters.saturate,
            'filter-grayscale': this.filters.grayscale
        };
        
        Object.entries(sliders).forEach(([id, value]) => {
            const slider = document.getElementById(id);
            if (slider) {
                slider.value = value;
            }
        });
        
        // Actualizar valores mostrados
        document.getElementById('brightness-value').textContent = `${this.filters.brightness}%`;
        document.getElementById('contrast-value').textContent = `${this.filters.contrast}%`;
        document.getElementById('saturate-value').textContent = `${this.filters.saturate}%`;
        document.getElementById('grayscale-value').textContent = `${this.filters.grayscale}%`;
        
        // Aplicar filtros
        this.applyFilters();
        
        console.log('Filtros reseteados');
    }
    
    /**
     * Establece un filtro específico
     * @param {string} filterName - Nombre del filtro
     * @param {number} value - Valor del filtro
     */
    setFilter(filterName, value) {
        if (!(filterName in this.filters)) {
            console.warn(`⚠️ Filtro desconocido: ${filterName}`);
            return;
        }
        
        this.filters[filterName] = value;
        
        // Actualizar slider y valor
        const slider = document.getElementById(`filter-${filterName}`);
        const valueSpan = document.getElementById(`${filterName}-value`);
        
        if (slider) slider.value = value;
        if (valueSpan) valueSpan.textContent = `${value}%`;
        
        this.applyFilters();
    }
    
    /**
     * Obtiene el valor actual de un filtro
     * @param {string} filterName - Nombre del filtro
     * @returns {number} Valor del filtro
     */
    getFilter(filterName) {
        return this.filters[filterName] || 100;
    }
    
    /**
     * Exporta la configuración actual de filtros
     * @returns {object} Configuración de filtros
     */
    exportConfig() {
        return { ...this.filters };
    }
    
    /**
     * Importa una configuración de filtros
     * @param {object} config - Configuración a importar
     */
    importConfig(config) {
        Object.entries(config).forEach(([key, value]) => {
            if (key in this.filters) {
                this.setFilter(key, value);
            }
        });
    }
}

// Exportar para uso en timeline_player.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FilterEngine;
}
