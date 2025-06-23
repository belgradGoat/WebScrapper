// EVE Region Detail Layout Engine - Subway Map Style with proper graph layout

class RegionDetailLayout {
    constructor() {
        this.gridSize = 100;
        this.nodeSpacing = 80;
        this.lineStyles = {
            highsec: { color: '#00ff00', width: 6, glow: true },
            lowsec: { color: '#ffaa00', width: 6, glow: true },
            nullsec: { color: '#ff4444', width: 6, glow: true },
            wormhole: { color: '#ff00ff', width: 6, glow: true }
        };
        this.stationRadius = {
            hub: 14,      // Major trade hubs
            standard: 10,  // Normal systems
            terminal: 8   // Dead-end systems
        };
    }

    // Update the layoutRegion method in eve-region-detail-layout-engine.js

// Replace the layoutRegion method in eve-region-detail-layout-engine.js with this fixed version:

layoutRegion(regionData, maxWidth, maxHeight) {
    // First, build a complete graph of all systems in the region
    const allSystems = [];
    const systemToConstellation = new Map();
    
    // Collect all systems
    regionData.constellations.forEach(constellation => {
        constellation.systems.forEach(system => {
            allSystems.push(system);
            systemToConstellation.set(system.id, constellation.id);
        });
    });
    
    console.log(`Layout region with ${allSystems.length} systems`);
    
    // Build adjacency map from actual connections in the universe data
    const adjacency = new Map();
    allSystems.forEach(system => {
        adjacency.set(system.id, new Set());
    });
    
    // Get all system IDs in this region
    const regionSystemIds = new Set(allSystems.map(s => s.id));
    
    // Use the universe connections data to build proper adjacency
    let connectionCount = 0;
    if (window.map && window.map.universeData && window.map.universeData.connections) {
        window.map.universeData.connections.forEach(conn => {
            // The connection object has 'from' and 'to' properties with system IDs
            const fromId = typeof conn.from === 'object' ? conn.from : parseInt(conn.from);
            const toId = typeof conn.to === 'object' ? conn.to : parseInt(conn.to);
            
            if (regionSystemIds.has(fromId) && regionSystemIds.has(toId)) {
                adjacency.get(fromId).add(toId);
                adjacency.get(toId).add(fromId);
                connectionCount++;
            }
        });
        
        console.log(`Built adjacency map with ${connectionCount} connections in this region`);
    } else {
        console.warn('No universe connections data available');
    }
    
    // Log connection statistics
    let isolatedCount = 0;
    let hubCount = 0;
    adjacency.forEach((neighbors, sysId) => {
        if (neighbors.size === 0) {
            isolatedCount++;
        } else if (neighbors.size >= 4) {
            hubCount++;
        }
    });
    console.log(`Systems: ${isolatedCount} isolated, ${hubCount} hubs`);
    
    // Use force-directed layout for initial positioning
    const positions = this.forceDirectedLayout(allSystems, adjacency);
    
    // Then apply subway-style constraints
    const subwayPositions = this.applySubwayConstraints(positions, adjacency);
    
    // Group by constellation
    const constellationLayouts = new Map();
    
    regionData.constellations.forEach(constellation => {
        const constSystems = new Map();
        
        constellation.systems.forEach(system => {
            const pos = subwayPositions.get(system.id);
            if (pos) {
                constSystems.set(system.id, {
                    x: pos.x,
                    y: pos.y,
                    radius: this.getSystemRadiusFromConnections(system.id, adjacency),
                    onMainRoute: pos.onMainRoute || false,
                    system: system
                });
            }
        });
        
        // Calculate constellation bounds
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        
        constSystems.forEach(sys => {
            minX = Math.min(minX, sys.x);
            maxX = Math.max(maxX, sys.x);
            minY = Math.min(minY, sys.y);
            maxY = Math.max(maxY, sys.y);
        });
        
        // Add padding
        const padding = 100;
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        
        constellationLayouts.set(constellation.id, {
            x: centerX,
            y: centerY,
            width: Math.max(maxX - minX + padding * 2, 200),
            height: Math.max(maxY - minY + padding * 2, 200),
            systems: constSystems,
            constellation: constellation
        });
    });
    
    return constellationLayouts;
}

