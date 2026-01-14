/**
 * 🎨 Motor de Transiciones Suaves
 * Gestiona transiciones fluidas entre frames usando interpolación
 * 
 * @module TransitionEngine
 * @author AgroTech Team
 * @version 1.0.0
 */

class TransitionEngine {
    constructor(player) {
        this.player = player;
        
        // Configuración de transiciones
        this.duration = 600; // ms (600ms = transición suave pero rápida)
        this.enabled = true;
        this.currentType = 'fade'; // 'fade', 'slide', 'dissolve', 'none'
        
        // Estado de transición actual
        this.active = false;
        this.progress = 0;
        this.startTime = 0;
        this.animationId = null;
        
        // Frames de la transición
        this.fromFrame = null;
        this.toFrame = null;
        this.fromImage = null;
        this.toImage = null;
        
        // Canvas temporal para composición
        this.offscreenCanvas = document.createElement('canvas');
        this.offscreenCtx = this.offscreenCanvas.getContext('2d');
        
        // Funciones de easing
        this.easingFunctions = {
            linear: t => t,
            easeInOut: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
            easeOut: t => t * (2 - t),
            easeIn: t => t * t,
            cubic: t => t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
        };
        
        this.currentEasing = this.easingFunctions.easeInOut;
        
        console.log('TransitionEngine inicializado');
    }
    
    /**
     * Inicializa el motor de transiciones
     */
    init() {
        this.setupOffscreenCanvas();
        this.createTransitionControls();
    }
    
    /**
     * Configura el canvas offscreen para composición
     */
    setupOffscreenCanvas() {
        const mainCanvas = this.player.canvas;
        this.offscreenCanvas.width = mainCanvas.width;
        this.offscreenCanvas.height = mainCanvas.height;
    }
    
