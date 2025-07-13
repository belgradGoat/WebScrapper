// Canvas setup
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Game objects
let player;
let gameLoopId;

// Initialize particle system
const particleSystem = new ParticleSystem();

// Screen shake variables
let screenShake = {
    intensity: 0,
    duration: 0,
    x: 0,
    y: 0
};

function addScreenShake(intensity, duration) {
    screenShake.intensity = intensity;
    screenShake.duration = duration;
}

function updateScreenShake() {
    if (screenShake.duration > 0) {
        screenShake.duration--;
        const intensity = screenShake.intensity * (screenShake.duration / 30);
        screenShake.x = (Math.random() - 0.5) * intensity;
        screenShake.y = (Math.random() - 0.5) * intensity;
    } else {
        screenShake.x = 0;
        screenShake.y = 0;
    }
}

// Maze paths system
const mazePaths = {
    nodes: [], // Connection points in the maze
    paths: []  // Valid paths between nodes
};

// Pause functionality
let gamePaused = false;

// Performance monitoring
let lastFrameTime = 0;
let frameCount = 0;
let fps = 0;

// Debug mode
let debugMode = false;

// Help screen
let showHelp = false;

// Maze visualization mode
let showMazeOverlay = false;

// Initialize game
function initGame() {
    // Initialize input handling
    initializeInput();
    
    // Create player
    player = new Player(400, 300, 3);
    
    // Generate initial work orders
    generateNewOrders();
    
    // Initialize maze
    initializeMaze();
    
    // Start game timer
    setInterval(() => {
        if (gameState.gameRunning) {
            updateTime();
            updateWorkOrderTimers();
            updateUI();
        }
    }, 1000);
    
    // Start game loop
    gameLoop();
    
    showMessage('Welcome to Machinist Runner! Select a work order to begin.', 'info');
}

// Main game loop
function gameLoop() {
    if (gameState.gameRunning && !gamePaused) {
        update();
        render();
    } else if (gamePaused) {
        // Still render when paused, just don't update
        render();
        drawPauseOverlay();
    }
    gameLoopId = requestAnimationFrame(gameLoop);
}

// Draw pause overlay
function drawPauseOverlay() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('PAUSED', canvas.width / 2, canvas.height / 2 - 20);
    
    ctx.font = '18px Arial';
    ctx.fillText('Press P or ESC to resume', canvas.width / 2, canvas.height / 2 + 20);
}

// Update game state
function update() {
    // Calculate FPS
    frameCount++;
    const currentTime = Date.now();
    if (currentTime - lastFrameTime >= 1000) {
        fps = frameCount;
        frameCount = 0;
        lastFrameTime = currentTime;
    }
    
    // Update screen shake
    updateScreenShake();
    
    // Update particles
    particleSystem.update();
    
    // Update player
    player.update();
    player.updateMiniGame();
    
    // Update enemies
    enemyManager.update(player);
    
    // Update messages
    updateMessages();
    
    // Update achievements periodically
    if (frameCount % 60 === 0) { // Check every second
        updateAchievementProgress();
    }
    
    // Check for game over conditions
    if (gameState.pips >= 3) {
        gameOver('Too many PIPs! You\'ve been terminated.');
    }
}

// Render everything
function render() {
    // Apply screen shake
    ctx.save();
    ctx.translate(screenShake.x, screenShake.y);
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw background pattern
    drawBackground();
    
    // Draw maze paths
    drawMaze();
    
    // Draw stations
    drawStations(ctx);
    
    // Draw enemies
    enemyManager.draw(ctx);
    
    // Draw player
    player.draw(ctx);
    
    // Draw particles
    particleSystem.draw(ctx);
    
    // Restore context from screen shake
    ctx.restore();
    
    // Draw UI overlays (not affected by screen shake)
    drawMessages(ctx);
    
    // Draw mini-game overlay if active
    if (player.inMiniGame) {
        drawMiniGameOverlay();
    }
    
    // Draw debug information if enabled
    if (debugMode) {
        drawDebugInfo();
    }
    if (showHelp) {
        drawHelpScreen();
    }
    drawMazeOverlay();
}