    // Update the forceDirectedLayout method to better handle isolated systems

forceDirectedLayout(systems, adjacency) {
    const positions = new Map();
    const velocities = new Map();
    
    // Initialize positions in a grid to avoid overlap
    const cols = Math.ceil(Math.sqrt(systems.length));
    systems.forEach((system, index) => {
        const row = Math.floor(index / cols);
        const col = index % cols;
        positions.set(system.id, {
            x: col * this.nodeSpacing * 2 - (cols * this.nodeSpacing),
            y: row * this.nodeSpacing * 2 - (cols * this.nodeSpacing)
        });
        velocities.set(system.id, { x: 0, y: 0 });
    });
    
    // Force-directed iterations - fewer for better performance
    const iterations = 50;
    const idealDistance = this.nodeSpacing * 1.5;
    const repulsionStrength = 8000;
    const attractionStrength = 0.05;
    const damping = 0.85;
    
    for (let iter = 0; iter < iterations; iter++) {
        // Calculate forces
        const forces = new Map();
        systems.forEach(sys => {
            forces.set(sys.id, { x: 0, y: 0 });
        });
        
        // Repulsion between all nodes
        for (let i = 0; i < systems.length; i++) {
            for (let j = i + 1; j < systems.length; j++) {
                const sys1 = systems[i];
                const sys2 = systems[j];
                const pos1 = positions.get(sys1.id);
                const pos2 = positions.get(sys2.id);
                
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const dist = Math.sqrt(dx * dx + dy * dy) + 0.001;
                
                // Only apply repulsion within reasonable distance
                if (dist < idealDistance * 3) {
                    const force = repulsionStrength / (dist * dist);
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    
                    forces.get(sys1.id).x -= fx;
                    forces.get(sys1.id).y -= fy;
                    forces.get(sys2.id).x += fx;
                    forces.get(sys2.id).y += fy;
                }
            }
        }
        
        // Attraction along edges
        adjacency.forEach((neighbors, sysId) => {
            const pos1 = positions.get(sysId);
            neighbors.forEach(neighborId => {
                const pos2 = positions.get(neighborId);
                if (!pos2) return;
                
                const dx = pos2.x - pos1.x;
                const dy = pos2.y - pos1.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist > idealDistance) {
                    const force = (dist - idealDistance) * attractionStrength;
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    
                    forces.get(sysId).x += fx;
                    forces.get(sysId).y += fy;
                }
            });
        });
        
        // Update positions
        systems.forEach(system => {
            const vel = velocities.get(system.id);
            const force = forces.get(system.id);
            const pos = positions.get(system.id);
            
            vel.x = (vel.x + force.x) * damping;
            vel.y = (vel.y + force.y) * damping;
            
            pos.x += vel.x;
            pos.y += vel.y;
        });
    }
    