    /**
     * Crea controles de transición en la UI
     */
    createTransitionControls() {
        // Buscar panel de configuración o crear uno nuevo
        let configPanel = document.getElementById('timeline-config-panel');
        
        if (!configPanel) {
            // Crear panel de configuración
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
                    <div class="config-section" id="transition-config"></div>
                </div>
            `;
            container.appendChild(configPanel);
            
            // Toggle panel
            document.getElementById('toggle-config-panel').addEventListener('click', () => {
                configPanel.classList.toggle('collapsed');
            });
        }
        
        // Agregar controles de transición
        const transitionConfig = document.getElementById('transition-config') || 
                                 configPanel.querySelector('.config-content');
        
        if (transitionConfig) {
            const transitionHTML = `
                <div class="config-group">
                    <label class="config-label">
                        <input type="checkbox" id="transitions-enabled" ${this.enabled ? 'checked' : ''}>
                        <span>Transiciones suaves</span>
                    </label>
                </div>
                <div class="config-group ${this.enabled ? '' : 'disabled'}" id="transition-options">
                    <label>Tipo de transición:</label>
                    <select id="transition-type" class="form-control form-control-sm">
                        <option value="fade">Fade (Fundido)</option>
                        <option value="slide">Slide (Deslizamiento)</option>
                        <option value="dissolve">Dissolve (Disolución)</option>
                        <option value="none">Sin transición</option>
                    </select>
                    
                    <label>Duración:</label>
                    <div class="slider-group">
                        <input type="range" id="transition-duration" 
                               min="200" max="2000" step="100" value="${this.duration}">
                        <span id="transition-duration-value">${this.duration}ms</span>
                    </div>
                </div>
            `;
            
            transitionConfig.innerHTML += transitionHTML;
            
            this.setupTransitionEventListeners();
        }
    }
    
    /**
     * Configura event listeners para controles de transición
     */
    setupTransitionEventListeners() {
        const enabledCheckbox = document.getElementById('transitions-enabled');
        const typeSelect = document.getElementById('transition-type');
        const durationSlider = document.getElementById('transition-duration');
        const durationValue = document.getElementById('transition-duration-value');
        const optionsGroup = document.getElementById('transition-options');            if (enabledCheckbox) {
            enabledCheckbox.addEventListener('change', (e) => {
                this.enabled = e.target.checked;
                optionsGroup?.classList.toggle('disabled', !this.enabled);
                console.log(`Transiciones: ${this.enabled ? 'ON' : 'OFF'}`);
            });
        }
        
        if (typeSelect) {
            typeSelect.addEventListener('change', (e) => {
                this.currentType = e.target.value;
                console.log(`Tipo de transición: ${this.currentType}`);
            });
        }
        
        if (durationSlider && durationValue) {
            durationSlider.addEventListener('input', (e) => {
                this.duration = parseInt(e.target.value);
                durationValue.textContent = `${this.duration}ms`;
            });
        }
    }
    
    /**
     * Ejecuta una transición entre dos frames
     * @param {object} fromFrame - Frame de origen
     * @param {object} toFrame - Frame de destino
     * @returns {Promise} Promesa que se resuelve cuando termina la transición
     */
    async transition(fromFrame, toFrame) {
        // Si las transiciones están deshabilitadas, renderizar directamente
        if (!this.enabled || this.currentType === 'none') {
            return this.renderFrameDirectly(toFrame);
        }
        
        // Cancelar transición anterior si existe
        if (this.active) {
            this.cancelTransition();
        }
        
        // Verificar que fromFrame y toFrame son válidos
        if (!fromFrame || !toFrame) {
            console.error('Frames inválidos para transición');
            return this.renderFrameDirectly(toFrame);
        }
        
        // Verificar que tienen imágenes disponibles
        const fromImageUrl = fromFrame.imagenes[this.player.currentIndice];
        const toImageUrl = toFrame.imagenes[this.player.currentIndice];
        
        if (!fromImageUrl || !toImageUrl) {
            console.warn('Una o ambas imágenes no disponibles, renderizando directo');
            return this.renderFrameDirectly(toFrame);
        }
        
        const fromIndex = this.player.frames.indexOf(fromFrame);
        const toIndex = this.player.frames.indexOf(toFrame);
        console.log(`Iniciando transición ${this.currentType}: Frame ${fromIndex} -> ${toIndex}`);
        
        // Guardar frames
        this.fromFrame = fromFrame;
        this.toFrame = toFrame;
        
        // Cargar imágenes
        try {
            [this.fromImage, this.toImage] = await Promise.all([
                this.loadImage(fromFrame),
                this.loadImage(toFrame)
            ]);
        } catch (error) {
            console.error('❌ Error cargando imágenes para transición:', error);
            return this.renderFrameDirectly(toFrame);
        }
        
        // Iniciar animación
        this.active = true;
        this.progress = 0;
        this.startTime = performance.now();
        
        return new Promise((resolve) => {
            this.animate(resolve);
        });
    }
    
    /**
     * Carga una imagen desde el frame
     * @param {object} frame - Frame con URL de imagen
     * @returns {Promise<Image>} Promesa con imagen cargada
     */
    loadImage(frame) {
        return new Promise((resolve, reject) => {
            // Obtener URL según el índice actual del player
            const imageUrl = frame.imagenes[this.player.currentIndice];
            
            if (!imageUrl) {
                reject(new Error('No hay URL de imagen disponible'));
                return;
            }
            
            // Verificar si ya está en caché
            if (this.player.imageCache.has(imageUrl)) {
                resolve(this.player.imageCache.get(imageUrl));
                return;
            }
            
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => {
                this.player.imageCache.set(imageUrl, img);
                resolve(img);
            };
            img.onerror = (error) => {
                console.error('Error cargando imagen:', imageUrl);
                reject(error);
            };
            img.src = imageUrl;
        });
    }
    
    /**
     * Renderiza frame directamente sin transición
     * @param {object} frame - Frame a renderizar
     */
    async renderFrameDirectly(frame) {
        // Buscar el índice del frame en el array de frames del player
        const frameIndex = this.player.frames.findIndex(f => f === frame);
        
        if (frameIndex === -1) {
            console.error('Frame no encontrado en el array de frames');
            return;
        }
        
        return this.player.renderFrame(frameIndex);
    }
    
    /**
     * Anima la transición
     * @param {function} resolve - Callback al terminar
     */
    animate(resolve) {
        const now = performance.now();
        const elapsed = now - this.startTime;
        
        // Calcular progreso (0 a 1)
        this.progress = Math.min(elapsed / this.duration, 1);
        const easedProgress = this.currentEasing(this.progress);
        
        // Renderizar frame de transición
        this.renderTransitionFrame(easedProgress);
        
        // Continuar animación o finalizar
        if (this.progress < 1) {
            this.animationId = requestAnimationFrame(() => this.animate(resolve));
        } else {
            this.finishTransition();
            resolve();
        }
    }
    
    /**
     * Renderiza un frame de la transición
     * @param {number} progress - Progreso de la transición (0-1)
     */
    renderTransitionFrame(progress) {
        const ctx = this.player.ctx;
        const canvas = this.player.canvas;
        
        // Limpiar canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        switch (this.currentType) {
            case 'fade':
                this.renderFadeTransition(progress);
                break;
            case 'slide':
                this.renderSlideTransition(progress);
                break;
            case 'dissolve':
                this.renderDissolveTransition(progress);
                break;
            default:
                this.renderFadeTransition(progress);
        }
    }
    
    /**
     * Renderiza transición tipo fade (fundido)
     * @param {number} progress - Progreso (0-1)
     */
    renderFadeTransition(progress) {
        const ctx = this.player.ctx;
        
        // Dibujar imagen origen con opacidad decreciente
        ctx.globalAlpha = 1 - progress;
        ctx.drawImage(this.fromImage, 0, 0, this.player.canvas.width, this.player.canvas.height);
        
        // Dibujar imagen destino con opacidad creciente
        ctx.globalAlpha = progress;
        ctx.drawImage(this.toImage, 0, 0, this.player.canvas.width, this.player.canvas.height);
        
        // Restaurar opacidad
        ctx.globalAlpha = 1;
    }
    
    /**
     * Renderiza transición tipo slide (deslizamiento)
     * @param {number} progress - Progreso (0-1)
     */
    renderSlideTransition(progress) {
        const ctx = this.player.ctx;
        const width = this.player.canvas.width;
        const height = this.player.canvas.height;
        
        const offset = width * progress;
        
        // Dibujar imagen origen saliendo por la izquierda
        ctx.drawImage(this.fromImage, -offset, 0, width, height);
        
        // Dibujar imagen destino entrando por la derecha
        ctx.drawImage(this.toImage, width - offset, 0, width, height);
    }
    
    /**
     * Renderiza transición tipo dissolve (disolución con ruido)
     * @param {number} progress - Progreso (0-1)
     */
    renderDissolveTransition(progress) {
        const ctx = this.player.ctx;
        const offCtx = this.offscreenCtx;
        const width = this.player.canvas.width;
        const height = this.player.canvas.height;
        
        // Dibujar imagen origen en offscreen
        offCtx.clearRect(0, 0, width, height);
        offCtx.drawImage(this.fromImage, 0, 0, width, height);
        
        // Obtener datos de píxeles
        const imageData = offCtx.getImageData(0, 0, width, height);
        const data = imageData.data;
        
        // Dibujar imagen destino en offscreen
        offCtx.clearRect(0, 0, width, height);
        offCtx.drawImage(this.toImage, 0, 0, width, height);
        const toImageData = offCtx.getImageData(0, 0, width, height);
        const toData = toImageData.data;
        
        // Mezclar píxeles con ruido
        for (let i = 0; i < data.length; i += 4) {
            const noise = Math.random();
            if (noise < progress) {
                data[i] = toData[i];
                data[i + 1] = toData[i + 1];
                data[i + 2] = toData[i + 2];
                data[i + 3] = toData[i + 3];
            }
        }
        
        // Dibujar resultado
        ctx.putImageData(imageData, 0, 0);
    }
    
    /**
     * Finaliza la transición
     */
    finishTransition() {
        this.active = false;
        this.progress = 1;
        
        // Buscar el índice del frame de destino
        const toFrameIndex = this.player.frames.findIndex(f => f === this.toFrame);
        
        if (toFrameIndex !== -1) {
            // Actualizar currentIndex del player
            this.player.currentIndex = toFrameIndex;
            
            // Actualizar UI completa
            if (this.player.elements.slider) {
                this.player.elements.slider.value = toFrameIndex;
            }
            this.player.updateFrameCounter();
            this.player.updateMetadata(this.toFrame);
            
            // Asegurar que se dibuja el frame final completo con overlay
            this.player.drawImage(this.toImage, this.toFrame);
        } else {
            // Fallback: solo dibujar la imagen
            const ctx = this.player.ctx;
            ctx.globalAlpha = 1;
            ctx.drawImage(this.toImage, 0, 0, this.player.canvas.width, this.player.canvas.height);
        }
        
        console.log('Transición completada');
    }
    
    /**
     * Cancela la transición actual
     */
    cancelTransition() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this.active = false;
    }
    
    /**
     * Habilita/deshabilita transiciones
     * @param {boolean} enabled - Estado deseado
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        const checkbox = document.getElementById('transitions-enabled');
        if (checkbox) {
            checkbox.checked = enabled;
        }
    }
}

// Exportar para uso en timeline_player.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TransitionEngine;
}