function drawDebugInfo() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(10, 10, 250, 150);
    
    ctx.fillStyle = '#00ff00';
    ctx.font = '12px monospace';
    ctx.textAlign = 'left';
    
    const nearestIntersection = mazePaths.nodes.find(node => 
        node.type === 'intersection' && 
        distance(player.x, player.y, node.x, node.y) < 100
    );
    
    const debugInfo = [
        `FPS: ${fps}`,
        `Player: (${Math.round(player.x)}, ${Math.round(player.y)})`,
        `Speed: ${player.speed.toFixed(1)}`,
        `Enemies: ${enemyManager.enemies.length}`,
        `On Path: ${isOnPath(player.x, player.y)}`,
        `Maze Nodes: ${mazePaths.nodes.length}`,
        `Maze Paths: ${mazePaths.paths.length}`,
        `Near Intersection: ${nearestIntersection ? nearestIntersection.id : 'None'}`,
        `Current Order: ${gameState.currentOrder ? gameState.currentOrder.difficulty : 'None'}`,
        `Level: ${gameState.level}`,
        `Score: ${gameState.score}`,
        `Material: ${gameState.material}`,
        `Parts: ${gameState.parts}`
    ];
    
    debugInfo.forEach((info, i) => {
        ctx.fillText(info, 15, 25 + i * 14);
    });
}

function drawHelpScreen() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('MACHINIST RUNNER - HELP', canvas.width / 2, 50);
    
    ctx.font = '14px Arial';
    ctx.textAlign = 'left';
    
    const helpText = [
        'CONTROLS:',
        '  WASD or Arrow Keys - Move player',
        '  Spacebar - Interact with stations',
        '  Click work orders - Select orders',
        '  P or ESC - Pause/Resume',
        '  H or F1 - Show/Hide this help',
        '  D - Toggle debug mode',
        '',
        'GAMEPLAY:',
        '  1. Select a work order from the right panel',
        '  2. Create CAD program at CAD station',
        '  3. Collect materials from Material Room',
        '  4. Machine part at Machining Center',
        '  5. Pass Quality Control inspection',
        '  6. Ship completed order',
        '',
        'ENEMIES:',
        '  Coworkers (Brown) - Slow you down',
        '  Managers (Red) - Longer delays',
        '  HR (Pink) - Gives PIPs, 3 PIPs = Game Over',
        '',
        'TIPS:',
        '  • Higher difficulty = More points',
        '  • Plan efficient routes',
        '  • Watch order timers carefully',
        '  • Avoid dead ends near enemies',
        '',
        'MAZE SYSTEM:',
        '  • Movement is restricted to horizontal/vertical paths',
        '  • Green arrows show valid movement directions',
        '  • Follow factory corridors between stations',
        '  • Orange intersections are junction points',
        '  • Press M to toggle maze visualization overlay'
    ];
    
    helpText.forEach((line, i) => {
        const y = 100 + i * 18;
        if (line.startsWith('  ')) {
            ctx.fillStyle = '#ccc';
        } else if (line.includes(':')) {
            ctx.fillStyle = '#4CAF50';
        } else {
            ctx.fillStyle = '#fff';
        }
        ctx.fillText(line, 50, y);
    });
    
    ctx.fillStyle = '#4CAF50';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Press H or F1 to close help', canvas.width / 2, canvas.height - 30);
}

function drawBackground() {
    // Draw factory floor pattern
    ctx.fillStyle = '#2a2a2a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid pattern
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    
    const gridSize = 40;
    for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    
    for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
}

function drawPaths() {
    // Draw connection paths between stations
    ctx.strokeStyle = '#444';
    ctx.lineWidth = 8;
    ctx.lineCap = 'round';
    
    // Define paths between stations
    const paths = [
        // CAD to Material
        { from: stations[0], to: stations[1] },
        // CAD to Machine
        { from: stations[0], to: stations[2] },
        // Material to Machine
        { from: stations[1], to: stations[2] },
        // Machine to QC
        { from: stations[2], to: stations[3] },
        // QC to Ship
        { from: stations[3], to: stations[4] },
        // Material to Ship (express path)
        { from: stations[1], to: stations[4] }
    ];
    
    paths.forEach(path => {
        ctx.beginPath();
        ctx.moveTo(path.from.x, path.from.y);
        ctx.lineTo(path.to.x, path.to.y);
        ctx.stroke();
    });
}

