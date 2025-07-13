class WorkOrder {
    constructor() {
        this.id = Date.now() + Math.random();
        this.difficulty = this.generateDifficulty();
        this.timeLimit = this.calculateTimeLimit();
        this.materialNeeded = this.calculateMaterialNeeded();
        this.programNeeded = true;
        this.machineTime = this.calculateMachineTime();
        this.qcFailChance = this.calculateQcFailChance();
        this.points = this.calculatePoints();
        this.status = 'pending'; // pending, in_progress, completed, failed
        this.createdAt = Date.now();
        this.steps = {
            cad: false,
            material: false,
            machined: false,
            qc: false,
            shipped: false
        };
        this.progressBarSteps = 0; // For spacebar mini-games
    }

    generateDifficulty() {
        const difficulties = ['Easy', 'Medium', 'Hard'];
        const weights = [0.5, 0.3, 0.2]; // Easy is more common at start
        const levelMultiplier = Math.min(gameState.level * 0.1, 0.4);
        
        // Adjust weights based on level
        const adjustedWeights = [
            Math.max(0.1, weights[0] - levelMultiplier),
            weights[1],
            Math.min(0.7, weights[2] + levelMultiplier)
        ];
        
        const random = Math.random();
        let cumulative = 0;
        for (let i = 0; i < difficulties.length; i++) {
            cumulative += adjustedWeights[i];
            if (random < cumulative) {
                return difficulties[i];
            }
        }
        return 'Easy';
    }

    calculateTimeLimit() {
        const baseTimes = { 'Easy': 60, 'Medium': 45, 'Hard': 30 };
        const baseTime = baseTimes[this.difficulty];
        const levelReduction = Math.min(gameState.level * 3, 20);
        return Math.max(20, baseTime - levelReduction);
    }

    calculateMaterialNeeded() {
        const materials = { 'Easy': 1, 'Medium': 2, 'Hard': 3 };
        return materials[this.difficulty];
    }

    calculateMachineTime() {
        const times = { 'Easy': 3, 'Medium': 5, 'Hard': 8 };
        return times[this.difficulty];
    }

    calculateQcFailChance() {
        const chances = { 'Easy': 0.1, 'Medium': 0.2, 'Hard': 0.35 };
        return chances[this.difficulty];
    }

    calculatePoints() {
        const basePoints = { 'Easy': 100, 'Medium': 200, 'Hard': 400 };
        return basePoints[this.difficulty] + (gameState.level * 50);
    }

    isExpired() {
        return Date.now() > (this.createdAt + this.timeLimit * 1000);
    }

    canProgress(step) {
        switch (step) {
            case 'cad':
                return true;
            case 'material':
                return true;
            case 'machine':
                return this.steps.cad && gameState.material >= this.materialNeeded;
            case 'qc':
                return this.steps.machined;
            case 'ship':
                return this.steps.qc;
            default:
                return false;
        }
    }

    performStep(step) {
        if (!this.canProgress(step)) return false;

        try {
            switch (step) {
                case 'cad':
                    if (!this.steps.cad) {
                        this.steps.cad = true;
                        gameState.programs++;
                        showMessage('CAD program created!', 'success');
                        updateUI();
                        return true;
                    }
                    break;
                    
                case 'material':
                    if (gameState.material < this.materialNeeded) {
                        gameState.material++;
                        showMessage('Material collected!', 'success');
                        updateUI();
                        return true;
                    }
                    break;
                    
                case 'machine':
                    if (!this.steps.machined) {
                        this.steps.machined = true;
                        gameState.material -= this.materialNeeded;
                        gameState.parts++;
                        showMessage('Part machined!', 'success');
                        updateUI();
                        return true;
                    }
                    break;
                    
                case 'qc':
                    if (!this.steps.qc) {
                        if (Math.random() > this.qcFailChance) {
                            this.steps.qc = true;
                            showMessage('QC passed!', 'success');
                            if (typeof recordQCPass !== 'undefined') {
                                recordQCPass();
                            }
                            updateUI();
                            return true;
                        } else {
                            // Failed QC - need to remake
                            this.steps.machined = false;
                            gameState.parts--;
                            showMessage('QC failed! Remake required.', 'error');
                            if (typeof recordQCFail !== 'undefined') {
                                recordQCFail();
                            }
                            updateUI();
                            return false;
                        }
                    }
                    break;
                    
                case 'ship':
                    if (!this.steps.shipped) {
                        this.steps.shipped = true;
                        completeOrder(this.id);
                        return true;
                    }
                    break;
            }
        } catch (error) {
            console.error('Error performing work order step:', error);
            showMessage('Error processing work order step', 'error');
        }
        return false;
    }

    getProgress() {
        const steps = Object.values(this.steps);
        return steps.filter(step => step).length / steps.length;
    }

    getTimeRemaining() {
        const elapsed = (Date.now() - this.createdAt) / 1000;
        return Math.max(0, this.timeLimit - elapsed);
    }
}