    return positions;
}

    applySubwayConstraints(positions, adjacency) {
        // Find main routes (paths with high connectivity)
        const mainRoutes = this.findMainRoutes(adjacency);
        const subwayPositions = new Map();
        
        // Snap positions to grid angles (0°, 45°, 90°, etc.)
        positions.forEach((pos, sysId) => {
            const neighbors = Array.from(adjacency.get(sysId) || []);
            
            if (neighbors.length === 0) {
                // Isolated system
                subwayPositions.set(sysId, {
                    x: Math.round(pos.x / this.gridSize) * this.gridSize,
                    y: Math.round(pos.y / this.gridSize) * this.gridSize,
                    onMainRoute: false
                });
                return;
            }
            
            // Calculate average angle to neighbors
            let avgAngle = 0;
            let angleCount = 0;
            
            neighbors.forEach(neighborId => {
                const nPos = positions.get(neighborId);
                if (nPos) {
                    const angle = Math.atan2(nPos.y - pos.y, nPos.x - pos.x);
                    avgAngle += angle;
                    angleCount++;
                }
            });
            
            if (angleCount > 0) {
                avgAngle /= angleCount;
                
                // Snap to nearest 45-degree angle
                const snapAngle = Math.round(avgAngle * 4 / Math.PI) * Math.PI / 4;
                
                // Adjust position based on snapped angle
                const adjustedX = Math.round(pos.x / this.gridSize) * this.gridSize;
                const adjustedY = Math.round(pos.y / this.gridSize) * this.gridSize;
                
                subwayPositions.set(sysId, {
                    x: adjustedX,
                    y: adjustedY,
                    onMainRoute: mainRoutes.has(sysId)
                });
            } else {
                subwayPositions.set(sysId, {
                    x: pos.x,
                    y: pos.y,
                    onMainRoute: false
                });
            }
        });
        
        // Straighten main routes
        mainRoutes.forEach(route => {
            this.straightenRoute(route, subwayPositions, adjacency);
        });
        
        return subwayPositions;
    }

    findMainRoutes(adjacency) {
        const routes = new Set();
        const visited = new Set();
        
        // Find high-degree nodes (hubs)
        const hubs = [];
        adjacency.forEach((neighbors, sysId) => {
            if (neighbors.size >= 4) {
                hubs.push({ id: sysId, degree: neighbors.size });
            }
        });
        
        // Sort by degree
        hubs.sort((a, b) => b.degree - a.degree);
        
        // Find paths between major hubs
        hubs.slice(0, 5).forEach(hub => {
            const path = this.bfs(hub.id, adjacency, visited);
            path.forEach(sysId => routes.add(sysId));
        });
        
        return routes;
    }

    bfs(startId, adjacency, globalVisited) {
        const visited = new Set();
        const queue = [startId];
        const path = [];
        
        while (queue.length > 0 && path.length < 20) {
            const current = queue.shift();
            if (visited.has(current)) continue;
            
            visited.add(current);
            globalVisited.add(current);
            path.push(current);
            
            // Add unvisited neighbors
            const neighbors = adjacency.get(current) || new Set();
            neighbors.forEach(neighborId => {
                if (!visited.has(neighborId) && !globalVisited.has(neighborId)) {
                    queue.push(neighborId);
                }
            });
        }
        
        return path;
    }

    straightenRoute(route, positions, adjacency) {
        // Align systems on main routes to create straighter lines
        if (route.length < 3) return;
        
        for (let i = 1; i < route.length - 1; i++) {
            const prev = positions.get(route[i - 1]);
            const curr = positions.get(route[i]);
            const next = positions.get(route[i + 1]);
            
            if (!prev || !curr || !next) continue;
            
            // Calculate if we should align horizontally, vertically, or diagonally
            const dx = next.x - prev.x;
            const dy = next.y - prev.y;
            const angle = Math.atan2(dy, dx);
            
            // Snap to nearest 45-degree angle
            const snapAngle = Math.round(angle * 4 / Math.PI) * Math.PI / 4;
            
            // Interpolate position along the snapped angle
            const t = 0.5; // Middle position
            curr.x = prev.x + Math.cos(snapAngle) * Math.abs(dx) * t;
            curr.y = prev.y + Math.sin(snapAngle) * Math.abs(dy) * t;
        }
    }

    getSystemRadiusFromConnections(systemId, adjacency) {
        const degree = adjacency.get(systemId)?.size || 0;
        
        if (degree === 0) return this.stationRadius.terminal;
        if (degree === 1) return this.stationRadius.terminal;
        if (degree >= 4) return this.stationRadius.hub;
        return this.stationRadius.standard;
    }

    // Replace the calculateConnections method in eve-region-detail-layout-engine.js

// Replace calculateConnections method in eve-region-detail-layout-engine.js:

calculateConnections(regionData, regionLayout) {
    const connections = [];
    const processedPairs = new Set();
    
    // Get all system IDs in this region
    const regionSystemIds = new Set();
    regionData.constellations.forEach(constellation => {
        constellation.systems.forEach(system => {
            regionSystemIds.add(system.id);
        });
    });
    
    console.log(`Region has ${regionSystemIds.size} systems`);
    
    // Use universe connections data if available
    if (window.map && window.map.universeData && window.map.universeData.connections) {
        let totalConnections = 0;
        let regionConnections = 0;
        
        window.map.universeData.connections.forEach(conn => {
            totalConnections++;
            
            // Parse connection IDs (they might be strings or numbers)
            const fromId = typeof conn.from === 'object' ? conn.from : parseInt(conn.from);
            const toId = typeof conn.to === 'object' ? conn.to : parseInt(conn.to);
            
            // Only include connections where both systems are in this region
            if (regionSystemIds.has(fromId) && regionSystemIds.has(toId)) {
                regionConnections++;
                
                const pairId = fromId < toId ? 
                    `${fromId}-${toId}` : 
                    `${toId}-${fromId}`;
                
                if (!processedPairs.has(pairId)) {
                    processedPairs.add(pairId);
                    
                    // Find constellation IDs
                    let fromConstId = null;
                    let toConstId = null;
                    
                    regionData.constellations.forEach(constellation => {
                        constellation.systems.forEach(system => {
                            if (system.id === fromId) fromConstId = constellation.id;
                            if (system.id === toId) toConstId = constellation.id;
                        });
                    });
                    
                    if (fromConstId && toConstId) {
                        connections.push({
                            from: {
                                systemId: fromId,
                                constId: fromConstId
                            },
                            to: {
                                systemId: toId,
                                constId: toConstId
                            },
                            type: fromConstId === toConstId ? 'intra' : 'inter'
                        });
                    }
                }
            }
        });
        
        console.log(`Checked ${totalConnections} total connections, found ${regionConnections} in region`);
    } else {
        console.warn('No universe connections data available');
    }
    
    console.log(`Created ${connections.length} unique connections for region`);
    return connections;
}
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RegionDetailLayout;
}