function drawMiniGameOverlay() {
    // Semi-transparent overlay
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Mini-game instructions
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`${player.miniGameType.toUpperCase()} STATION`, canvas.width / 2, canvas.height / 2 - 60);
    
    ctx.font = '18px Arial';
    ctx.fillText(`Press SPACEBAR rapidly!`, canvas.width / 2, canvas.height / 2 - 20);
    ctx.fillText(`${player.miniGameProgress} / ${player.miniGameTarget}`, canvas.width / 2, canvas.height / 2 + 20);
    
    // Progress bar
    const barWidth = 300;
    const barHeight = 20;
    const barX = (canvas.width - barWidth) / 2;
    const barY = canvas.height / 2 + 40;
    
    ctx.fillStyle = '#333';
    ctx.fillRect(barX, barY, barWidth, barHeight);
    
    const progress = player.miniGameProgress / player.miniGameTarget;
    ctx.fillStyle = '#4CAF50';
    ctx.fillRect(barX, barY, barWidth * progress, barHeight);
    
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.strokeRect(barX, barY, barWidth, barHeight);
}

function initializeMaze() {
    // Clear existing paths
    mazePaths.nodes = [];
    mazePaths.paths = [];
    mazePaths.grid = {};
    
    // Define grid size for perpendicular paths
    const GRID_SIZE = 50;
    const CORRIDOR_WIDTH = 35;
    
    // Create a grid-based layout where all paths are perpendicular
    // Define main corridors (horizontal and vertical lines)
    const horizontalCorridors = [
        { y: 150, startX: 50, endX: 750 },   // Top corridor
        { y: 300, startX: 100, endX: 700 },  // Middle corridor  
        { y: 450, startX: 50, endX: 750 }    // Bottom corridor
    ];
    
    const verticalCorridors = [
        { x: 150, startY: 100, endY: 500 },  // Left corridor
        { x: 300, startY: 150, endY: 450 },  // Left-center corridor
        { x: 400, startY: 100, endY: 500 },  // Center corridor
        { x: 500, startY: 150, endY: 450 },  // Right-center corridor
        { x: 650, startY: 100, endY: 500 }   // Right corridor
    ];
    
    // Create intersection nodes at corridor crossings
    const intersections = [];
    horizontalCorridors.forEach((hCorridor, hIndex) => {
        verticalCorridors.forEach((vCorridor, vIndex) => {
            // Check if corridors intersect
            if (vCorridor.x >= hCorridor.startX && vCorridor.x <= hCorridor.endX &&
                hCorridor.y >= vCorridor.startY && hCorridor.y <= vCorridor.endY) {
                const intersection = {
                    x: vCorridor.x,
                    y: hCorridor.y,
                    type: 'intersection',
                    id: `h${hIndex}_v${vIndex}`
                };
                intersections.push(intersection);
                mazePaths.nodes.push(intersection);
                
                // Store in grid for quick lookup
                const gridKey = `${intersection.x}_${intersection.y}`;
                mazePaths.grid[gridKey] = intersection;
            }
        });
    });
    
    // Add station nodes and connect them to nearest intersections
    stations.forEach((station, index) => {
        const stationNode = {
            x: station.x,
            y: station.y,
            type: 'station',
            name: station.name,
            id: `station_${index}`
        };
        mazePaths.nodes.push(stationNode);
        
        // Find the nearest intersection to each station
        let nearestIntersection = null;
        let nearestDistance = Infinity;
        
        intersections.forEach(intersection => {
            const dist = distance(station.x, station.y, intersection.x, intersection.y);
            if (dist < nearestDistance) {
                nearestDistance = dist;
                nearestIntersection = intersection;
            }
        });
        
        // Create perpendicular connection from station to nearest intersection
        if (nearestIntersection) {
            // Connect via perpendicular path (either horizontal first then vertical, or vice versa)
            const dx = Math.abs(station.x - nearestIntersection.x);
            const dy = Math.abs(station.y - nearestIntersection.y);
            
            if (dx > 10 && dy > 10) {
                // Create intermediate node for L-shaped connection
                const intermediateX = station.x;
                const intermediateY = nearestIntersection.y;
                
                const intermediate = {
                    x: intermediateX,
                    y: intermediateY,
                    type: 'corner',
                    id: `corner_${station.name}`
                };
                mazePaths.nodes.push(intermediate);
                
                // Station to intermediate (vertical)
                mazePaths.paths.push({
                    start: stationNode,
                    end: intermediate,
                    direction: station.y < intermediateY ? 'down' : 'up',
                    width: CORRIDOR_WIDTH
                });
                
                // Intermediate to intersection (horizontal)
                mazePaths.paths.push({
                    start: intermediate,
                    end: nearestIntersection,
                    direction: station.x < nearestIntersection.x ? 'right' : 'left',
                    width: CORRIDOR_WIDTH
                });
            } else {
                // Direct perpendicular connection
                let direction;
                if (dx > dy) {
                    direction = station.x < nearestIntersection.x ? 'right' : 'left';
                } else {
                    direction = station.y < nearestIntersection.y ? 'down' : 'up';
                }
                
                mazePaths.paths.push({
                    start: stationNode,
                    end: nearestIntersection,
                    direction: direction,
                    width: CORRIDOR_WIDTH
                });
            }
        }
    });
    
    // Create perpendicular paths between intersections
    intersections.forEach(intersection => {
        // Connect horizontally to adjacent intersections
        const rightIntersection = intersections.find(other => 
            other.y === intersection.y && other.x > intersection.x &&
            !intersections.some(middle => 
                middle.y === intersection.y && 
                middle.x > intersection.x && 
                middle.x < other.x
            )
        );
        
        if (rightIntersection) {
            mazePaths.paths.push({
                start: intersection,
                end: rightIntersection,
                direction: 'right',
                width: CORRIDOR_WIDTH
            });
        }
        
        // Connect vertically to adjacent intersections
        const downIntersection = intersections.find(other => 
            other.x === intersection.x && other.y > intersection.y &&
            !intersections.some(middle => 
                middle.x === intersection.x && 
                middle.y > intersection.y && 
                middle.y < other.y
            )
        );
        
        if (downIntersection) {
            mazePaths.paths.push({
                start: intersection,
                end: downIntersection,
                direction: 'down',
                width: CORRIDOR_WIDTH
            });
        }
    });
    
    console.log(`Perpendicular maze initialized with ${mazePaths.nodes.length} nodes and ${mazePaths.paths.length} paths`);
}

