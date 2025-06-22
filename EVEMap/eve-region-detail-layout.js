class RegionDetailLayout {
    constructor() {
        this.constellationLayouts = new Map();
        this.systemLayouts = new Map();
    }
    
    layoutRegion(regionData, canvasWidth, canvasHeight) {
        // Create a grid-based layout for constellations
        const constellations = regionData.constellations || [];
        const constellationMap = new Map();
        
        // Calculate grid dimensions
        const cols = Math.ceil(Math.sqrt(constellations.length * 1.5));
        const rows = Math.ceil(constellations.length / cols);
        
        // Cell dimensions with padding
        const cellWidth = canvasWidth / (cols + 1);
        const cellHeight = canvasHeight / (rows + 1);
        const padding = 0.2; // 20% padding
        
        // Layout each constellation
        constellations.forEach((constellation, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            
            const x = (col + 1) * cellWidth;
            const y = (row + 1) * cellHeight;
            
            constellationMap.set(constellation.id, {
                x: x,
                y: y,
                width: cellWidth * (1 - padding),
                height: cellHeight * (1 - padding),
                systems: this.layoutConstellation(constellation, cellWidth * (1 - padding), cellHeight * (1 - padding))
            });
        });
        
        return constellationMap;
    }
    
    layoutConstellation(constellation, width, height) {
        const systems = constellation.systems || [];
        const systemMap = new Map();
        
        if (systems.length === 0) return systemMap;
        
        // Use different layouts based on system count
        if (systems.length <= 6) {
            // Hexagonal layout for small constellations
            return this.hexagonalLayout(systems, width, height);
        } else if (systems.length <= 12) {
            // Circular layout for medium constellations
            return this.circularLayout(systems, width, height);
        } else {
            // Grid layout for large constellations
            return this.gridLayout(systems, width, height);
        }
    }
    
    hexagonalLayout(systems, width, height) {
        const systemMap = new Map();
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) * 0.3;
        
        systems.forEach((system, index) => {
            let x, y;
            
            if (index === 0) {
                // Center system
                x = centerX;
                y = centerY;
            } else {
                // Surrounding systems
                const angle = ((index - 1) / (systems.length - 1)) * Math.PI * 2;
                x = centerX + Math.cos(angle) * radius;
                y = centerY + Math.sin(angle) * radius;
            }
            
            systemMap.set(system.id, { x, y, radius: 5 });
        });
        
        return systemMap;
    }
    
    circularLayout(systems, width, height) {
        const systemMap = new Map();
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) * 0.35;
        
        systems.forEach((system, index) => {
            const angle = (index / systems.length) * Math.PI * 2;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            
            systemMap.set(system.id, { x, y, radius: 4 });
        });
        
        return systemMap;
    }
    
    gridLayout(systems, width, height) {
        const systemMap = new Map();
        const cols = Math.ceil(Math.sqrt(systems.length));
        const rows = Math.ceil(systems.length / cols);
        
        const cellWidth = width / cols;
        const cellHeight = height / rows;
        
        systems.forEach((system, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            
            const x = (col + 0.5) * cellWidth;
            const y = (row + 0.5) * cellHeight;
            
            systemMap.set(system.id, { x, y, radius: 3 });
        });
        
        return systemMap;
    }
    
    // Calculate connections between systems
    calculateConnections(regionData, layoutMap) {
        const connections = [];
        
        // For each constellation
        layoutMap.forEach((constLayout, constId) => {
            const constellation = regionData.constellations.find(c => c.id === constId);
            if (!constellation) return;
            
            // Check connections between systems
            constellation.systems.forEach(system => {
                system.connections?.forEach(targetId => {
                    // Find target system in any constellation
                    layoutMap.forEach((targetConstLayout, targetConstId) => {
                        if (targetConstLayout.systems.has(targetId)) {
                            connections.push({
                                from: { constId, systemId: system.id },
                                to: { constId: targetConstId, systemId: targetId }
                            });
                        }
                    });
                });
            });
        });
        
        return connections;
    }
}

window.RegionDetailLayout = RegionDetailLayout;