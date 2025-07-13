const gameState = {
    level: 1,
    score: 0,
    pips: 0,
    timeLeft: 60,
    material: 0,
    programs: 0,
    parts: 0,
    currentOrder: null,
    workOrders: [],
    gameRunning: true,
    gameStartTime: Date.now(),
    hrInLabyrinth: false,
    completedOrdersThisLevel: 0,
    workOrderDeadlines: new Map(), // Track individual order deadlines
    
    // Achievement tracking
    totalOrdersCompleted: 0,
    consecutiveQCPasses: 0,
    lastCollisionTime: Date.now(),
    timeSinceLastCollision: 0,
    activeOrders: 0
};

function resetGameState() {
    gameState.level = 1;
    gameState.score = 0;
    gameState.pips = 0;
    gameState.timeLeft = 60;
    gameState.material = 0;
    gameState.programs = 0;
    gameState.parts = 0;
    gameState.currentOrder = null;
    gameState.workOrders = [];
    gameState.gameRunning = true;
    gameState.gameStartTime = Date.now();
    gameState.hrInLabyrinth = false;
    gameState.completedOrdersThisLevel = 0;
    gameState.workOrderDeadlines.clear();
}

function levelUp() {
    gameState.level++;
    gameState.completedOrdersThisLevel = 0;
    gameState.timeLeft = Math.max(30, 60 - gameState.level * 3);
    showMessage(`Level ${gameState.level}! Difficulty increased.`, 'info');
    
    // Add spectacular level-up particle effects
    if (typeof particleSystem !== 'undefined' && typeof player !== 'undefined') {
        particleSystem.levelUp(player.x, player.y);
        addScreenShake(8, 30);
    }
    
    // Add HR to labyrinth at higher levels
    if (gameState.level >= 3 && !gameState.hrInLabyrinth) {
        gameState.hrInLabyrinth = true;
        enemyManager.addHREnemy();
    }
}

function addWorkOrder(order) {
    gameState.workOrders.push(order);
    // Set deadline for this order
    gameState.workOrderDeadlines.set(order.id, Date.now() + order.timeLimit * 1000);
}

function selectWorkOrder(orderId) {
    const order = gameState.workOrders.find(o => o.id === orderId);
    if (order && order.status === 'pending') {
        // Deselect current order
        if (gameState.currentOrder) {
            gameState.currentOrder.status = 'pending';
        }
        
        gameState.currentOrder = order;
        order.status = 'in_progress';
        showMessage(`Work order selected: ${order.difficulty} part`, 'info');
        updateUI();
    }
}

function completeOrder(orderId) {
    const order = gameState.workOrders.find(o => o.id === orderId);
    if (order) {
        order.status = 'completed';
        gameState.score += order.points;
        gameState.parts--;
        gameState.completedOrdersThisLevel++;
        gameState.totalOrdersCompleted++;
        
        showMessage(`+${order.points} points! Order completed!`, 'success');
        
        // Add particle effects at player location
        if (typeof particleSystem !== 'undefined' && typeof player !== 'undefined') {
            particleSystem.workOrderComplete(player.x, player.y);
            addScreenShake(3, 15);
        }
        
        // Play completion sound
        if (typeof soundManager !== 'undefined') {
            soundManager.playComplete();
        }
        
        // Check achievements
        updateAchievementProgress();
        
        // Check for level up
        if (gameState.completedOrdersThisLevel >= gameState.level * 2) {
            levelUp();
        }
        
        // Clear current order if it's the completed one
        if (gameState.currentOrder === order) {
            gameState.currentOrder = null;
        }
        
        // Remove deadline
        gameState.workOrderDeadlines.delete(orderId);
    }
}

function failOrder(orderId) {
    const order = gameState.workOrders.find(o => o.id === orderId);
    if (order) {
        order.status = 'failed';
        showMessage('Order failed! Deadline missed.', 'error');
        
        // Clear current order if it's the failed one
        if (gameState.currentOrder === order) {
            gameState.currentOrder = null;
        }
        
        addPIP();
        gameState.workOrderDeadlines.delete(orderId);
    }
}

function addPIP() {
    gameState.pips++;
    showMessage('PIP assigned! Warning: Performance improvement needed.', 'warning');
    if (gameState.pips >= 3) {
        gameOver('Too many PIPs! You\'ve been terminated.');
    }
}

function gameOver(message) {
    gameState.gameRunning = false;
    document.getElementById('gameOverMessage').textContent = message;
    document.getElementById('gameOver').style.display = 'block';
}

function updateTime() {
    if (gameState.gameRunning) {
        gameState.timeLeft--;
        
        // Check for expired work orders
        const currentTime = Date.now();
        for (const [orderId, deadline] of gameState.workOrderDeadlines) {
            if (currentTime > deadline) {
                const order = gameState.workOrders.find(o => o.id === orderId);
                if (order && order.status === 'in_progress') {
                    failOrder(orderId);
                }
            }
        }
        
        if (gameState.timeLeft <= 0) {
            // Reset timer for new round
            gameState.timeLeft = Math.max(30, 60 - gameState.level * 3);
            generateNewOrders();
        }
    }
}

function updateAchievementProgress() {
    if (typeof achievementManager === 'undefined') return;
    
    // Update tracking variables
    gameState.timeSinceLastCollision = Date.now() - gameState.lastCollisionTime;
    gameState.activeOrders = gameState.workOrders.filter(o => o.status === 'in_progress').length;
    
    // Check all achievements
    achievementManager.checkAchievements(gameState);
}

function recordPlayerCollision() {
    gameState.lastCollisionTime = Date.now();
    gameState.timeSinceLastCollision = 0;
    updateAchievementProgress();
}

function recordQCPass() {
    gameState.consecutiveQCPasses++;
    updateAchievementProgress();
}

function recordQCFail() {
    gameState.consecutiveQCPasses = 0;
    updateAchievementProgress();
}