function drawMaze() {
    ctx.save();
    
    // Draw factory floor background
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw perpendicular paths with factory aesthetic
    mazePaths.paths.forEach(path => {
        const isHorizontal = path.direction === 'left' || path.direction === 'right';
        const isVertical = path.direction === 'up' || path.direction === 'down';
        
        if (isHorizontal) {
            // Draw horizontal corridor
            const y = path.start.y;
            const startX = Math.min(path.start.x, path.end.x);
            const endX = Math.max(path.start.x, path.end.x);
            const halfWidth = path.width / 2;
            
            // Factory floor
            ctx.fillStyle = '#333';
            ctx.fillRect(startX, y - halfWidth, endX - startX, path.width);
            
            // Top and bottom walls
            ctx.fillStyle = '#666';
            ctx.fillRect(startX, y - halfWidth - 3, endX - startX, 3); // Top wall
            ctx.fillRect(startX, y + halfWidth, endX - startX, 3); // Bottom wall
            
            // Center guideline
            ctx.strokeStyle = '#555';
            ctx.lineWidth = 2;
            ctx.setLineDash([15, 10]);
            ctx.beginPath();
            ctx.moveTo(startX, y);
            ctx.lineTo(endX, y);
            ctx.stroke();
            
        } else if (isVertical) {
            // Draw vertical corridor
            const x = path.start.x;
            const startY = Math.min(path.start.y, path.end.y);
            const endY = Math.max(path.start.y, path.end.y);
            const halfWidth = path.width / 2;
            
            // Factory floor
            ctx.fillStyle = '#333';
            ctx.fillRect(x - halfWidth, startY, path.width, endY - startY);
            
            // Left and right walls
            ctx.fillStyle = '#666';
            ctx.fillRect(x - halfWidth - 3, startY, 3, endY - startY); // Left wall
            ctx.fillRect(x + halfWidth, startY, 3, endY - startY); // Right wall
            
            // Center guideline
            ctx.strokeStyle = '#555';
            ctx.lineWidth = 2;
            ctx.setLineDash([15, 10]);
            ctx.beginPath();
            ctx.moveTo(x, startY);
            ctx.lineTo(x, endY);
            ctx.stroke();
        }
    });
    
    ctx.setLineDash([]);
    
    // Draw intersections with factory-style design
    mazePaths.nodes.forEach(node => {
        if (node.type === 'intersection') {
            const size = 40;
            
            // Intersection floor
            ctx.fillStyle = '#444';
            ctx.fillRect(node.x - size/2, node.y - size/2, size, size);
            
            // Industrial junction marker
            ctx.fillStyle = '#777';
            ctx.beginPath();
            ctx.arc(node.x, node.y, 12, 0, Math.PI * 2);
            ctx.fill();
            
            // Warning stripes around intersection
            ctx.strokeStyle = '#ff6b00';
            ctx.lineWidth = 3;
            ctx.setLineDash([8, 8]);
            ctx.strokeRect(node.x - size/2 + 2, node.y - size/2 + 2, size - 4, size - 4);
            
        } else if (node.type === 'corner') {
            // Corner junction markers
            ctx.fillStyle = '#555';
            ctx.beginPath();
            ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.strokeStyle = '#777';
            ctx.lineWidth = 2;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.arc(node.x, node.y, 15, 0, Math.PI * 2);
            ctx.stroke();
        }
    });
    
    ctx.setLineDash([]);
    
    // Add factory grid pattern for authenticity
    ctx.strokeStyle = 'rgba(100, 100, 100, 0.1)';
    ctx.lineWidth = 1;
    const gridSize = 25;
    
    for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    
    for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
    
    // Add hazard warnings at dead ends
    mazePaths.nodes.forEach(node => {
        if (node.type === 'station') {
            const connectedPaths = mazePaths.paths.filter(path => 
                path.start === node || path.end === node
            );
            
            if (connectedPaths.length === 1) {
                // Dead end - add warning
                ctx.fillStyle = '#ff3030';
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('⚠', node.x, node.y - 30);
            }
        }
    });
    
    ctx.restore();
}

