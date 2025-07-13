// Touch controls for mobile devices
class TouchControls {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.minSwipeDistance = 50;
        this.virtualButtons = new Map();
        this.setupTouchControls();
        this.setupVirtualButtons();
    }

    setupTouchControls() {
        // Touch movement controls
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Prevent default touch behaviors on game canvas
        canvas.addEventListener('touchstart', (e) => e.preventDefault());
        canvas.addEventListener('touchmove', (e) => e.preventDefault());
        canvas.addEventListener('touchend', (e) => e.preventDefault());
    }

    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
    }

    handleTouchMove(e) {
        e.preventDefault(); // Prevent scrolling
        
        if (!e.touches[0]) return;
        
        this.touchEndX = e.touches[0].clientX;
        this.touchEndY = e.touches[0].clientY;
        
        // Calculate movement direction for continuous movement
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        
        // Apply movement if significant
        if (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10) {
            this.applyMovement(deltaX, deltaY);
        }
    }

    handleTouchEnd(e) {
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        
        // Handle swipe gestures
        if (Math.abs(deltaX) > this.minSwipeDistance || Math.abs(deltaY) > this.minSwipeDistance) {
            this.handleSwipe(deltaX, deltaY);
        }
    }

    applyMovement(deltaX, deltaY) {
        if (!player || !gameState.gameRunning) return;
        
        const sensitivity = 0.3;
        const moveSpeed = player.speed * sensitivity;
        
        // Normalize movement
        const magnitude = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        if (magnitude > 0) {
            const normalizedX = (deltaX / magnitude) * moveSpeed;
            const normalizedY = (deltaY / magnitude) * moveSpeed;
            
            // Apply movement
            const newX = player.x + normalizedX;
            const newY = player.y + normalizedY;
            
            // Check boundaries and maze paths
            if (isOnPath(newX, newY)) {
                player.x = Math.max(player.size, Math.min(canvas.width - player.size, newX));
                player.y = Math.max(player.size, Math.min(canvas.height - player.size, newY));
            }
        }
    }

    handleSwipe(deltaX, deltaY) {
        // Quick movement for swipe gestures
        if (!player || !gameState.gameRunning) return;
        
        const swipeSpeed = 20;
        
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            // Horizontal swipe
            const direction = deltaX > 0 ? 1 : -1;
            const newX = player.x + (direction * swipeSpeed);
            if (isOnPath(newX, player.y)) {
                player.x = Math.max(player.size, Math.min(canvas.width - player.size, newX));
            }
        } else {
            // Vertical swipe
            const direction = deltaY > 0 ? 1 : -1;
            const newY = player.y + (direction * swipeSpeed);
            if (isOnPath(player.x, newY)) {
                player.y = Math.max(player.size, Math.min(canvas.height - player.size, newY));
            }
        }
    }

    setupVirtualButtons() {
        // Only show virtual buttons on mobile devices
        if (!this.isMobile()) return;
        
        this.createVirtualButton('interact', '⚡', 'bottom-right', () => {
            // Simulate spacebar press
            keys[' '] = true;
            setTimeout(() => keys[' '] = false, 100);
        });
        
        this.createVirtualButton('pause', '⏸️', 'top-right', () => {
            togglePause();
        });
        
        this.createVirtualButton('help', '❓', 'top-left', () => {
            showHelp = !showHelp;
        });
    }

    createVirtualButton(id, text, position, callback) {
        const button = document.createElement('div');
        button.className = `virtual-button virtual-button-${position}`;
        button.textContent = text;
        button.id = `virtual-${id}`;
        
        // Position the button
        const positions = {
            'bottom-right': { bottom: '20px', right: '20px' },
            'bottom-left': { bottom: '20px', left: '20px' },
            'top-right': { top: '20px', right: '20px' },
            'top-left': { top: '20px', left: '20px' }
        };
        
        Object.assign(button.style, positions[position]);
        
        // Add touch event listeners
        button.addEventListener('touchstart', (e) => {
            e.preventDefault();
            button.classList.add('pressed');
            callback();
        });
        
        button.addEventListener('touchend', (e) => {
            e.preventDefault();
            button.classList.remove('pressed');
        });
        
        document.body.appendChild(button);
        this.virtualButtons.set(id, button);
    }

    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }

    showControls() {
        this.virtualButtons.forEach(button => {
            button.style.display = 'block';
        });
    }

    hideControls() {
        this.virtualButtons.forEach(button => {
            button.style.display = 'none';
        });
    }

    updateControlsVisibility() {
        if (this.isMobile() && gameState.gameRunning) {
            this.showControls();
        } else {
            this.hideControls();
        }
    }
}

// Initialize touch controls when DOM is ready
let touchControls;
document.addEventListener('DOMContentLoaded', () => {
    touchControls = new TouchControls();
    
    // Update controls visibility on resize
    window.addEventListener('resize', () => {
        if (touchControls) {
            touchControls.updateControlsVisibility();
        }
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TouchControls };
}
