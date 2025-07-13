// Global keyboard state
const keys = {};

// Message display system
let messageQueue = [];
let currentMessage = null;
let messageTimer = 0;

// Initialize input handling
function initializeInput() {
    document.addEventListener('keydown', (e) => {
        keys[e.key] = true;
        keys[e.code] = true;
        
        // Prevent default for game keys
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
            e.preventDefault();
        }
        
        // Prevent default for WASD when not in input fields
        if (['KeyW', 'KeyA', 'KeyS', 'KeyD'].includes(e.code) && 
            !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            e.preventDefault();
        }
    });
    
    document.addEventListener('keyup', (e) => {
        keys[e.key] = false;
        keys[e.code] = false;
    });

    // Handle work order selection clicks
    document.addEventListener('click', (e) => {
        if (e.target.closest('.work-order, .order')) {
            const orderElement = e.target.closest('.work-order, .order');
            const orderId = orderElement.dataset.orderId;
            if (orderId) {
                selectWorkOrder(parseFloat(orderId));
            }
        }
    });
    
    // Handle window focus/blur to prevent key stuck states
    window.addEventListener('blur', () => {
        // Clear all keys when window loses focus
        Object.keys(keys).forEach(key => {
            keys[key] = false;
        });
    });
}

// Message system
function showMessage(text, type = 'info', duration = 3000) {
    const message = { text, type, duration, timestamp: Date.now() };
    messageQueue.push(message);
    
    // Play appropriate sound
    if (typeof soundManager !== 'undefined') {
        switch (type) {
            case 'success':
                soundManager.playSuccess();
                break;
            case 'error':
                soundManager.playError();
                break;
            case 'warning':
                soundManager.playWarning();
                break;
        }
    }
    
    // Also log to console for debugging
    console.log(`[${type.toUpperCase()}] ${text}`);
}

function updateMessages() {
    if (!currentMessage && messageQueue.length > 0) {
        currentMessage = messageQueue.shift();
        messageTimer = currentMessage.duration;
    }
    
    if (currentMessage && messageTimer > 0) {
        messageTimer -= 16; // Assuming 60fps
        if (messageTimer <= 0) {
            currentMessage = null;
        }
    }
}

function drawMessages(ctx) {
    if (!currentMessage) return;
    
    const alpha = Math.min(1, messageTimer / 500); // Fade out in last 500ms
    
    // Background
    ctx.fillStyle = `rgba(0, 0, 0, ${alpha * 0.8})`;
    ctx.fillRect(10, canvas.height - 80, canvas.width - 20, 60);
    
    // Border
    const borderColor = {
        'info': '#2196F3',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336'
    }[currentMessage.type] || '#fff';
    
    ctx.strokeStyle = `rgba(${hexToRgb(borderColor).r}, ${hexToRgb(borderColor).g}, ${hexToRgb(borderColor).b}, ${alpha})`;
    ctx.lineWidth = 2;
    ctx.strokeRect(10, canvas.height - 80, canvas.width - 20, 60);
    
    // Text
    ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(currentMessage.text, 20, canvas.height - 45);
}

// Utility functions
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function distance(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function lerp(start, end, factor) {
    return start + (end - start) * factor;
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Update UI elements
function updateUI() {
    document.getElementById('level').textContent = gameState.level;
    document.getElementById('pips').textContent = gameState.pips;
    document.getElementById('timeLeft').textContent = gameState.timeLeft;
    document.getElementById('score').textContent = gameState.score;
    document.getElementById('material').textContent = gameState.material;
    document.getElementById('programs').textContent = gameState.programs;
    document.getElementById('parts').textContent = gameState.parts;
    
    updateWorkOrdersDisplay();
}

function updateWorkOrdersDisplay() {
    const ordersList = document.getElementById('ordersList');
    ordersList.innerHTML = '';
    
    gameState.workOrders.forEach(order => {
        const div = document.createElement('div');
        div.className = `work-order ${order.status}`;
        div.dataset.orderId = order.id;
        
        if (order === gameState.currentOrder) {
            div.classList.add('selected');
        }
        
        const timeRemaining = Math.max(0, order.getTimeRemaining());
        const progress = order.getProgress() * 100;
        
        div.innerHTML = `
            <div><strong>${order.difficulty}</strong></div>
            <div>Points: ${order.points}</div>
            <div>Material: ${order.materialNeeded}</div>
            <div>Time: ${Math.ceil(timeRemaining)}s</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
        `;
        
        ordersList.appendChild(div);
    });
}

// Sound toggle function
function toggleSound() {
    if (typeof soundManager !== 'undefined') {
        const enabled = soundManager.toggle();
        const button = document.getElementById('soundToggle');
        button.textContent = enabled ? '🔊 Sound' : '🔇 Muted';
        button.style.opacity = enabled ? '1' : '0.5';
    }
}

// Game restart function
function restartGame() {
    resetGameState();
    player.x = 400;
    player.y = 300;
    player.speed = player.baseSpeed;
    player.inMiniGame = false;
    enemyManager.reset();
    
    document.getElementById('gameOver').style.display = 'none';
    
    generateNewOrders();
    updateUI();
    
    showMessage('Game restarted!', 'info');
}