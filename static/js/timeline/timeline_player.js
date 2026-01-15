/**
 * 🎬 Timeline Player para AgroTech Histórico
 * Reproductor visual de evolución temporal de datos satelitales
 * 
 * @author AgroTech Team
 * @version 1.0.0
 */

class TimelinePlayer {
    constructor(config) {
        this.config = config;
        this.canvas = document.getElementById(config.canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Datos del timeline
        this.frames = [];
        this.currentIndex = 0;
        this.currentIndice = 'ndvi'; // ndvi, ndmi, savi
        
        // Estado de reproducción
        this.isPlaying = false;
        this.playInterval = null;
        this.playSpeed = 8000; // ms por frame (más tiempo para análisis)
        
        // Caché de imágenes
        this.imageCache = new Map();
        this.loadingImages = new Set(); // 🆕 Tracking de imágenes en proceso de carga
        
        // Elementos del DOM
        this.elements = {};
        
        // Sistema de transiciones
        this.transition = {
            active: false,
            progress: 1,
            fromFrame: null,
            toFrame: null,
            startTime: 0,
            duration: 1200,  // ms de transición (más largo para suavidad)
            animationId: null
        };
        
        // 🆕 Sistema de tooltip
        this.tooltip = {
            element: null,
            visible: false
        };
        
        // 🆕 Sistema de loading con progreso
        this.loading = {
            active: false,
            progress: 0,
            total: 0,
            loaded: 0
        };
        
        // 🆕 FASE 2: Módulos avanzados (se inicializarán después)
        this.playbackController = null;
        this.transitionEngine = null;
        this.filterEngine = null;
        
        // Bind methods (solo los que existen)
        this.play = this.play.bind(this);
        this.pause = this.pause.bind(this);
        this.next = this.next.bind(this);
        this.prev = this.prev.bind(this);
        this.goToFrame = this.goToFrame.bind(this);
        this.changeIndice = this.changeIndice.bind(this);
    }
    
    /**
     * Inicializa el player
     */
    async init() {
        console.log('Inicializando Timeline Player...');
        
        // Configurar canvas
        this.setupCanvas();
        
        // Obtener referencias a elementos del DOM
        this.setupElements();
        
        // Configurar event listeners
        this.setupEventListeners();
        
        // FASE 2: Inicializar módulos avanzados
        this.initAdvancedModules();
        
        // Cargar datos del timeline
        await this.loadTimelineData();
        
        // Renderizar primer frame
        if (this.frames.length > 0) {
            await this.renderFrame(0);
        }
        
        console.log('Timeline Player inicializado correctamente');
    }
    
    /**
     * FASE 2: Inicializa los módulos avanzados
     */
    initAdvancedModules() {
        console.log('Inicializando módulos avanzados...');
        
        try {
            // Verificar si los módulos están disponibles
            if (typeof PlaybackController !== 'undefined') {
                this.playbackController = new PlaybackController(this);
                this.playbackController.init();
                console.log('PlaybackController inicializado');
            }
            
            if (typeof TransitionEngine !== 'undefined') {
                this.transitionEngine = new TransitionEngine(this);
                this.transitionEngine.init();
                console.log('TransitionEngine inicializado');
            }
            
            if (typeof FilterEngine !== 'undefined') {
                this.filterEngine = new FilterEngine(this);
                this.filterEngine.init();
                console.log('FilterEngine inicializado');
            }
            
            console.log('Módulos avanzados inicializados');
        } catch (error) {
            console.error('Error inicializando módulos avanzados:', error);
        }
    }
    
    /**
     * Configura el canvas con dimensiones responsive
     */
    setupCanvas() {
        // Función para redimensionar el canvas
        const resizeCanvas = () => {
            const container = this.canvas.parentElement;
            const rect = container.getBoundingClientRect();
            
            // Establecer dimensiones CSS (sin DPR)
            const cssWidth = rect.width;
            const cssHeight = rect.height;
            
            // Establecer dimensiones reales del canvas (con DPR para nitidez)
            const dpr = window.devicePixelRatio || 1;
            this.canvas.width = cssWidth * dpr;
            this.canvas.height = cssHeight * dpr;
            
            // Ajustar el canvas para que coincida con el tamaño CSS
            this.canvas.style.width = cssWidth + 'px';
            this.canvas.style.height = cssHeight + 'px';
            
            // Escalar el contexto para compensar el DPR
            this.ctx.scale(dpr, dpr);
            
            // Re-renderizar el frame actual si existe
            if (this.frames.length > 0 && this.currentIndex >= 0) {
                const frame = this.frames[this.currentIndex];
                const imageUrl = frame.imagenes[this.currentIndice];
                
                if (imageUrl && this.imageCache.has(imageUrl)) {
                    const img = this.imageCache.get(imageUrl);
                    this.drawImage(img, frame);
                } else {
                    this.drawPlaceholder(frame, 'Redimensionando...');
                }
            } else {
                // Fondo inicial
                this.ctx.fillStyle = '#000';
                this.ctx.fillRect(0, 0, cssWidth, cssHeight);
            }
        };
        
        // Configurar canvas inicial
        resizeCanvas();
        
        // Redimensionar cuando cambie el tamaño de la ventana
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(resizeCanvas, 150);
        });
        
