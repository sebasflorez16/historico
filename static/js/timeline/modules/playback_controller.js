/**
 * 🎬 Controlador de Velocidad de Reproducción
 * Gestiona las velocidades variables del timeline (0.5x, 1x, 2x, 4x)
 * 
 * @module PlaybackController
 * @author AgroTech Team
 * @version 1.0.0
 */

class PlaybackController {
    constructor(player) {
        this.player = player;
        
        // Velocidades disponibles (multiplicadores)
        this.speeds = [
            { value: 0.5, label: '0.5x (Lento)', interval: 16000 },
            { value: 1, label: '1x (Normal)', interval: 8000 },
            { value: 2, label: '2x (Rápido)', interval: 4000 },
            { value: 4, label: '4x (Muy rápido)', interval: 2000 }
        ];
        
        this.currentSpeedIndex = 1; // 1x por defecto
        this.speedIndicator = null;
        
        console.log('PlaybackController inicializado');
    }
    
    /**
     * Inicializa el controlador de velocidad
     */
    init() {
        this.createSpeedControl();
        this.updateSpeedIndicator();
    }
    
    /**
     * Crea el control de velocidad en la UI
     */
    createSpeedControl() {
        const toolbar = document.querySelector('.timeline-controls');
        if (!toolbar) {
            console.warn('No se encontró toolbar para agregar control de velocidad');
            return;
        }
        
        // Contenedor del control de velocidad
        const speedContainer = document.createElement('div');
        speedContainer.className = 'speed-control';
        speedContainer.innerHTML = `
            <button id="speed-dropdown-btn" class="btn btn-sm" title="Cambiar velocidad">
                <span id="speed-current">1x</span>
                <i class="bi bi-chevron-down"></i>
            </button>
            <div id="speed-dropdown-menu" class="speed-menu hidden">
                ${this.speeds.map((speed, index) => `
                    <div class="speed-option ${index === this.currentSpeedIndex ? 'active' : ''}" 
                         data-speed-index="${index}">
                        <span>${speed.label}</span>
                        ${index === this.currentSpeedIndex ? '<i class="bi bi-check"></i>' : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Insertar antes del contador de frames
        const frameCounter = toolbar.querySelector('#frame-counter');
        if (frameCounter) {
            toolbar.insertBefore(speedContainer, frameCounter);
        } else {
            toolbar.appendChild(speedContainer);
        }
        
        this.speedIndicator = document.getElementById('speed-current');
        
        // Event listeners
        this.setupEventListeners();
    }
    
    /**
     * Configura event listeners del control de velocidad
     */
    setupEventListeners() {
        const dropdownBtn = document.getElementById('speed-dropdown-btn');
        const dropdownMenu = document.getElementById('speed-dropdown-menu');
        
        if (!dropdownBtn || !dropdownMenu) return;
        
        // Toggle dropdown
        dropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('hidden');
        });
        
        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', () => {
            dropdownMenu.classList.add('hidden');
        });
        
        // Opciones de velocidad
        dropdownMenu.querySelectorAll('.speed-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const speedIndex = parseInt(e.currentTarget.dataset.speedIndex);
                this.setSpeed(speedIndex);
                dropdownMenu.classList.add('hidden');
            });
        });
    }
    
    /**
     * Establece la velocidad de reproducción
     * @param {number} speedIndex - Índice de velocidad (0-3)
     */
    setSpeed(speedIndex) {
        if (speedIndex < 0 || speedIndex >= this.speeds.length) {
            console.warn(`⚠️ Índice de velocidad inválido: ${speedIndex}`);
            return;
        }
        
        const oldSpeed = this.speeds[this.currentSpeedIndex];
        this.currentSpeedIndex = speedIndex;
        const newSpeed = this.speeds[speedIndex];
        
        console.log(`Velocidad cambiada: ${oldSpeed.value}x -> ${newSpeed.value}x`);
        
        // Actualizar intervalo del player
        this.player.playSpeed = newSpeed.interval;
        
        // Si está reproduciendo, reiniciar con nueva velocidad
        if (this.player.isPlaying) {
            this.player.pause();
            this.player.play();
        }
        
        // Actualizar UI
        this.updateSpeedIndicator();
        this.updateActiveOption();
        
        // Notificación visual (opcional)
        this.showSpeedNotification(newSpeed.label);
    }
    
    /**
     * Actualiza el indicador de velocidad actual
     */
    updateSpeedIndicator() {
        if (!this.speedIndicator) return;
        
        const currentSpeed = this.speeds[this.currentSpeedIndex];
        this.speedIndicator.textContent = `${currentSpeed.value}x`;
    }
    
    /**
     * Actualiza la opción activa en el dropdown
     */
    updateActiveOption() {
        const options = document.querySelectorAll('.speed-option');
        options.forEach((option, index) => {
            const isActive = index === this.currentSpeedIndex;
            option.classList.toggle('active', isActive);
            
            // Actualizar icono de check
            const checkIcon = option.querySelector('.bi-check');
            if (isActive && !checkIcon) {
                option.innerHTML += '<i class="bi bi-check"></i>';
            } else if (!isActive && checkIcon) {
                checkIcon.remove();
            }
        });
    }
    
    /**
     * Muestra notificación temporal de cambio de velocidad
     * @param {string} label - Etiqueta de la velocidad
     */
    showSpeedNotification(label) {
        // Crear notificación si no existe
        let notification = document.getElementById('speed-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'speed-notification';
            notification.className = 'speed-notification';
            document.body.appendChild(notification);
        }
        
        // Actualizar contenido
        notification.textContent = label;
        notification.classList.add('show');
        
        // Ocultar después de 2 segundos
        setTimeout(() => {
            notification.classList.remove('show');
        }, 2000);
    }
    
    /**
     * Cicla entre velocidades (útil para atajos de teclado)
     * @param {number} direction - Dirección: 1 (siguiente) o -1 (anterior)
     */
    cycleSpeed(direction = 1) {
        let newIndex = this.currentSpeedIndex + direction;
        
        // Wrap around
        if (newIndex >= this.speeds.length) {
            newIndex = 0;
        } else if (newIndex < 0) {
            newIndex = this.speeds.length - 1;
        }
        
        this.setSpeed(newIndex);
    }
    
    /**
     * Obtiene la velocidad actual
     * @returns {object} Objeto con información de velocidad actual
     */
    getCurrentSpeed() {
        return this.speeds[this.currentSpeedIndex];
    }
    
    /**
     * Resetea la velocidad a normal (1x)
     */
    resetSpeed() {
        this.setSpeed(1);
    }
}

// Exportar para uso en timeline_player.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PlaybackController;
}