function generateNewOrders() {
    // Generate 2-4 new work orders
    const numOrders = Math.floor(Math.random() * 3) + 2;
    for (let i = 0; i < numOrders; i++) {
        const order = new WorkOrder();
        addWorkOrder(order);
    }
    updateUI();
}

function updateWorkOrderTimers() {
    // Check for expired orders
    gameState.workOrders.forEach(order => {
        if (order.status === 'in_progress' && order.isExpired()) {
            failOrder(order.id);
        }
    });
    
    // Auto-generate new orders if we're running low
    const pendingOrders = gameState.workOrders.filter(o => o.status === 'pending').length;
    const inProgressOrders = gameState.workOrders.filter(o => o.status === 'in_progress').length;
    
    if (pendingOrders + inProgressOrders < 2) {
        const order = new WorkOrder();
        addWorkOrder(order);
        updateUI();
        showMessage('New work order available!', 'info');
    }
}

// Helper functions for UI updates
function updateOrdersUI() {
    const ordersList = document.getElementById('ordersList');
    ordersList.innerHTML = '';
    
    gameState.workOrders.forEach(order => {
        if (order.status !== 'completed') {
            const orderElement = createOrderElement(order);
            ordersList.appendChild(orderElement);
        }
    });
}

function createOrderElement(order) {
    const orderElement = document.createElement('div');
    orderElement.className = `order ${order.status}`;
    orderElement.dataset.orderId = order.id;
    
    // Calculate time remaining
    const timeRemaining = order.getTimeRemaining();
    const timeStr = Math.floor(timeRemaining);
    
    // Progress bar
    const progress = order.getProgress() * 100;
    
    // Create step indicators
    const steps = [
        { key: 'cad', icon: '🖥️', name: 'CAD' },
        { key: 'material', icon: '📦', name: 'MAT' },
        { key: 'machined', icon: '⚙️', name: 'MCH' },
        { key: 'qc', icon: '🔍', name: 'QC' },
        { key: 'shipped', icon: '🚚', name: 'SHP' }
    ];
    
    const stepsHtml = steps.map(step => {
        const completed = order.steps[step.key];
        const isCurrent = gameState.currentOrder === order && 
                         !completed && 
                         order.canProgress(step.key);
        
        const stepClass = completed ? 'completed' : (isCurrent ? 'current' : 'pending');
        
        return `
            <div class="order-step ${stepClass}">
                <span class="step-icon">${step.icon}</span>
                <span>${step.name}</span>
            </div>
        `;
    }).join('');
    
    orderElement.innerHTML = `
        <div class="order-header">
            <span class="order-difficulty">${order.difficulty}</span>
            <span class="order-time">${timeStr}s</span>
        </div>
        <div class="order-details">
            <div>Material: ${order.materialNeeded}</div>
            <div>QC Pass: ${Math.round((1 - order.qcFailChance) * 100)}%</div>
            <div>Points: ${order.points}</div>
        </div>
        <div class="order-steps">
            ${stepsHtml}
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${progress}%"></div>
        </div>
        <div class="order-status">${order.status.toUpperCase()}</div>
    `;
    
    // Add click handler for selecting orders
    orderElement.addEventListener('click', () => {
        selectWorkOrder(order.id);
    });
    
    return orderElement;
}