        // Guardar referencia para uso posterior
        this.resizeCanvas = resizeCanvas;
    }
    
    /**
     * Obtiene referencias a elementos del DOM
     */
    setupElements() {
        this.elements = {
            // Controles
            btnPlay: document.getElementById('btn-play'),
            btnPrev: document.getElementById('btn-prev'),
            btnNext: document.getElementById('btn-next'),
            btnFirst: document.getElementById('btn-first'),
            btnLast: document.getElementById('btn-last'),
            slider: document.getElementById('timeline-slider'),
            frameCounter: document.getElementById('frame-counter'),
            
            // Metadata
            iconPeriodo: document.getElementById('icon-periodo'),
            valuePeriodo: document.getElementById('value-periodo'),
            iconIndice: document.getElementById('icon-indice'),
            valueIndice: document.getElementById('value-indice'),
            iconTendencia: document.getElementById('icon-tendencia'),
            valueTendencia: document.getElementById('value-tendencia'),
            iconCalidad: document.getElementById('icon-calidad'),
            valueCalidad: document.getElementById('value-calidad'),
            resumenSimple: document.getElementById('resumen-simple'),
            
            // Selector de índice
            indexButtons: document.querySelectorAll('.index-btn'),
            
            // Botones de descarga
            btnDownloadNdvi: document.getElementById('btn-download-ndvi'),
            btnDownloadNdmi: document.getElementById('btn-download-ndmi'),
            btnDownloadSavi: document.getElementById('btn-download-savi'),
            
            // 🆕 Loading mejorado
            loadingOverlay: document.getElementById('loading-overlay'),
            loadingText: document.getElementById('loading-text'),
            loadingProgress: document.getElementById('loading-progress'),
            loadingPercentage: document.getElementById('loading-percentage'),
            
            // 🆕 Tooltip
            canvasTooltip: document.getElementById('canvas-tooltip')
        };
        
        // Guardar referencia del tooltip
        this.tooltip.element = this.elements.canvasTooltip;
    }
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Controles de reproducción
        this.elements.btnPlay.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });
        
        this.elements.btnPrev.addEventListener('click', this.prev);
        this.elements.btnNext.addEventListener('click', this.next);
        
        this.elements.btnFirst.addEventListener('click', () => {
            this.goToFrame(0);
        });
        
        this.elements.btnLast.addEventListener('click', () => {
            this.goToFrame(this.frames.length - 1);
        });
        
        // Slider
        this.elements.slider.addEventListener('input', (e) => {
            const index = parseInt(e.target.value);
            this.goToFrame(index);
        });
        
        // Selector de índice con feedback visual mejorado
        this.elements.indexButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const indice = e.currentTarget.dataset.index;
                this.changeIndice(indice);
            });
        });
        
        // Botones de descarga
        this.elements.btnDownloadNdvi.addEventListener('click', () => {
            this.downloadVideo('ndvi');
        });
        
        this.elements.btnDownloadNdmi.addEventListener('click', () => {
            this.downloadVideo('ndmi');
        });
        
        this.elements.btnDownloadSavi.addEventListener('click', () => {
            this.downloadVideo('savi');
        });
        
        // Click en canvas para pausar/reanudar
        this.canvas.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });
        
        // 🆕 Atajos de teclado mejorados
        document.addEventListener('keydown', (e) => {
            // Ignorar si el usuario está escribiendo en un input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.key) {
                case ' ':
                case 'Enter':
                    e.preventDefault();
                    if (this.isPlaying) this.pause();
                    else this.play();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.prev();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.next();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    // Cambiar a siguiente índice
                    this.cycleIndice(1);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    // Cambiar a índice anterior
                    this.cycleIndice(-1);
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToFrame(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToFrame(this.frames.length - 1);
                    break;
                case 'Escape':
                    e.preventDefault();
                    if (this.isPlaying) this.pause();
                    break;
                // Teclas numéricas 1, 2, 3 para cambiar índices
                case '1':
                    e.preventDefault();
                    this.changeIndice('ndvi');
                    break;
                case '2':
                    e.preventDefault();
                    this.changeIndice('ndmi');
                    break;
                case '3':
                    e.preventDefault();
                    this.changeIndice('savi');
                    break;
            }
        });
    }
    
    /**
     * Carga datos del timeline desde la API con progreso
     */
    async loadTimelineData() {
        this.showLoading(true, 'Conectando con servidor...', 10);
        
        try {
            console.log('Cargando datos del timeline...');
            this.updateLoadingProgress(1, 5, 'Obteniendo frames...');
            
            const response = await fetch(this.config.apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.updateLoadingProgress(2, 5, 'Procesando datos...');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.mensaje || 'Error desconocido');
            }
            
            this.frames = data.frames || [];
            console.log(`Cargados ${this.frames.length} frames`);
            
            if (this.frames.length === 0) {
                throw new Error('No hay datos disponibles para mostrar');
            }
            
            this.updateLoadingProgress(3, 5, `${this.frames.length} frames listos`);
            
            // Configurar slider
            if (this.elements.slider) {
                this.elements.slider.max = Math.max(0, this.frames.length - 1);
                this.elements.slider.value = 0;
            }
            
            // Actualizar contador
            this.updateFrameCounter();
            
            this.updateLoadingProgress(4, 5, 'Precargando imágenes...');
            
            // Pre-cargar las primeras imágenes con progreso
            await this.preloadImagesWithProgress(0, Math.min(5, this.frames.length));
            
            this.updateLoadingProgress(5, 5, 'Listo');
            
        } catch (error) {
            console.error('Error cargando timeline:', error);
            this.showError('Error cargando datos: ' + error.message);
        } finally {
            setTimeout(() => {
                this.showLoading(false);
            }, 500);
        }
    }
    
    /**
     * Precarga imágenes mostrando progreso
     */
    async preloadImagesWithProgress(startIndex, endIndex) {
        const total = endIndex - startIndex;
        let loaded = 0;
        
        for (let i = startIndex; i < endIndex; i++) {
            if (i >= this.frames.length) break;
            
            const frame = this.frames[i];
            const imageUrl = frame.imagenes[this.currentIndice];
            
            if (imageUrl) {
                await this.loadImage(imageUrl);
                loaded++;
                this.updateLoadingProgress(4 + (loaded / total) * 0.8, 5, 
                    `Precargando imagen ${loaded}/${total}...`);
            }
        }
    }
    
    /**
     * Renderiza un frame específico
     */
    async renderFrame(index) {
        if (index < 0 || index >= this.frames.length) {
            console.warn('Índice de frame fuera de rango:', index);
            return;
        }
        
        const previousFrame = this.frames[this.currentIndex];
        this.currentIndex = index;
        const frame = this.frames[index];
        
        // Actualizar slider sin disparar evento
        if (this.elements.slider) {
            this.elements.slider.value = index;
        }
        
        // Actualizar contador
        this.updateFrameCounter();
        
        // Actualizar metadata
        this.updateMetadata(frame);
        
        // Obtener URL de imagen según índice actual
        const imageUrl = frame.imagenes[this.currentIndice];
        
        console.log(`Frame ${index} - ${this.currentIndice.toUpperCase()} URL:`, imageUrl);
        
        if (imageUrl) {
            // Cargar y renderizar imagen
            const img = await this.loadImage(imageUrl);
            if (img) {
                this.drawImage(img, frame);
            } else {
                this.drawPlaceholder(frame, 'Error cargando imagen');
            }
        } else {
            this.drawPlaceholder(frame, 'No disponible por nubosidad');
        }
        
        // Pre-cargar imágenes adyacentes
        this.preloadImages(index - 1, index + 2);
    }
    
    /**
     * Dibuja una imagen en el canvas (responsive con mejor aspect ratio)
     */
    drawImage(img, frame) {
        // Usar dimensiones CSS del canvas (no las del canvas interno que están escaladas por DPR)
        const rect = this.canvas.getBoundingClientRect();
        const canvasWidth = rect.width;
        const canvasHeight = rect.height;
        
        // Limpiar canvas
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        // Calcular dimensiones para CONTAIN (mostrar imagen completa sin recorte)
        // Reducir para dar espacio al overlay y crear un marco visual limpio
        const imgRatio = img.width / img.height;
        const canvasRatio = canvasWidth / canvasHeight;
        const scaleFactor = 0.88; // Reducir 12% para marco visual limpio
        
        let drawWidth, drawHeight, offsetX, offsetY;
        
        if (imgRatio > canvasRatio) {
            // Imagen más ancha - ajustar por anchura
            drawWidth = canvasWidth * scaleFactor;
            drawHeight = (canvasWidth * scaleFactor) / imgRatio;
            offsetX = (canvasWidth - drawWidth) / 2;
            offsetY = (canvasHeight - drawHeight) / 2;
        } else {
            // Imagen más alta - ajustar por altura
            drawHeight = canvasHeight * scaleFactor;
            drawWidth = (canvasHeight * scaleFactor) * imgRatio;
            offsetX = (canvasWidth - drawWidth) / 2;
            offsetY = (canvasHeight - drawHeight) / 2;
        }
        
        // Dibujar imagen
        this.ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
        
        // Overlay con información
        this.drawOverlay(frame, canvasWidth, canvasHeight);
    }
    
    /**
     * Dibuja overlay con información del frame (responsive y legible)
     */
    drawOverlay(frame, canvasWidth, canvasHeight) {
        const clasificacion = frame.clasificaciones[this.currentIndice];
        if (!clasificacion) return;
        
        // Tamaños de fuente balanceados para óptima legibilidad
        const baseFontSize = Math.max(11, canvasWidth / 85);
        const periodFontSize = baseFontSize * 1.0; // Período legible
        const valueFontSize = baseFontSize * 1.4; // Valor del índice destacado
        const labelFontSize = baseFontSize * 0.95; // Etiqueta clara
        const smallFontSize = baseFontSize * 0.75; // Descripción
        
        // Altura del overlay compacta pero legible
        const overlayHeight = Math.min(50, canvasHeight * 0.09);
        
        // Fondo SÓLIDO con opacidad adecuada
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(0, canvasHeight - overlayHeight, canvasWidth, overlayHeight);
        
        // Padding balanceado
        const padding = Math.max(10, canvasWidth * 0.012);
        const lineHeight = baseFontSize * 1.2;
        
        // IZQUIERDA: Período y Valor del índice EN UNA SOLA LÍNEA
        let yPos = canvasHeight - overlayHeight / 2;
        
        // Texto del período + valor del índice juntos
        this.ctx.fillStyle = '#fff';
        this.ctx.font = `600 ${periodFontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Arial`;
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(frame.periodo_texto, padding, yPos);
        
        // Valor del índice al lado del período
        const valorIndice = frame[this.currentIndice].promedio;
        if (valorIndice !== null) {
            const periodoWidth = this.ctx.measureText(frame.periodo_texto).width;
            this.ctx.font = `700 ${valueFontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Arial`;
            this.ctx.fillStyle = clasificacion.color;
            const texto = ` ${this.currentIndice.toUpperCase()}: ${valorIndice.toFixed(3)}`;
            this.ctx.fillText(texto, padding + periodoWidth + 10, yPos);
        }
        
        // DERECHA: Estado EN UNA SOLA LÍNEA
        this.ctx.textAlign = 'right';
        this.ctx.textBaseline = 'middle';
        
        // Estado (etiqueta + descripción juntos)
        this.ctx.font = `600 ${labelFontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Arial`;
        this.ctx.fillStyle = clasificacion.color;
        const textoEstado = `${clasificacion.etiqueta} - ${clasificacion.descripcion}`;
        this.ctx.fillText(textoEstado, canvasWidth - padding, yPos);
    }
    
    /**
     * Dibuja placeholder cuando no hay imagen - Visualización con colores según índice (responsive)
     */
    drawPlaceholder(frame, mensaje) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasWidth = rect.width;
        const canvasHeight = rect.height;
        
        // Calcular tamaños responsivos
        const iconSize = Math.max(60, canvasWidth / 10);
        const valueFontSize = Math.max(24, canvasWidth / 20);
        const labelFontSize = Math.max(16, canvasWidth / 35);
        const borderRadius = Math.max(10, canvasWidth / 60);
        
        // Limpiar canvas
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        // Obtener clasificación y valor del índice actual
        const clasificacion = frame.clasificaciones[this.currentIndice];
        const valorIndice = frame[this.currentIndice].promedio;
        
        if (clasificacion && valorIndice !== null) {
            // Obtener color base (con transición si está activa)
            let baseColor = clasificacion.color;
            let currentValor = valorIndice;
            
            // Si hay transición activa, interpolar
            if (this.transition.active && this.transition.fromFrame) {
                const fromClasif = this.transition.fromFrame.clasificaciones[this.currentIndice];
                const fromValor = this.transition.fromFrame[this.currentIndice].promedio;
                
                if (fromClasif && fromValor !== null) {
                    baseColor = this.interpolateColorHex(fromClasif.color, clasificacion.color, this.transition.progress);
                    currentValor = fromValor + (valorIndice - fromValor) * this.transition.progress;
                }
            }
            
            // Crear gradiente basado en el color de clasificación
            const gradient = this.ctx.createRadialGradient(
                canvasWidth / 2, canvasHeight / 2, 0,
                canvasWidth / 2, canvasHeight / 2, Math.max(canvasWidth, canvasHeight) / 2
            );
            gradient.addColorStop(0, this.hexToRgba(baseColor, 0.8));
            gradient.addColorStop(0.5, this.hexToRgba(baseColor, 0.5));
            gradient.addColorStop(1, this.hexToRgba(baseColor, 0.2));
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // Dibujar área de parcela representativa (rectángulo con bordes redondeados)
            const parcelaWidth = canvasWidth * 0.7;
            const parcelaHeight = canvasHeight * 0.6;
            const parcelaX = (canvasWidth - parcelaWidth) / 2;
            const parcelaY = (canvasHeight - parcelaHeight) / 2;
            
            // Sombra de parcela
            this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
            this.ctx.shadowBlur = Math.max(10, canvasWidth / 60);
            this.ctx.shadowOffsetX = 0;
            this.ctx.shadowOffsetY = Math.max(5, canvasWidth / 120);
            
            // Parcela con color del índice
            this.ctx.fillStyle = this.hexToRgba(baseColor, 0.9);
            this.roundRect(parcelaX, parcelaY, parcelaWidth, parcelaHeight, borderRadius);
            this.ctx.fill();
            
            // Resetear sombra
            this.ctx.shadowColor = 'transparent';
            this.ctx.shadowBlur = 0;
            
            // Borde de parcela
            this.ctx.strokeStyle = '#fff';
            this.ctx.lineWidth = Math.max(2, canvasWidth / 400);
            this.roundRect(parcelaX, parcelaY, parcelaWidth, parcelaHeight, borderRadius);
            this.ctx.stroke();
            
            // Icono del estado en el centro
            this.ctx.font = `${iconSize}px Arial`;
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(clasificacion.icono, canvasWidth / 2, canvasHeight / 2 - iconSize / 4);
            
            // Valor del índice prominente (usar valor interpolado si hay transición)
            this.ctx.font = `bold ${valueFontSize}px Arial`;
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(
                `${this.currentIndice.toUpperCase()}: ${currentValor.toFixed(3)}`,
                canvasWidth / 2,
                canvasHeight / 2 + iconSize / 2 + 20
            );
            
            // Etiqueta del estado
            this.ctx.font = `bold ${labelFontSize}px Arial`;
            this.ctx.fillText(clasificacion.etiqueta, canvasWidth / 2, canvasHeight / 2 + iconSize / 2 + 20 + labelFontSize + 10);
            
        } else {
            // Fallback: gradiente genérico verde
            const gradient = this.ctx.createLinearGradient(0, 0, canvasWidth, canvasHeight);
            gradient.addColorStop(0, '#2e8b57');
            gradient.addColorStop(1, '#1a4d2e');
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // Icono grande
            this.ctx.font = `${iconSize}px Arial`;
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('🛰️', canvasWidth / 2, canvasHeight / 2 - iconSize / 3);
            
            // Mensaje
            this.ctx.font = `bold ${labelFontSize}px Arial`;
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(mensaje, canvasWidth / 2, canvasHeight / 2 + iconSize / 3);
        }
        
        // Overlay con período (siempre mostrar)
        this.drawOverlay(frame, canvasWidth, canvasHeight);
    }
    
    /**
     * Dibuja rectángulo con bordes redondeados
     */
    roundRect(x, y, width, height, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + width - radius, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.ctx.lineTo(x + width, y + height - radius);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.ctx.lineTo(x + radius, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.closePath();
    }
    
    /**
     * Convierte color hex a rgba
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    /**
     * Carga una imagen (con caché)
     */
    async loadImage(url) {
        // Verificar caché
        if (this.imageCache.has(url)) {
            return this.imageCache.get(url);
        }
        
        // Evitar cargas duplicadas
        if (this.loadingImages.has(url)) {
            return new Promise((resolve) => {
                const checkInterval = setInterval(() => {
                    if (this.imageCache.has(url)) {
                        clearInterval(checkInterval);
                        resolve(this.imageCache.get(url));
                    }
                }, 100);
            });
        }
        
        this.loadingImages.add(url);
        
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                this.imageCache.set(url, img);
                this.loadingImages.delete(url);
                console.log('Imagen cargada:', url);
                resolve(img);
            };
            
            img.onerror = () => {
                this.loadingImages.delete(url);
                console.error('Error cargando imagen:', url);
                resolve(null);
            };
            
            img.src = url;
        });
    }
    
    /**
     * Pre-carga imágenes
     */
    preloadImages(startIndex, endIndex) {
        for (let i = Math.max(0, startIndex); i < Math.min(endIndex, this.frames.length); i++) {
            const frame = this.frames[i];
            const imageUrl = frame.imagenes[this.currentIndice];
            
            if (imageUrl && !this.imageCache.has(imageUrl)) {
                this.loadImage(imageUrl);
            }
        }
    }
    
    /**
     * Actualiza metadata en el panel
     */
    updateMetadata(frame) {
        // Validar que el frame existe
        if (!frame) {
            console.warn('Frame no válido para actualizar metadata');
            return;
        }
        
        // Período
        this.elements.valuePeriodo.textContent = frame.periodo_texto;
        
        // Índice actual
        const clasificacion = frame.clasificaciones[this.currentIndice];
        if (clasificacion) {
            this.elements.iconIndice.textContent = clasificacion.icono;
            this.elements.valueIndice.textContent = frame[this.currentIndice].promedio?.toFixed(3) || '-';
        }
        
        // Tendencia (Cambio vs mes anterior)
        if (frame.comparacion && frame.comparacion[this.currentIndice]) {
            const comp = frame.comparacion[this.currentIndice];
            
            // Determinar mensaje claro para agricultores
            let mensaje = '';
            let iconoMensaje = comp.icono;
            
            if (comp.tendencia === 'mejora') {
                mensaje = 'Mejoró';
                iconoMensaje = '📈';
            } else if (comp.tendencia === 'deterioro') {
                mensaje = 'Disminuyó';
                iconoMensaje = '📉';
            } else {
                mensaje = 'Sin cambios significativos';
                iconoMensaje = '➡️';
            }
            
            this.elements.iconTendencia.textContent = iconoMensaje;
            this.elements.valueTendencia.textContent = `${mensaje} (${comp.porcentaje >= 0 ? '+' : ''}${comp.porcentaje.toFixed(1)}%)`;
            this.elements.valueTendencia.style.color = comp.tendencia === 'mejora' ? '#28a745' : 
                                                       comp.tendencia === 'deterioro' ? '#dc3545' : '#6c757d';
        } else {
            this.elements.iconTendencia.textContent = '📋';
            this.elements.valueTendencia.textContent = 'Primer registro disponible';
            this.elements.valueTendencia.style.color = '#6c757d';
        }
        
        // Calidad de datos
        const calidad = frame.calidad_datos;
        if (calidad) {
            this.elements.valueCalidad.textContent = calidad.charAt(0).toUpperCase() + calidad.slice(1);
            
            // Icono y color según calidad
            if (calidad === 'excelente') {
                this.elements.iconCalidad.textContent = '⭐⭐⭐';
                this.elements.valueCalidad.style.color = '#28a745';
            } else if (calidad === 'buena') {
                this.elements.iconCalidad.textContent = '⭐⭐';
                this.elements.valueCalidad.style.color = '#17a2b8';
            } else if (calidad === 'aceptable') {
                this.elements.iconCalidad.textContent = '⭐';
                this.elements.valueCalidad.style.color = '#ffc107';
            } else {
                this.elements.iconCalidad.textContent = '⚠️';
                this.elements.valueCalidad.style.color = '#dc3545';
            }
        } else {
            this.elements.iconCalidad.textContent = '❓';
            this.elements.valueCalidad.textContent = 'Sin datos';
            this.elements.valueCalidad.style.color = '#6c757d';
        }
        
        // Resumen simple
        this.elements.resumenSimple.textContent = frame.resumen_simple;
    }
    
    /**
     * Actualiza contador de frames
     */
    updateFrameCounter() {
        if (!this.elements.frameCounter) return;
        
        const current = this.currentIndex + 1;
        const total = this.frames.length;
        
        this.elements.frameCounter.textContent = `${current} / ${total}`;
    }
    
    /**
     * FASE 2: Actualiza la UI para un frame sin renderizar
     */
    updateUIForFrame(index) {
        if (index < 0 || index >= this.frames.length) return;
        
        this.currentIndex = index;
        
        // Actualizar slider
        if (this.elements.slider) {
            this.elements.slider.value = index;
        }
        
        // Actualizar contador
        this.updateFrameCounter();
        
        // Actualizar metadata si el frame existe
        const frame = this.frames[index];
        if (frame) {
            this.updateMetadata(frame);
        }
    }
    
    /**
     * Reproduce el timeline
     */
    play() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        this.elements.btnPlay.innerHTML = '<i class="fas fa-pause"></i>';
        
        this.playInterval = setInterval(() => {
            if (this.currentIndex >= this.frames.length - 1) {
                // Fin del timeline, reiniciar
                this.goToFrame(0);
            } else {
                this.next();
            }
        }, this.playSpeed);
    }
    
    /**
     * Pausa la reproducción
     */
    pause() {
        if (!this.isPlaying) return;
        
        this.isPlaying = false;
        this.elements.btnPlay.innerHTML = '<i class="fas fa-play"></i>';
        
        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
    }
    
    /**
     * Frame siguiente
     */
    next() {
        const nextIndex = Math.min(this.currentIndex + 1, this.frames.length - 1);
        this.goToFrame(nextIndex);
    }
    
    /**
     * Frame anterior
     */
    prev() {
        const prevIndex = Math.max(this.currentIndex - 1, 0);
        this.goToFrame(prevIndex);
    }
    
    /**
     * Ir a un frame específico
     */
    /**
     * Navega a un frame específico con transiciones opcionales
     */
    async goToFrame(index) {
        if (index === this.currentIndex) return;
        
        // Validar índice
        if (index < 0 || index >= this.frames.length) {
            console.warn('Índice de frame fuera de rango:', index);
            return;
        }
        
        // Si TransitionEngine está disponible y habilitado, usar transición
        if (this.transitionEngine && this.transitionEngine.enabled && this.frames.length > 0) {
            const fromFrame = this.frames[this.currentIndex];
            const toFrame = this.frames[index];
            
            if (fromFrame && toFrame) {
                // Realizar transición (NO actualizar currentIndex aquí, lo hace renderFrame)
                try {
                    // La transición internamente llamará a renderFrame al finalizar
                    await this.transitionEngine.transition(fromFrame, toFrame);
                } catch (error) {
                    console.error('Error en transición, renderizando directo:', error);
                    await this.renderFrame(index);
                }
                return;
            }
        }
        
        // Renderizado directo sin transición
        await this.renderFrame(index);
    }
    
    /**
     * Cambia el índice activo con feedback visual
     */
    changeIndice(indice) {
        if (this.currentIndice === indice) return;
        
        const oldIndice = this.currentIndice;
        this.currentIndice = indice;
        
        // Feedback visual: Animación de botones
        this.elements.indexButtons.forEach(btn => {
            if (btn.dataset.index === indice) {
                btn.classList.add('active');
                btn.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    btn.style.transform = '';
                }, 150);
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Mensaje temporal en el resumen
        const oldText = this.elements.resumenSimple.textContent;
        this.elements.resumenSimple.textContent = `Cambiando a ${indice.toUpperCase()}...`;
        this.elements.resumenSimple.style.color = '#3b82f6';
        
        // Fade out/in del canvas durante el cambio
        this.canvas.style.opacity = '0.6';
        this.canvas.style.transition = 'opacity 0.3s ease';
        
        setTimeout(() => {
            // Re-renderizar frame actual con nuevo índice
            this.renderFrame(this.currentIndex);
            
            // Restaurar opacidad
            this.canvas.style.opacity = '1';
            
            // Restaurar texto del resumen después de actualización
            setTimeout(() => {
                this.elements.resumenSimple.style.color = '';
            }, 500);
        }, 200);
        
        console.log(`Índice cambiado: ${oldIndice.toUpperCase()} → ${indice.toUpperCase()}`);
    }
    
    /**
     * Cambia al siguiente o anterior índice (para flechas arriba/abajo)
     */
    cycleIndice(direction) {
        const indices = ['ndvi', 'ndmi', 'savi'];
        const currentIdx = indices.indexOf(this.currentIndice);
        const newIdx = (currentIdx + direction + indices.length) % indices.length;
        this.changeIndice(indices[newIdx]);
    }
    
    /**
     * Muestra loading overlay con progreso
     */
    showLoading(show, text = 'Cargando timeline...', progress = 0) {
        const overlay = this.elements.loadingOverlay;
        const textEl = this.elements.loadingText;
        const progressBar = this.elements.loadingProgress;
        const percentageEl = this.elements.loadingPercentage;
        
        if (show) {
            if (overlay) overlay.style.display = 'flex';
            if (textEl) textEl.textContent = text;
            if (progressBar) progressBar.style.width = progress + '%';
            if (percentageEl) percentageEl.textContent = Math.round(progress) + '%';
            this.loading.active = true;
        } else {
            if (overlay) overlay.style.display = 'none';
            this.loading.active = false;
        }
    }
    
    /**
     * Actualiza el progreso del loading
     */
    updateLoadingProgress(loaded, total, text = null) {
        if (!this.loading.active) return;
        
        const progress = (loaded / total) * 100;
        const progressBar = this.elements.loadingProgress;
        const percentageEl = this.elements.loadingPercentage;
        const textEl = this.elements.loadingText;
        
        if (progressBar) progressBar.style.width = progress + '%';
        if (percentageEl) percentageEl.textContent = Math.round(progress) + '%';
        if (text && textEl) textEl.textContent = text;
        
        this.loading.loaded = loaded;
        this.loading.total = total;
        this.loading.progress = progress;
    }
    
    /**
     * Muestra un mensaje de error
     */
    showError(mensaje) {
        console.error(mensaje);
        
        if (this.loading.active && this.elements.loadingText) {
            this.elements.loadingText.textContent = 'Error: ' + mensaje;
            this.elements.loadingText.style.color = '#ef4444';
            
            if (this.elements.loadingProgress) {
                this.elements.loadingProgress.parentElement.style.display = 'none';
            }
            
            setTimeout(() => {
                this.showLoading(false);
            }, 5000);
        }
    }
    
    /**
     * Descarga video del timeline en alta calidad
     * La generación se realiza en backend usando FFmpeg
     * 
     * @param {string} indice - Índice a exportar (ndvi, ndmi, savi)
     */
    async downloadVideo(indice) {
        console.log(`Iniciando descarga de video para índice: ${indice.toUpperCase()}`);
        
        // Mostrar loading
        this.showLoading(true, 'Generando video de alta calidad...', 10);
        
        try {
            // Obtener parcela_id de la URL
            const parcelaId = this.config.apiUrl.match(/parcelas\/(\d+)\//)[1];
            
            // Construir URL de exportación
            const exportUrl = `/informes/parcelas/${parcelaId}/timeline/exportar-video/?indice=${indice}`;
            
            this.updateLoadingProgress(2, 5, 'Procesando frames...');
            
            // Realizar petición de descarga
            const response = await fetch(exportUrl);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.mensaje || `HTTP ${response.status}`);
            }
            
            this.updateLoadingProgress(4, 5, 'Descargando video...');
            
            // Obtener blob del video
            const blob = await response.blob();
            
            // Crear URL temporal y descargar
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `timeline_${indice}_${new Date().getTime()}.mp4`;
            document.body.appendChild(a);
            a.click();
            
            // Limpiar
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.updateLoadingProgress(5, 5, 'Completado');
            
            console.log(`Video descargado exitosamente: ${indice.toUpperCase()}`);
            
            // Mensaje de éxito
            setTimeout(() => {
                this.showLoading(false);
                alert('✅ Video descargado exitosamente en alta calidad');
            }, 500);
            
        } catch (error) {
            console.error('Error descargando video:', error);
            this.showError(`Error al generar video: ${error.message}`);
            
            setTimeout(() => {
                this.showLoading(false);
            }, 3000);
        }
    }
    
    /**
     * FASE 3: Interpolación de colores (Utilidad para transiciones)
     */
    interpolateColorHex(color1, color2, progress) {
        // Extraer componentes RGB
        const r1 = parseInt(color1.slice(1, 3), 16);
        const g1 = parseInt(color1.slice(3, 5), 16);
        const b1 = parseInt(color1.slice(5, 7), 16);
        
        const r2 = parseInt(color2.slice(1, 3), 16);
        const g2 = parseInt(color2.slice(3, 5), 16);
        const b2 = parseInt(color2.slice(5, 7), 16);
        
        // Interpolar
        const r = Math.round(r1 + (r2 - r1) * progress);
        const g = Math.round(g1 + (g2 - g1) * progress);
        const b = Math.round(b1 + (b2 - b1) * progress);
        
        // Convertir de vuelta a hex
        return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }
}

// Hacer disponible globalmente
window.TimelinePlayer = TimelinePlayer;

