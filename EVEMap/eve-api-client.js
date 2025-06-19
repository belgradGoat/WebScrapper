// EVE API Client Module
(function(window) {
    'use strict';
    
    class EVEAPIClient {
        constructor(options = {}) {
            this.baseURL = options.proxyURL || 'http://localhost:3001/api';
            this.cache = new Map();
            this.rateLimitDelay = 150;
            this.requestQueue = [];
            this.processing = false;
            this.maxRetries = 3;
            this.cacheExpiry = 600000; // 10 minutes
        }
        
        async makeRequest(endpoint, useCache = true) {
            if (useCache) {
                const cached = this.getFromCache(endpoint);
                if (cached) return cached;
            }
            
            return new Promise((resolve, reject) => {
                this.requestQueue.push({ 
                    endpoint, 
                    useCache, 
                    resolve, 
                    reject,
                    retries: 0 
                });
                this.processQueue();
            });
        }
        
        getFromCache(endpoint) {
            const cached = this.cache.get(endpoint);
            if (cached && Date.now() - cached.timestamp < this.cacheExpiry) {
                return cached.data;
            }
            this.cache.delete(endpoint);
            return null;
        }
        
        setCache(endpoint, data) {
            this.cache.set(endpoint, {
                data,
                timestamp: Date.now()
            });
        }
        
        async processQueue() {
            if (this.processing || this.requestQueue.length === 0) return;
            this.processing = true;
            
            while (this.requestQueue.length > 0) {
                const request = this.requestQueue.shift();
                
                try {
                    const response = await fetch(`${this.baseURL}${request.endpoint}`);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    if (request.useCache) {
                        this.setCache(request.endpoint, data);
                    }
                    
                    request.resolve(data);
                    
                    // Rate limiting
                    if (this.requestQueue.length > 0) {
                        await this.delay(this.rateLimitDelay);
                    }
                    
                } catch (error) {
                    if (request.retries < this.maxRetries) {
                        request.retries++;
                        this.requestQueue.unshift(request);
                        await this.delay(1000 * request.retries);
                    } else {
                        console.warn(`API request failed: ${request.endpoint}`, error);
                        request.reject(error);
                    }
                }
            }
            
            this.processing = false;
        }
        
        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        // Batch request multiple endpoints
        async batchRequest(endpoints) {
            const response = await fetch(`${this.baseURL}/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ endpoints })
            });
            
            return response.json();
        }
        
        // Public API methods
        async getRegions() {
            return this.makeRequest('/universe/regions/');
        }
        
        async getRegionInfo(regionId) {
            return this.makeRequest(`/universe/regions/${regionId}/`);
        }
        
        async getConstellationInfo(constellationId) {
            return this.makeRequest(`/universe/constellations/${constellationId}/`);
        }
        
        async getSystemInfo(systemId) {
            return this.makeRequest(`/universe/systems/${systemId}/`);
        }
        
        async getStargateInfo(stargateId) {
            return this.makeRequest(`/universe/stargates/${stargateId}/`);
        }
        
        async getSystemKills() {
            return this.makeRequest('/universe/system_kills/', false);
        }
        
        async getSystemJumps() {
            return this.makeRequest('/universe/system_jumps/', false);
        }
        
        async calculateRoute(origin, destination, options = {}) {
            const params = new URLSearchParams({
                avoid: options.avoid || 'secure',
                connections: options.connections || 'secure',
                destination: destination,
                flag: options.flag || 'shortest',
                origin: origin
            });
            
            return this.makeRequest(`/route/${origin}/${destination}/?${params}`, false);
        }
        
        // Optimized bulk loading - matches FastAPI endpoint
        async getUniverseOverview() {
            try {
                const response = await fetch(`${this.baseURL}/universe/optimized`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Failed to get universe overview:', error);
                throw error;
            }
        }
        
        // Export cache for persistence
        exportCache() {
            const cacheData = {};
            this.cache.forEach((value, key) => {
                cacheData[key] = value;
            });
            return JSON.stringify(cacheData);
        }
        
        // Import cache from storage
        importCache(cacheString) {
            try {
                const cacheData = JSON.parse(cacheString);
                Object.entries(cacheData).forEach(([key, value]) => {
                    this.cache.set(key, value);
                });
            } catch (error) {
                console.error('Failed to import cache:', error);
            }
        }
        
        // Clear cache
        clearCache() {
            this.cache.clear();
        }
        
        // Get cache statistics
        getCacheStats() {
            let totalSize = 0;
            let validEntries = 0;
            const now = Date.now();
            
            this.cache.forEach((value, key) => {
                if (now - value.timestamp < this.cacheExpiry) {
                    validEntries++;
                }
                totalSize += JSON.stringify(value).length;
            });
            
            return {
                totalEntries: this.cache.size,
                validEntries,
                totalSize,
                sizeInMB: (totalSize / 1048576).toFixed(2)
            };
        }
    }
    
    // Export to window
    window.EVEAPIClient = EVEAPIClient;
    
})(window);