function drawMazeOverlay() {
    if (!showMazeOverlay) return;
    
    ctx.save();
    
    // Semi-transparent overlay to highlight the maze structure
    ctx.fillStyle = 'rgba(0, 255, 255, 0.1)';
    
    // Highlight all valid paths
    mazePaths.paths.forEach(path => {
        const isHorizontal = path.direction === 'left' || path.direction === 'right';
        const halfWidth = path.width / 2;
        
        if (isHorizontal) {
            const y = path.start.y;
            const startX = Math.min(path.start.x, path.end.x);
            const endX = Math.max(path.start.x, path.end.x);
            
            ctx.fillRect(startX, y - halfWidth, endX - startX, path.width);
        } else {
            const x = path.start.x;
            const startY = Math.min(path.start.y, path.end.y);
            const endY = Math.max(path.start.y, path.end.y);
            
            ctx.fillRect(x - halfWidth, startY, path.width, endY - startY);
        }
    });
    
    // Draw path direction indicators
    ctx.fillStyle = '#00ffff';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    
    mazePaths.paths.forEach(path => {
        const midX = (path.start.x + path.end.x) / 2;
        const midY = (path.start.y + path.end.y) / 2;
        
        let arrow = '';
        switch (path.direction) {
            case 'up': arrow = '↑'; break;
            case 'down': arrow = '↓'; break;
            case 'left': arrow = '←'; break;
            case 'right': arrow = '→'; break;
        }
        
        ctx.fillText(arrow, midX, midY + 6);
    });
    
    // Highlight intersections
    ctx.fillStyle = '#ff00ff';
    mazePaths.nodes.forEach(node => {
        if (node.type === 'intersection') {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 10px Arial';
            ctx.fillText('INT', node.x, node.y + 3);
            ctx.fillStyle = '#ff00ff';
        } else if (node.type === 'corner') {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 15, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 8px Arial';
            ctx.fillText('COR', node.x, node.y + 2);
            ctx.fillStyle = '#ff00ff';
        }
    });
    
    // Show connection lines between nodes
    ctx.strokeStyle = '#ffff00';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    
    mazePaths.paths.forEach(path => {
        ctx.beginPath();
        ctx.moveTo(path.start.x, path.start.y);
        ctx.lineTo(path.end.x, path.end.y);
        ctx.stroke();
    });
    
    ctx.setLineDash([]);
    ctx.restore();
}

