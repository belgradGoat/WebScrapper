class Player {
    constructor(x, y, speed) {
        this.x = x;
        this.y = y;
        this.speed = speed;
        this.baseSpeed = speed;
        this.size = 15;
        this.color = '#4CAF50';
        this.slowedUntil = 0;
        this.interactionCooldown = 0;
        this.currentStation = null;
        this.inMiniGame = false;
        this.miniGameProgress = 0;
        this.miniGameTarget = 0;
    }

    update() {
        // Handle movement slowdown
        if (Date.now() > this.slowedUntil) {
            this.speed = this.baseSpeed;
        }

        // Update interaction cooldown
        if (this.interactionCooldown > 0) {
            this.interactionCooldown--;
        }

        // Handle movement input
        this.handleMovement();

        // Check station interactions
        this.checkStationInteractions();

        // Ensure player stays within bounds
        this.checkBounds();
    }

    handleMovement() {
        if (this.inMiniGame) return; // Can't move during mini-games

        let newX = this.x;
        let newY = this.y;
        let moveHorizontal = false;
        let moveVertical = false;

        // Detect movement input
        if (keys['ArrowLeft'] || keys['a'] || keys['A']) {
            newX -= this.speed;
            moveHorizontal = true;
        }
        if (keys['ArrowRight'] || keys['d'] || keys['D']) {
            newX += this.speed;
            moveHorizontal = true;
        }
        if (keys['ArrowUp'] || keys['w'] || keys['W']) {
            newY -= this.speed;
            moveVertical = true;
        }
        if (keys['ArrowDown'] || keys['s'] || keys['S']) {
            newY += this.speed;
            moveVertical = true;
        }

        // Enforce perpendicular movement - prevent diagonal movement
        if (moveHorizontal && moveVertical) {
            // If both directions are pressed, prioritize the direction with larger movement
            const deltaX = Math.abs(newX - this.x);
            const deltaY = Math.abs(newY - this.y);
            
            if (deltaX > deltaY) {
                // Prioritize horizontal movement
                newY = this.y;
            } else {
                // Prioritize vertical movement
                newX = this.x;
            }
        }

        // Try horizontal movement first
        if (newX !== this.x && this.canMoveTo(newX, this.y)) {
            this.x = newX;
            return; // Successful horizontal movement
        }
        
        // Try vertical movement if horizontal failed or wasn't attempted
        if (newY !== this.y && this.canMoveTo(this.x, newY)) {
            this.y = newY;
            return; // Successful vertical movement
        }
        
        // If neither direction works, try to find the nearest valid path
        this.snapToNearestPath();
    }

    canMoveTo(x, y) {
        // Check boundaries
        const margin = this.size;
        if (!(x >= margin && x <= canvas.width - margin && 
              y >= margin && y <= canvas.height - margin)) {
            return false;
        }
        
        // If maze isn't initialized yet, allow free movement
        if (!mazePaths || mazePaths.paths.length === 0) {
            return true;
        }
        
        // Check if on a valid perpendicular path
        if (isOnPath(x, y)) {
            return true;
        }
        
        // Check if near a station (allow some tolerance around stations)
        const stationTolerance = 60;
        for (let station of stations) {
            if (distance(x, y, station.x, station.y) < stationTolerance) {
                return true;
            }
        }
        
        // Check if near an intersection (for smoother transitions)
        const intersectionTolerance = 25;
        for (let node of mazePaths.nodes) {
            if (node.type === 'intersection' || node.type === 'corner') {
                if (distance(x, y, node.x, node.y) < intersectionTolerance) {
                    return true;
                }
            }
        }
        
        return false;
    }

    checkBounds() {
        const margin = this.size;
        this.x = Math.max(margin, Math.min(canvas.width - margin, this.x));
        this.y = Math.max(margin, Math.min(canvas.height - margin, this.y));
    }

    checkStationInteractions() {
        let nearStation = null;
        const interactionDistance = 40;

        // Find nearest station
        stations.forEach(station => {
            const distance = this.distanceTo(station.x, station.y);
            if (distance < interactionDistance) {
                nearStation = station;
            }
        });

        this.currentStation = nearStation;

        // Handle spacebar interaction
        if (nearStation && (keys[' '] || keys['Space']) && this.interactionCooldown === 0) {
            if (typeof soundManager !== 'undefined') {
                soundManager.playInteraction();
            }
            this.interactWithStation(nearStation);
            this.interactionCooldown = 10; // Prevent spam clicking
        }
    }

    distanceTo(x, y) {
        return Math.sqrt(Math.pow(this.x - x, 2) + Math.pow(this.y - y, 2));
    }

    interactWithStation(station) {
        if (!gameState.currentOrder) {
            showMessage('Select a work order first!', 'warning');
            return;
        }

        const order = gameState.currentOrder;

        // Add particle effect for station activation
        if (typeof particleSystem !== 'undefined') {
            particleSystem.stationActivated(station.x, station.y, station.action);
        }

        switch (station.action) {
            case 'cad':
                this.startMiniGame('cad', 5, () => {
                    order.performStep('cad');
                });
                break;
                
            case 'material':
                this.startMiniGame('material', 3, () => {
                    order.performStep('material');
                });
                break;
                
            case 'machine':
                if (order.canProgress('machine')) {
                    this.startMiniGame('machine', order.machineTime, () => {
                        order.performStep('machine');
                    });
                } else {
                    showMessage('Need CAD program and materials first!', 'warning');
                }
                break;
                
            case 'qc':
                if (order.canProgress('qc')) {
                    this.startMiniGame('qc', 4, () => {
                        order.performStep('qc');
                    });
                } else {
                    showMessage('Need machined part first!', 'warning');
                }
                break;
                
            case 'ship':
                if (order.canProgress('ship')) {
                    order.performStep('ship');
                    showMessage('Order shipped!', 'success');
                } else {
                    showMessage('Part must pass QC first!', 'warning');
                }
                break;
        }
    }

    startMiniGame(type, targetPresses, onComplete) {
        this.inMiniGame = true;
        this.miniGameProgress = 0;
        this.miniGameTarget = targetPresses;
        this.miniGameCallback = onComplete;
        this.miniGameType = type;
        
        showMessage(`Press spacebar ${targetPresses} times quickly!`, 'info');
    }

    updateMiniGame() {
        if (!this.inMiniGame) return;

        if ((keys[' '] || keys['Space']) && this.interactionCooldown === 0) {
            this.miniGameProgress++;
            this.interactionCooldown = 8; // Prevent too rapid clicking
            
            if (this.miniGameProgress >= this.miniGameTarget) {
                this.completeMiniGame();
            } else {
                showMessage(`${this.miniGameProgress}/${this.miniGameTarget} - Keep pressing!`, 'info');
            }
        }
    }

    completeMiniGame() {
        this.inMiniGame = false;
        this.miniGameCallback();
        showMessage(`${this.miniGameType.toUpperCase()} completed!`, 'success');
    }

    slowDown(duration = 2000) {
        this.speed = this.baseSpeed * 0.3;
        this.slowedUntil = Date.now() + duration;
        showMessage('Slowed down by obstacle!', 'warning');
    }

    snapToNearestPath() {
        // Use the enhanced path finding function
        const nearestPoint = findNearestValidPosition(this.x, this.y);
        
        // Snap to nearest point if it's reasonably close and provides a valid path
        if (nearestPoint && distance(this.x, this.y, nearestPoint.x, nearestPoint.y) < 60) {
            // Smooth transition to path
            const transitionSpeed = 0.2;
            this.x += (nearestPoint.x - this.x) * transitionSpeed;
            this.y += (nearestPoint.y - this.y) * transitionSpeed;
            
            // Add visual feedback
            if (typeof particleSystem !== 'undefined') {
                particleSystem.addParticles(this.x, this.y, 3, '#ffeb3b', 'star');
            }
        }
    }

    // Add method to get valid movement directions
    getValidDirections() {
        const validDirections = {
            up: false,
            down: false,
            left: false,
            right: false
        };
        
        const testDistance = this.speed + 5;
        
        // Test each direction
        if (this.canMoveTo(this.x, this.y - testDistance)) {
            validDirections.up = true;
        }
        if (this.canMoveTo(this.x, this.y + testDistance)) {
            validDirections.down = true;
        }
        if (this.canMoveTo(this.x - testDistance, this.y)) {
            validDirections.left = true;
        }
        if (this.canMoveTo(this.x + testDistance, this.y)) {
            validDirections.right = true;
        }
        
        return validDirections;
    }

    // Enhanced draw method with movement indicators
    draw(ctx) {
        // Get valid movement directions
        const validDirections = this.getValidDirections();
        
        // Draw movement direction indicators
        const indicatorDistance = 35;
        const indicatorSize = 8;
        
        ctx.fillStyle = 'rgba(76, 175, 80, 0.7)'; // Green for valid directions
        
        if (validDirections.up) {
            ctx.fillRect(this.x - indicatorSize/2, this.y - indicatorDistance, indicatorSize, indicatorSize);
            // Arrow
            ctx.beginPath();
            ctx.moveTo(this.x, this.y - indicatorDistance - 5);
            ctx.lineTo(this.x - 4, this.y - indicatorDistance + 2);
            ctx.lineTo(this.x + 4, this.y - indicatorDistance + 2);
            ctx.fill();
        }
        
        if (validDirections.down) {
            ctx.fillRect(this.x - indicatorSize/2, this.y + indicatorDistance, indicatorSize, indicatorSize);
            // Arrow
            ctx.beginPath();
            ctx.moveTo(this.x, this.y + indicatorDistance + 5);
            ctx.lineTo(this.x - 4, this.y + indicatorDistance - 2);
            ctx.lineTo(this.x + 4, this.y + indicatorDistance - 2);
            ctx.fill();
        }
        
        if (validDirections.left) {
            ctx.fillRect(this.x - indicatorDistance, this.y - indicatorSize/2, indicatorSize, indicatorSize);
            // Arrow
            ctx.beginPath();
            ctx.moveTo(this.x - indicatorDistance - 5, this.y);
            ctx.lineTo(this.x - indicatorDistance + 2, this.y - 4);
            ctx.lineTo(this.x - indicatorDistance + 2, this.y + 4);
            ctx.fill();
        }
        
        if (validDirections.right) {
            ctx.fillRect(this.x + indicatorDistance, this.y - indicatorSize/2, indicatorSize, indicatorSize);
            // Arrow
            ctx.beginPath();
            ctx.moveTo(this.x + indicatorDistance + 5, this.y);
            ctx.lineTo(this.x + indicatorDistance - 2, this.y - 4);
            ctx.lineTo(this.x + indicatorDistance - 2, this.y + 4);
            ctx.fill();
        }
        
        // Draw player circle
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw player outline
        ctx.strokeStyle = '#2E7D32';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw factory worker indicator
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('W', this.x, this.y + 3);
        
        // If slowed, add visual effect
        if (this.speed < this.baseSpeed) {
            ctx.strokeStyle = '#FF5722';
            ctx.lineWidth = 3;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size + 8, 0, Math.PI * 2);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        
        // If in mini-game, add pulsing effect
        if (this.inMiniGame) {
            const pulse = Math.sin(Date.now() / 200) * 0.5 + 0.5;
            ctx.strokeStyle = `rgba(33, 150, 243, ${pulse})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size + 12, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
}