
class Enemy {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.type = type;
        this.lastCollision = 0;
        this.direction = Math.random() * Math.PI * 2;
        this.changeDirectionTimer = 0;
        
        // Set properties based on type
        switch (type) {
            case 'coworker':
                this.size = 12;
                this.speed = 0.8 + Math.random() * 0.4;
                this.color = '#795548';
                this.slowDuration = 1500;
                this.detectionRange = 30;
                break;
            case 'manager':
                this.size = 15;
                this.speed = 1.2 + Math.random() * 0.6;
                this.color = '#FF5722';
                this.slowDuration = 3000;
                this.detectionRange = 50;
                break;
            case 'hr':
                this.size = 18;
                this.speed = 0.6;
                this.color = '#E91E63';
                this.pipOnContact = true;
                this.detectionRange = 60;
                break;
        }
    }

    update(player) {
        // AI behavior
        this.updateAI(player);
        
        // Move based on direction
        this.x += Math.cos(this.direction) * this.speed;
        this.y += Math.sin(this.direction) * this.speed;
        
        // Bounce off walls
        this.handleWallCollisions();
        
        // Check collision with player
        this.checkPlayerCollision(player);
    }

    updateAI(player) {
        const dx = player.x - this.x;
        const dy = player.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Change direction periodically
        this.changeDirectionTimer--;
        if (this.changeDirectionTimer <= 0) {
            this.changeDirectionTimer = 60 + Math.random() * 120; // 1-3 seconds
            
            if (distance < this.detectionRange) {
                // More intelligent pathfinding when player is detected
                if (this.type === 'hr') {
                    // HR actively hunts the player
                    this.direction = Math.atan2(dy, dx);
                } else if (this.type === 'manager') {
                    // Managers try to intercept player's path
                    const playerSpeed = 3; // Assume player speed
                    const interceptTime = distance / (this.speed + playerSpeed);
                    const futurePlayerX = player.x + Math.cos(player.direction || 0) * playerSpeed * interceptTime;
                    const futurePlayerY = player.y + Math.sin(player.direction || 0) * playerSpeed * interceptTime;
                    
                    this.direction = Math.atan2(futurePlayerY - this.y, futurePlayerX - this.x);
                } else {
                    // Coworkers move somewhat randomly toward player
                    this.direction = Math.atan2(dy, dx) + (Math.random() - 0.5) * 0.8;
                }
            } else if (distance < this.detectionRange * 2) {
                // Patrol behavior when player is nearby but not detected
                this.direction += (Math.random() - 0.5) * 0.5;
            } else {
                // Random movement when player is far away
                this.direction = Math.random() * Math.PI * 2;
            }
        }
        
        // Add some randomness to movement to avoid getting stuck
        if (Math.random() < 0.02) {
            this.direction += (Math.random() - 0.5) * 0.3;
        }
    }

    handleWallCollisions() {
        const margin = this.size;
        
        // Check canvas boundaries
        if (this.x <= margin || this.x >= canvas.width - margin) {
            this.direction = Math.PI - this.direction;
            this.x = Math.max(margin, Math.min(canvas.width - margin, this.x));
        }
        
        if (this.y <= margin || this.y >= canvas.height - margin) {
            this.direction = -this.direction;
            this.y = Math.max(margin, Math.min(canvas.height - margin, this.y));
        }
        
        // Check if enemy is on a valid path (if maze is initialized)
        if (mazePaths && mazePaths.paths.length > 0) {
            const onPath = isOnPath(this.x, this.y) || 
                          stations.some(station => 
                              distance(this.x, this.y, station.x, station.y) < 60
                          );
            
            if (!onPath) {
                // Find nearest path or station
                let nearestPoint = null;
                let minDistance = Infinity;
                
                // Check stations
                stations.forEach(station => {
                    const dist = distance(this.x, this.y, station.x, station.y);
                    if (dist < minDistance) {
                        minDistance = dist;
                        nearestPoint = { x: station.x, y: station.y };
                    }
                });
                
                // Check path intersections
                mazePaths.nodes.forEach(node => {
                    const dist = distance(this.x, this.y, node.x, node.y);
                    if (dist < minDistance) {
                        minDistance = dist;
                        nearestPoint = { x: node.x, y: node.y };
                    }
                });
                
                if (nearestPoint) {
                    // Move towards nearest valid point
                    this.direction = Math.atan2(nearestPoint.y - this.y, nearestPoint.x - this.x);
                }
            }
        }
    }

    checkPlayerCollision(player) {
        const dx = player.x - this.x;
        const dy = player.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < this.size + player.size && Date.now() > this.lastCollision + 2000) {
            this.lastCollision = Date.now();
            this.onPlayerCollision(player);
        }
    }

    onPlayerCollision(player) {
        // Add particle effects for collision
        if (typeof particleSystem !== 'undefined') {
            if (this.type === 'hr') {
                particleSystem.playerCaught(player.x, player.y);
                addScreenShake(5, 25);
            } else {
                particleSystem.addParticles(player.x, player.y, 8, this.color, 'spark');
                addScreenShake(2, 10);
            }
        }
        
        // Record collision for achievements
        if (typeof recordPlayerCollision !== 'undefined') {
            recordPlayerCollision();
        }
        
        switch (this.type) {
            case 'coworker':
                player.slowDown(this.slowDuration);
                showMessage('Bumped into coworker!', 'warning');
                break;
            case 'manager':
                player.slowDown(this.slowDuration);
                showMessage('Manager pulled you into a meeting!', 'warning');
                break;
            case 'hr':
                addPIP();
                showMessage('HR caught you! PIP assigned!', 'error');
                break;
        }
    }

    draw(ctx) {
        // Draw enemy body
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();

        // Draw border
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Draw type indicator
        ctx.fillStyle = '#fff';
        ctx.font = '8px Arial';
        ctx.textAlign = 'center';
        const label = this.type === 'coworker' ? 'CW' : 
                     this.type === 'manager' ? 'MGR' : 'HR';
        ctx.fillText(label, this.x, this.y + 2);

        // Draw detection range (debug - can be removed)
        if (false) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.detectionRange, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
}

class EnemyManager {
    constructor() {
        this.enemies = [];
        this.initializeEnemies();
    }

    initializeEnemies() {
        // Start with basic enemies
        this.enemies = [
            new Enemy(200, 200, 'coworker'),
            new Enemy(600, 400, 'coworker'),
            new Enemy(300, 500, 'manager')
        ];
    }

    addHREnemy() {
        if (!this.enemies.find(e => e.type === 'hr')) {
            this.enemies.push(new Enemy(400, 300, 'hr'));
            showMessage('HR has entered the labyrinth!', 'warning');
        }
    }

    addEnemy(type) {
        const x = Math.random() * (canvas.width - 100) + 50;
        const y = Math.random() * (canvas.height - 100) + 50;
        this.enemies.push(new Enemy(x, y, type));
    }

    update(player) {
        this.enemies.forEach(enemy => enemy.update(player));
        
        // Occasionally add more enemies at higher levels
        if (Math.random() < 0.0005 * gameState.level && this.enemies.length < 8) {
            const type = Math.random() < 0.7 ? 'coworker' : 'manager';
            this.addEnemy(type);
        }
    }

    draw(ctx) {
        this.enemies.forEach(enemy => enemy.draw(ctx));
    }

    reset() {
        this.initializeEnemies();
    }
}

// Global enemy manager instance
const enemyManager = new EnemyManager();

function addHREnemy() {
    enemyManager.addHREnemy();
}