// Add wall collision detection for better perpendicular path enforcement
function getWallCollisions(x, y, radius = 15) {
    const walls = [];
    
    // Check if player would hit a wall (area not covered by paths)
    if (!isOnPath(x, y)) {
        // Find nearby paths to determine wall directions
        const nearbyPaths = mazePaths.paths.filter(path => {
            const pathDistance = getDistanceToPath(x, y, path);
            return pathDistance < 50; // Within 50 pixels
        });
        
        nearbyPaths.forEach(path => {
            const isHorizontal = path.direction === 'left' || path.direction === 'right';
            const halfWidth = path.width / 2;
            
            if (isHorizontal) {
                const pathY = path.start.y;
                const startX = Math.min(path.start.x, path.end.x);
                const endX = Math.max(path.start.x, path.end.x);
                
                // Check if player is near this horizontal path
                if (x >= startX - 20 && x <= endX + 20) {
                    if (y < pathY - halfWidth && y > pathY - halfWidth - 30) {
                        walls.push({ type: 'horizontal', side: 'top', pathY: pathY - halfWidth });
                    }
                    if (y > pathY + halfWidth && y < pathY + halfWidth + 30) {
                        walls.push({ type: 'horizontal', side: 'bottom', pathY: pathY + halfWidth });
                    }
                }
            } else {
                const x = path.start.x;
                const startY = Math.min(path.start.y, path.end.y);
                const endY = Math.max(path.start.y, path.end.y);
                
                // Check if player is near this vertical path
                if (y >= startY - 20 && y <= endY + 20) {
                    if (x < pathX - halfWidth && x > pathX - halfWidth - 30) {
                        walls.push({ type: 'vertical', side: 'left', pathX: pathX - halfWidth });
                    }
                    if (x > pathX + halfWidth && x < pathX + halfWidth + 30) {
                        walls.push({ type: 'vertical', side: 'right', pathX: pathX + halfWidth });
                    }
                }
            }
        });
    }
    
    return walls;
}

function getDistanceToPath(x, y, path) {
    const isHorizontal = path.direction === 'left' || path.direction === 'right';
    
    if (isHorizontal) {
        const pathY = path.start.y;
        const startX = Math.min(path.start.x, path.end.x);
        const endX = Math.max(path.start.x, path.end.x);
        
        if (x >= startX && x <= endX) {
            return Math.abs(y - pathY);
        } else {
            const distToStart = Math.sqrt((x - startX) ** 2 + (y - pathY) ** 2);
            const distToEnd = Math.sqrt((x - endX) ** 2 + (y - pathY) ** 2);
            return Math.min(distToStart, distToEnd);
        }
    } else {
        const pathX = path.start.x;
        const startY = Math.min(path.start.y, path.end.y);
        const endY = Math.max(path.start.y, path.end.y);
        
        if (y >= startY && y <= endY) {
            return Math.abs(x - pathX);
        } else {
            const distToStart = Math.sqrt((x - pathX) ** 2 + (y - startY) ** 2);
            const distToEnd = Math.sqrt((x - pathX) ** 2 + (y - endY) ** 2);
            return Math.min(distToStart, distToEnd);
        }
    }
}

// Enhanced path validation with smooth transitions
function findNearestValidPosition(x, y) {
    let nearestPoint = null;
    let nearestDistance = Infinity;
    
    // Check all paths for the nearest valid position
    mazePaths.paths.forEach(path => {
        const isHorizontal = path.direction === 'left' || path.direction === 'right';
        const halfWidth = path.width / 2;
        
        if (isHorizontal) {
            const pathY = path.start.y;
            const startX = Math.min(path.start.x, path.end.x);
            const endX = Math.max(path.start.x, path.end.x);
            
            // Clamp x to path bounds
            const clampedX = Math.max(startX, Math.min(endX, x));
            const candidatePoint = { x: clampedX, y: pathY };
            
            const dist = distance(x, y, candidatePoint.x, candidatePoint.y);
            if (dist < nearestDistance) {
                nearestDistance = dist;
                nearestPoint = candidatePoint;
            }
        } else {
            const pathX = path.start.x;
            const startY = Math.min(path.start.y, path.end.y);
            const endY = Math.max(path.start.y, path.end.y);
            
            // Clamp y to path bounds
            const clampedY = Math.max(startY, Math.min(endY, y));
            const candidatePoint = { x: pathX, y: clampedY };
            
            const dist = distance(x, y, candidatePoint.x, candidatePoint.y);
            if (dist < nearestDistance) {
                nearestDistance = dist;
                nearestPoint = candidatePoint;
            }
        }
    });
    
    // Also check intersections and corners
    mazePaths.nodes.forEach(node => {
        if (node.type === 'intersection' || node.type === 'corner') {
            const dist = distance(x, y, node.x, node.y);
            if (dist < nearestDistance) {
                nearestDistance = dist;
                nearestPoint = { x: node.x, y: node.y };
            }
        }
    });
    
    return nearestPoint;
}

