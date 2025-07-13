
const stations = [
    {
        name: 'CAD',
        action: 'cad',
        x: 150,  // Aligned with left vertical corridor
        y: 80,   // Above top horizontal corridor
        width: 80,
        height: 60,
        color: '#2196F3',
        description: 'Create CAD programs'
    },
    {
        name: 'Material',
        action: 'material',
        x: 650,  // Aligned with right vertical corridor
        y: 80,   // Above top horizontal corridor
        width: 80,
        height: 60,
        color: '#FF9800',
        description: 'Collect materials'
    },
    {
        name: 'Machine',
        action: 'machine',
        x: 150,  // Aligned with left vertical corridor
        y: 520,  // Below bottom horizontal corridor
        width: 80,
        height: 60,
        color: '#9C27B0',
        description: 'Machine parts'
    },
    {
        name: 'QC',
        action: 'qc',
        x: 400,  // Aligned with center vertical corridor
        y: 520,  // Below bottom horizontal corridor
        width: 80,
        height: 60,
        color: '#F44336',
        description: 'Quality control'
    },
    {
        name: 'Ship',
        action: 'ship',
        x: 650,  // Aligned with right vertical corridor
        y: 520,  // Below bottom horizontal corridor
        width: 80,
        height: 60,
        color: '#4CAF50',
        description: 'Ship orders'
    }
];

function createStations() {
    return stations;
}

function drawStations(ctx) {
    stations.forEach(station => {
        // Check if player is near this station
        const playerNear = player && player.distanceTo(station.x, station.y) < 50;
        
        // Draw station platform
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(
            station.x - station.width/2 - 5, 
            station.y - station.height/2 - 5, 
            station.width + 10, 
            station.height + 10
        );

        // Draw interaction glow if player is near
        if (playerNear) {
            ctx.shadowColor = station.color;
            ctx.shadowBlur = 20;
            ctx.fillStyle = station.color + '30';
            ctx.fillRect(
                station.x - station.width/2 - 10, 
                station.y - station.height/2 - 10, 
                station.width + 20, 
                station.height + 20
            );
            ctx.shadowBlur = 0;
        }

        // Draw station background with gradient effect
        const gradient = ctx.createLinearGradient(
            station.x - station.width/2, station.y - station.height/2,
            station.x + station.width/2, station.y + station.height/2
        );
        gradient.addColorStop(0, station.color);
        gradient.addColorStop(1, station.color + '80');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(
            station.x - station.width/2, 
            station.y - station.height/2, 
            station.width, 
            station.height
        );

        // Draw station border with enhanced glow if player is near
        ctx.shadowColor = station.color;
        ctx.shadowBlur = playerNear ? 15 : 10;
        ctx.strokeStyle = playerNear ? '#fff' : '#ccc';
        ctx.lineWidth = playerNear ? 4 : 3;
        ctx.strokeRect(
            station.x - station.width/2, 
            station.y - station.height/2, 
            station.width, 
            station.height
        );
        ctx.shadowBlur = 0;

        // Draw station icon based on type
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        
        const icons = {
            'CAD': '🖥️',
            'Material': '📦',
            'Machine': '⚙️',
            'QC': '🔍',
            'Ship': '🚚'
        };
        
        ctx.fillText(icons[station.name] || station.name, station.x, station.y - 5);
        
        // Draw station name
        ctx.font = 'bold 10px Arial';
        ctx.fillText(station.name, station.x, station.y + 15);

        // Draw description below
        ctx.font = '8px Arial';
        ctx.fillStyle = playerNear ? '#fff' : '#ccc';
        ctx.fillText(station.description, station.x, station.y + station.height/2 + 15);
        
        // Draw requirement indicator if player has selected order
        if (playerNear && gameState.currentOrder) {
            const order = gameState.currentOrder;
            let canInteract = false;
            let statusText = '';
            
            switch (station.action) {
                case 'cad':
                    canInteract = !order.steps.cad;
                    statusText = order.steps.cad ? '✅ Done' : '🖥️ Create CAD';
                    break;
                case 'material':
                    canInteract = gameState.material < order.materialNeeded;
                    statusText = `📦 Need ${order.materialNeeded - gameState.material} more`;
                    break;
                case 'machine':
                    canInteract = order.canProgress('machine') && !order.steps.machined;
                    statusText = canInteract ? '⚙️ Machine Part' : '❌ Need CAD + Materials';
                    break;
                case 'qc':
                    canInteract = order.canProgress('qc') && !order.steps.qc;
                    statusText = canInteract ? '🔍 Quality Check' : '❌ Need Machined Part';
                    break;
                case 'ship':
                    canInteract = order.canProgress('ship') && !order.steps.shipped;
                    statusText = canInteract ? '🚚 Ship Order' : '❌ Need QC Pass';
                    break;
            }
            
            ctx.font = '9px Arial';
            ctx.fillStyle = canInteract ? '#4CAF50' : '#FF5722';
            ctx.fillText(statusText, station.x, station.y + station.height/2 + 28);
        }
    });
}

function getStationAt(x, y) {
    return stations.find(station => {
        const dx = Math.abs(x - station.x);
        const dy = Math.abs(y - station.y);
        return dx < station.width/2 && dy < station.height/2;
    });
}