// Toggle pause state
function togglePause() {
    gamePaused = !gamePaused;
    gameState.gameRunning = !gamePaused;
    
    if (gamePaused) {
        showMessage('Game Paused - Press P to resume', 'info');
    } else {
        showMessage('Game Resumed', 'info');
    }
}

// Add key handlers
document.addEventListener('keydown', (e) => {
    if (e.key === 'p' || e.key === 'P') {
        togglePause();
    }
    if (e.key === 'Escape') {
        togglePause();
    }
    if (e.key === 'd' || e.key === 'D') {
        debugMode = !debugMode;
        showMessage(`Debug mode: ${debugMode ? 'ON' : 'OFF'}`, 'info');
    }
    if (e.key === 'h' || e.key === 'H' || e.key === 'F1') {
        showHelp = !showHelp;
        e.preventDefault();
    }
    if (e.key === 'm' || e.key === 'M') {
        showMazeOverlay = !showMazeOverlay;
        e.preventDefault();
    }
});

// Game over function
function gameOver(message) {
    gameState.gameRunning = false;
    document.getElementById('gameOverMessage').textContent = message;
    document.getElementById('gameOver').style.display = 'block';
    
    // Save high score
    saveHighScore();
}

async function saveHighScore() {
    const highScore = parseInt(localStorage.getItem('machinistRunnerHighScore') || '0');
    
    if (gameState.score > highScore) {
        localStorage.setItem('machinistRunnerHighScore', gameState.score.toString());
        showMessage('New high score!', 'success');
        
        // Try to submit to backend
        try {
            const playerName = prompt('New high score! Enter your name:') || 'Anonymous';
            const response = await fetch('http://localhost:3001/api/highscores', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: playerName,
                    score: gameState.score,
                    level: gameState.level
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showMessage(`High score saved! Rank: #${result.rank}`, 'success');
            }
        } catch (error) {
            console.log('Could not save to server, using local storage only');
        }
    }
}

async function loadHighScores() {
    try {
        const response = await fetch('http://localhost:3001/api/highscores');
        if (response.ok) {
            const scores = await response.json();
            if (scores.length > 0) {
                showMessage(`Server High Score: ${scores[0].score} by ${scores[0].name}`, 'info');
            }
        }
    } catch (error) {
        // Fallback to local storage
        const highScore = localStorage.getItem('machinistRunnerHighScore');
        if (highScore) {
            showMessage(`Local High Score: ${highScore}`, 'info');
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    initGame();
    updateUI();
    loadHighScores();
});

// Critical missing function: isOnPath
function isOnPath(x, y) {
    // Check if point is on any perpendicular path
    return mazePaths.paths.some(path => {
        const isHorizontal = path.direction === 'left' || path.direction === 'right';
        const isVertical = path.direction === 'up' || path.direction === 'down';
        const halfWidth = path.width / 2;
        
        if (isHorizontal) {
            // Check horizontal path
            const pathY = path.start.y;
            const startX = Math.min(path.start.x, path.end.x);
            const endX = Math.max(path.start.x, path.end.x);
            
            return (x >= startX - 5 && x <= endX + 5 && 
                    y >= pathY - halfWidth && y <= pathY + halfWidth);
                    
        } else if (isVertical) {
            // Check vertical path
            const pathX = path.start.x;
            const startY = Math.min(path.start.y, path.end.y);
            const endY = Math.max(path.start.y, path.end.y);
            
            return (y >= startY - 5 && y <= endY + 5 && 
                    x >= pathX - halfWidth && x <= pathX + halfWidth);
        }
        
        return false;
    });
}