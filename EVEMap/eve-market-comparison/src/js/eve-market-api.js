// EVE Market API handler for browser use
class EVEMarketAPI {
    constructor() {
        this.baseUrl = '/api';
        this.esiUrl = 'https://esi.evetech.net/latest';
        this.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'EVE-Market-Comparison/2.0'
        };
        this._fetchLocks = new Map();

        // Initialize cache
        this.cache = {};
        this.cacheExpiry = {};
        this.maxCacheSize = 1000; // Maximum number of cached items
        this.cacheCleanupInterval = 60000; // Cleanup every minute
        this.cacheTTL = 15 * 60 * 1000; // 15 minutes default

        // Market location type definitions
        this.marketLocationTypes = {
            STATION: 'station',
            REGION: 'region',
            STRUCTURE: 'structure',
            CONSTELLATION: 'constellation',
            SOLAR_SYSTEM: 'solar_system',
            CORPORATION: 'corporation',
            ALLIANCE: 'alliance'
        };
        
        // Start cache cleanup interval
        this.cleanupInterval = setInterval(() => this.cleanupCache(), this.cacheCleanupInterval);
    }

    // Cache management methods
    setCache(key, data, ttl = this.cacheTTL) {
        this.cache[key] = data;
        this.cacheExpiry[key] = Date.now() + ttl;
    }

    getCache(key) {
        if (!this.cache[key]) return null;
        if (Date.now() > this.cacheExpiry[key]) {
            delete this.cache[key];
            delete this.cacheExpiry[key];
            return null;
        }
        return this.cache[key];
    }

    clearCache() {
        this.cache = {};
        this.cacheExpiry = {};
    }

    // Clear the cache for a specific item
    clearItemCache(typeId) {
        const cacheKey = `item_${typeId}`;
        delete this.cache[cacheKey];
        delete this.cacheExpiry[cacheKey];
        console.log(`Cache cleared for item ${typeId}`);
    }

    // Cache cleanup method
    cleanupCache() {
        const now = Date.now();
        const cacheKeys = Object.keys(this.cache);
        
        // Remove expired entries
        cacheKeys.forEach(key => {
            if (now > this.cacheExpiry[key]) {
                delete this.cache[key];
                delete this.cacheExpiry[key];
            }
        });
        
        // If still over limit, remove oldest entries
        if (Object.keys(this.cache).length > this.maxCacheSize) {
            const sortedKeys = Object.keys(this.cacheExpiry)
                .sort((a, b) => this.cacheExpiry[a] - this.cacheExpiry[b]);
            
            while (Object.keys(this.cache).length > this.maxCacheSize) {
                const oldestKey = sortedKeys.shift();
                if (oldestKey) {
                    delete this.cache[oldestKey];
                    delete this.cacheExpiry[oldestKey];
                }
            }
        }
    }

    // Clear cache and stop cleanup interval
    dispose() {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
            this.cleanupInterval = null;
        }
        this.clearCache();
    }

    // Original market data methods
    // Get market orders based on location type and ID
    async getMarketOrders(locationId, locationType, options = {}) {
    console.log(`Getting market orders for ${locationType} ID:`, locationId);
    
    const lockKey = `${locationId}_${locationType}`;
    if (this._fetchLocks.get(lockKey)) {
        throw new Error(`Already fetching orders for location ${locationId}`);
    }
    this._fetchLocks.set(lockKey, true);

    try {
        
        let url;
        const headers = { ...this.headers };
        let allOrders = [];
        let page = 1;
        let hasMorePages = true;
        let errorLimit = 100; // Start with default error limit
        let skipPages = new Set();
        
        // Safety limits to prevent infinite loops
        const MAX_PAGES = 2000; // Increased from 300 to handle large markets
        const MAX_CONSECUTIVE_EMPTY_PAGES = 5; // Stop if we get multiple empty pages
        let consecutiveEmptyPages = 0;
        
        switch(locationType) {
            case 'structure':
                const token = localStorage.getItem('eveAccessToken');
                if (!this.validateToken(token)) {
                    throw new Error('Valid V2 authentication token required for structure access');
                }
                headers.Authorization = `Bearer ${token}`;
                url = `http://localhost:8085/api/markets/structures/${locationId}`;
                break;

            case 'station':
                // Fix region ID calculation for stations
                // Example: Jita 4-4 (60003760) is in The Forge (10000002)
                const stationToRegion = {
                    '60003760': '10000002', // Jita 4-4 -> The Forge
                    '60008494': '10000043', // Amarr VIII -> Domain
                    '60011866': '10000032', // Dodixie IX -> Sinq Laison
                    '60004588': '10000042', // Rens VI -> Metropolis
                    '60005686': '10000030'  // Hek VIII -> Heimatar
                };
                
                const regionId = stationToRegion[locationId];
                if (!regionId) {
                    throw new Error(`Unknown station ID: ${locationId}`);
                }
                url = `${this.esiUrl}/markets/${regionId}/orders/`;
                console.log(`Using region ${regionId} for station ${locationId}`);
                break;

            case 'region':
                url = `${this.esiUrl}/markets/${locationId}/orders/`;
                break;

            default:
                throw new Error(`Unsupported market location type: ${locationType}`);
        }
        
        while (hasMorePages && page <= MAX_PAGES) {
            try {
                const paginatedUrl = `${url}?page=${page}`;
                console.log(`Fetching page ${page} from ${paginatedUrl}`);

                const response = await fetch(paginatedUrl, { headers });
                
                if (!response.ok) {
                    if (response.status === 420) {
                        const resetTime = parseInt(response.headers.get('x-esi-error-limit-reset') || '60');
                        console.log(`Rate limited, waiting ${resetTime}s...`);
                        await new Promise(resolve => setTimeout(resolve, resetTime * 1000));
                        continue;
                    }
                    if (response.status === 404 || response.status === 500) {
                        console.log(`No more pages available (${response.status})`);
                        hasMorePages = false;
                        break;
                    }
                    throw new Error(`Failed to fetch market data: ${response.status}`);
                }

                const data = await response.json();
                
                // Handle paginated response format
                const orders = Array.isArray(data) ? data : data.orders || [];
                
                if (orders.length > 0) {
                    await window.marketStorage.storePartialMarketData(locationId, orders, page);
                    allOrders.push(...orders);
                    consecutiveEmptyPages = 0; // Reset counter on successful data
                } else {
                    consecutiveEmptyPages++;
                    console.log(`Empty page ${page}, consecutive empty pages: ${consecutiveEmptyPages}`);
                }

                // Check if we should continue pagination
                if (data.hasMore === false || orders.length === 0) {
                    hasMorePages = false;
                    break;
                }
                
                // Stop if we've hit too many consecutive empty pages
                if (consecutiveEmptyPages >= MAX_CONSECUTIVE_EMPTY_PAGES) {
                    console.log(`Stopping pagination after ${consecutiveEmptyPages} consecutive empty pages`);
                    hasMorePages = false;
                    break;
                }

                // Increment page only on successful request
                page++;
                
                // Add delay between requests, this is main throttle point
                await new Promise(resolve => setTimeout(resolve, 200));

            } catch (pageError) {
                console.error(`Error on page ${page}:`, pageError);
                throw pageError;
            }
        }
        
        // Log completion statistics
        if (page > MAX_PAGES) {
            console.warn(`Market data fetch stopped at maximum page limit (${MAX_PAGES}). There may be more data available.`);
        }
        console.log(`Market data fetch completed. Total pages: ${page - 1}, Total orders: ${allOrders.length}`);

        return allOrders;

    } catch (error) {
        console.error('Error in getMarketOrders:', error);
        throw error;
    }
}

    // Add server check method
    async checkServerStatus() {
        try {
            const response = await fetch('http://localhost:8085/api/health');
            return response.ok;
        } catch (error) {
            console.error('Proxy server not responding:', error);
            return false;
        }
    }

    // Legacy method for backward compatibility
    async getPublicMarketOrders(regionId) {
        return this.getMarketOrders(regionId, this.marketLocationTypes.REGION);
    }

    // Legacy method for backward compatibility
    async getPrivateStructureMarket(structureId) {
        return this.getMarketOrders(structureId, this.marketLocationTypes.STRUCTURE);
    }

    // Get market location information
    async getMarketLocationInfo(locationId, locationType) {
        console.log(`Getting info for ${locationType} ID:`, locationId);
        
        let url;
        switch (locationType) {
            case this.marketLocationTypes.STATION:
                url = `${this.baseUrl}/universe/stations/${locationId}`;
                break;
            case this.marketLocationTypes.STRUCTURE:
                url = `${this.baseUrl}/universe/structures/${locationId}`;
                break;
            case this.marketLocationTypes.CONSTELLATION:
                url = `${this.baseUrl}/universe/constellations/${locationId}`;
                break;
            case this.marketLocationTypes.SOLAR_SYSTEM:
                url = `${this.baseUrl}/universe/systems/${locationId}`;
                break;
            default:
                throw new Error(`Location type ${locationType} does not support detailed info`);
        }

        try {
            const response = await fetch(url, { headers: this.headers });
            if (!response.ok) throw new Error(`Failed to fetch location info: ${response.status}`);
            return response.json();
        } catch (error) {
            console.error('Error in getMarketLocationInfo:', error);
            throw error;
        }
    }

    // Improved item info fetching with request tracking and rate limiting
    async getItemInfo(typeId) {
        // Check IndexedDB first
        const cachedItem = await window.marketStorage.getItemInfo(typeId);
        if (cachedItem) {
            return cachedItem;
        }

        // Rate limiting
        const now = Date.now();
        if (!this.lastItemRequest) this.lastItemRequest = 0;
        const timeSinceLastRequest = now - this.lastItemRequest;
        if (timeSinceLastRequest < 200) { // Increased to 200ms for better memory management
            await new Promise(resolve => setTimeout(resolve, 200 - timeSinceLastRequest));
        }
        this.lastItemRequest = Date.now();

        try {
            const response = await fetch(
                `${this.baseUrl}/universe/types/${typeId}`,
                { 
                    headers: this.headers,
                    cache: 'no-cache'
                }
            );

            if (response.ok) {
                const data = await response.json();
                if (data && data.name && data.type_id) {
                    // Store in IndexedDB instead of memory cache
                    await window.marketStorage.storeItemInfo(typeId, data);
                    return data;
                }
            }

            throw new Error(`Failed to fetch item info: ${response.status}`);

        } catch (error) {
            if (error.message.includes('ERR_INSUFFICIENT_RESOURCES')) {
                console.warn(`Memory limit reached fetching item ${typeId}, using placeholder`);
            } else {
                console.warn(`Error fetching item ${typeId}:`, error.message);
            }

            const placeholder = {
                type_id: parseInt(typeId),
                name: `Item ${typeId}`,
                description: 'Item information could not be retrieved.',
                group_id: 0,
                category_id: 0
            };
            
            // Store placeholder in IndexedDB
            await window.marketStorage.storeItemInfo(typeId, placeholder);
            return placeholder;
        }
    }

    // Rate limiting helpers
    getOrCreateRateLimitBucket() {
        if (!this.rateLimitBucket) {
            this.rateLimitBucket = {
                tokens: 20,
                lastRefill: Date.now(),
                maxTokens: 20
            };
        }

        // Refill tokens if enough time has passed
        const now = Date.now();
        const timePassed = now - this.rateLimitBucket.lastRefill;
        const tokensToAdd = Math.floor(timePassed / 1000); // 1 token per second

        if (tokensToAdd > 0) {
            this.rateLimitBucket.tokens = Math.min(
                this.rateLimitBucket.maxTokens,
                this.rateLimitBucket.tokens + tokensToAdd
            );
            this.rateLimitBucket.lastRefill = now;
        }

        return this.rateLimitBucket;
    }

    consumeRateLimit() {
        const bucket = this.getOrCreateRateLimitBucket();
        if (bucket.tokens >= 1) {
            bucket.tokens -= 1;
        }
    }


    // New methods for category and filtering support
    async getCategories() {
        // Check cache first
        const cacheKey = 'categories';
        const cachedData = this.getCache(cacheKey);
        if (cachedData) return cachedData;
        
        const response = await fetch(
            `${this.baseUrl}/universe/categories`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error('Failed to fetch categories');
        const data = await response.json();
        
        // Cache for 24 hours (categories rarely change)
        this.setCache(cacheKey, data, 24 * 60 * 60 * 1000);
        return data;
    }

    async getGroupsInCategory(categoryId) {
        // Check cache first
        const cacheKey = `groups_${categoryId}`;
        const cachedData = this.getCache(cacheKey);
        if (cachedData) return cachedData;
        
        const response = await fetch(
            `${this.baseUrl}/universe/groups/${categoryId}`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error('Failed to fetch groups');
        const data = await response.json();
        
        // Cache for 24 hours (groups rarely change)
        this.setCache(cacheKey, data, 24 * 60 * 60 * 1000);
        return data;
    }

    async getMarketGroups() {
        // Check cache first
        const cacheKey = 'market_groups';
        const cachedData = this.getCache(cacheKey);
        if (cachedData) return cachedData;
        
        const response = await fetch(
            `${this.baseUrl}/universe/market-groups`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error('Failed to fetch market groups');
        const data = await response.json();
        
        // Cache for 24 hours (market groups rarely change)
        this.setCache(cacheKey, data, 24 * 60 * 60 * 1000);
        return data;
    }

    async searchItems(query, options = {}) {
        if (!query || query.length < 3) {
            throw new Error('Search query must be at least 3 characters');
        }
        
        const { category, group } = options;
        let url = `${this.baseUrl}/universe/types/search?query=${encodeURIComponent(query)}`;
        
        if (category) url += `&category=${category}`;
        if (group) url += `&group=${group}`;
        
        const response = await fetch(url, { headers: this.headers });
        if (!response.ok) throw new Error('Failed to search items');
        return response.json();
    }

    async getFilteredMarketOrders(regionId, filters = {}) {
        console.log('Getting filtered market orders for region ID:', regionId);
        console.log('Filters:', JSON.stringify(filters));
        
        const { typeIds, categoryId, groupId, minPrice, maxPrice } = filters;
        
        let url = `${this.baseUrl}/markets/${regionId}/orders/filtered`;
        const queryParams = [];
        
        if (typeIds && typeIds.length > 0) {
            queryParams.push(`typeIds=${typeIds.join(',')}`);
            console.log('Added typeIds filter:', typeIds.join(','));
        }
        
        if (categoryId) {
            queryParams.push(`categoryId=${categoryId}`);
            console.log('Added categoryId filter:', categoryId);
        }
        
        if (groupId) {
            queryParams.push(`groupId=${groupId}`);
            console.log('Added groupId filter:', groupId);
        }
        
        if (minPrice) {
            queryParams.push(`minPrice=${minPrice}`);
            console.log('Added minPrice filter:', minPrice);
        }
        
        if (maxPrice) {
            queryParams.push(`maxPrice=${maxPrice}`);
            console.log('Added maxPrice filter:', maxPrice);
        }
        
        if (queryParams.length > 0) {
            url += `?${queryParams.join('&')}`;
        }
        
        console.log('Fetching from URL:', url);
        
        try {
            const response = await fetch(url, { headers: this.headers });
            console.log('Filtered market response status:', response.status);
            
            if (!response.ok) {
                const responseText = await response.text();
                console.error('Error response text:', responseText);
                throw new Error(`Failed to fetch filtered market data: ${response.status} - ${responseText || 'Unknown error'}`);
            }
            
            const data = await response.json();
            console.log('Successfully fetched filtered market data, entries:', data.length);
            return data;
        } catch (error) {
            console.error('Error in getFilteredMarketOrders:', error);
            throw error;
        }
    }

    // User filter management
    async saveFilter(filterData) {
        const response = await fetch(
            `${this.baseUrl}/user/filters`,
            {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(filterData)
            }
        );
        
        if (!response.ok) throw new Error('Failed to save filter');
        return response.json();
    }

    async getSavedFilters() {
        const response = await fetch(
            `${this.baseUrl}/user/filters`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error('Failed to fetch saved filters');
        return response.json();
    }

    // Local storage for filters (client-side only)
    saveFilterToLocalStorage(name, filterData) {
        try {
            // Get existing filters
            const filtersJson = localStorage.getItem('eveMarketFilters') || '{}';
            const filters = JSON.parse(filtersJson);
            
            // Add new filter
            filters[name] = {
                ...filterData,
                timestamp: Date.now()
            };
            
            // Save back to localStorage
            localStorage.setItem('eveMarketFilters', JSON.stringify(filters));
            return true;
        } catch (error) {
            console.error('Failed to save filter to localStorage:', error);
            return false;
        }
    }

    getFiltersFromLocalStorage() {
        try {
            const filtersJson = localStorage.getItem('eveMarketFilters') || '{}';
            return JSON.parse(filtersJson);
        } catch (error) {
            console.error('Failed to get filters from localStorage:', error);
            return {};
        }
    }

    deleteFilterFromLocalStorage(name) {
        try {
            const filtersJson = localStorage.getItem('eveMarketFilters') || '{}';
            const filters = JSON.parse(filtersJson);
            
            if (filters[name]) {
                delete filters[name];
                localStorage.setItem('eveMarketFilters', JSON.stringify(filters));
            }
            
            return true;
        } catch (error) {
            console.error('Failed to delete filter from localStorage:', error);
            return false;
        }
    }

    async searchItemsByGroup(groupId) {
        // Check cache first
        const cacheKey = `group_items_${groupId}`;
        const cachedData = this.getCache(cacheKey);
        if (cachedData) return cachedData;
        
        const response = await fetch(
            `${this.baseUrl}/universe/groups/${groupId}/types`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error(`Failed to fetch items for group ${groupId}`);
        const typeIds = await response.json();
        
        // Convert the type IDs to our standard format, checking if they're already in proper format
        const result = typeIds.map(id => {
            // If it's already an object with type_id, use it
            if (id && typeof id === 'object' && 'type_id' in id) {
                return id;
            }
            // Otherwise create a new object with type_id
            return { type_id: id };
        });

        console.log(`Retrieved ${result.length} items for group ${groupId}`);
        
        // Cache for 24 hours (items in groups rarely change)
        this.setCache(cacheKey, result, 24 * 60 * 60 * 1000);
        return result;
    }

    // Helper methods for excluded categories persistence
    saveExcludedCategories(categoryIds) {
        try {
            localStorage.setItem('eveMarketExcludedCategories', JSON.stringify(categoryIds));
            return true;
        } catch (error) {
            console.error('Failed to save excluded categories:', error);
            return false;
        }
    }

    getExcludedCategories() {
        try {
            const saved = localStorage.getItem('eveMarketExcludedCategories');
            return saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Failed to get excluded categories:', error);
            return [];
        }
    }

    // Clear all excluded categories data (utility for debugging/fixing issues)
    clearExcludedCategories() {
        try {
            localStorage.removeItem('eveMarketExcludedCategories');
            console.log('✅ Cleared all excluded categories data from localStorage');
            return true;
        } catch (error) {
            console.error('Failed to clear excluded categories:', error);
            return false;
        }
    }

    // Reset excluded categories to empty state and update filters
    resetExcludedCategories() {
        try {
            this.clearExcludedCategories();
            
            // Reset in-memory filters if available
            if (window.marketFilters) {
                window.marketFilters.excludedCategoryIds = [];
            }
            
            // Update UI if available
            if (window.updateExcludedCategoriesUI) {
                window.updateExcludedCategoriesUI();
            }
            
            console.log('✅ Reset excluded categories to empty state');
            return true;
        } catch (error) {
            console.error('Failed to reset excluded categories:', error);
            return false;
        }
    }

    // New method to get market ID info
    getMarketIdInfo(marketId) {
        const id = marketId.toString();
        
        // Station IDs (600xxxxx)
        if (id.startsWith('600')) {
            return {
                type: this.marketLocationTypes.STATION,
                locationId: marketId
            };
        }
        
        // Region IDs (100000xx)
        if (id.startsWith('100000')) {
            return {
                type: this.marketLocationTypes.REGION,
                locationId: marketId
            };
        }
        
        // Structure IDs (1xxxxxxxxx)
        if (id.startsWith('10')) {
            return {
                type: this.marketLocationTypes.STRUCTURE,
                locationId: marketId
            };
        }
        
        // Constellation IDs (200xxxxx)
        if (id.startsWith('200')) {
            return {
                type: this.marketLocationTypes.CONSTELLATION,
                locationId: marketId
            };
        }
        
        // Solar System IDs (300xxxxx)
        if (id.startsWith('300')) {
            return {
                type: this.marketLocationTypes.SOLAR_SYSTEM,
                locationId: marketId
            };
        }
        
        // Corporation IDs (98xxxxxx)
        if (id.startsWith('98')) {
            return {
                type: this.marketLocationTypes.CORPORATION,
                locationId: marketId
            };
        }
        
        // Alliance IDs (99xxxxxx)
        if (id.startsWith('99')) {
            return {
                type: this.marketLocationTypes.ALLIANCE,
                locationId: marketId
            };
        }
        
        throw new Error(`Unknown market ID format: ${marketId}`);
    }

    // Get market orders for specific type IDs (batch processing)
    async getMarketOrdersBatch(locationId, typeIds) {
        const orders = [];
        const batchSize = 20; // Smaller batches for better memory management
        
        for (let i = 0; i < typeIds.length; i += batchSize) {
            const batch = typeIds.slice(i, i + batchSize);
            
            try {
                // Fetch orders for each type in the batch
                const batchPromises = batch.map(async typeId => {
                    try {
                        const url = `${this.baseUrl}/markets/${locationId}/orders/?type_id=${typeId}`;
                        const response = await this.fetchWithAuth(url);
                        if (response.ok) {
                            const typeOrders = await response.json();
                            return typeOrders;
                        }
                        return [];
                    } catch (error) {
                        console.warn(`Failed to fetch orders for type ${typeId}:`, error);
                        return [];
                    }
                });
                
                const batchResults = await Promise.all(batchPromises);
                batchResults.forEach(typeOrders => {
                    orders.push(...typeOrders);
                });
                
                // Add delay to prevent rate limiting
                await new Promise(resolve => setTimeout(resolve, 100));
                
            } catch (error) {
                console.warn(`Error processing batch ${i}-${i + batchSize}:`, error);
            }
        }
        
        return orders;
    }

    // Get item types for a specific category
    async getCategoryTypes(categoryId) {
        try {
            // First get the category info to find its groups
            const categoryUrl = `${this.baseUrl}/universe/categories/${categoryId}/`;
            const categoryResponse = await this.fetchWithAuth(categoryUrl);
            
            if (!categoryResponse.ok) {
                throw new Error(`Failed to fetch category ${categoryId}`);
            }
            
            const categoryData = await categoryResponse.json();
            const groupIds = categoryData.groups || [];
            
            // Get types for each group in the category
            const allTypes = [];
            
            for (const groupId of groupIds) {
                try {
                    const groupUrl = `${this.baseUrl}/universe/groups/${groupId}/`;
                    const groupResponse = await this.fetchWithAuth(groupUrl);
                    
                    if (groupResponse.ok) {
                        const groupData = await groupResponse.json();
                        const groupTypes = (groupData.types || []).map(typeId => ({
                            id: typeId,
                            group_id: groupId,
                            category_id: categoryId
                        }));
                        allTypes.push(...groupTypes);
                    }
                    
                    // Small delay to prevent rate limiting
                    await new Promise(resolve => setTimeout(resolve, 50));
                    
                } catch (error) {
                    console.warn(`Failed to fetch group ${groupId}:`, error);
                }
            }
            
            return allTypes;
            
        } catch (error) {
            console.error(`Error fetching category types for ${categoryId}:`, error);
            throw error;
        }
    }

    // Group-based filtering methods
    async getGroupInfo(groupId) {
        const cacheKey = `group_info_${groupId}`;
        const cachedData = this.getCache(cacheKey);
        if (cachedData) return cachedData;

        try {
            const response = await fetch(`${this.esiUrl}/universe/groups/${groupId}/`, {
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const groupInfo = await response.json();
            this.setCache(cacheKey, groupInfo, 24 * 60 * 60 * 1000); // Cache for 24 hours
            return groupInfo;
        } catch (error) {
            console.error(`Error fetching group info for ${groupId}:`, error);
            throw error;
        }
    }

    async getGroupInfoBatch(groupIds) {
        const results = {};
        const batchSize = 10;
        
        for (let i = 0; i < groupIds.length; i += batchSize) {
            const batch = groupIds.slice(i, i + batchSize);
            const promises = batch.map(async groupId => {
                try {
                    const groupInfo = await this.getGroupInfo(groupId);
                    results[groupId] = groupInfo;
                } catch (error) {
                    console.warn(`Failed to get info for group ${groupId}:`, error);
                    results[groupId] = { name: `Group ${groupId}`, error: true };
                }
            });
            
            await Promise.all(promises);
            
            // Small delay between batches
            if (i + batchSize < groupIds.length) {
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        }
        
        return results;
    }

    async getAllGroups() {
        const cacheKey = 'all_groups';
        const cachedData = this.getCache(cacheKey);
        if (cachedData) return cachedData;

        try {
            const response = await fetch(`${this.esiUrl}/universe/groups/`, {
                headers: this.headers
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const groupIds = await response.json();
            this.setCache(cacheKey, groupIds, 24 * 60 * 60 * 1000); // Cache for 24 hours
            return groupIds;
        } catch (error) {
            console.error('Error fetching all groups:', error);
            throw error;
        }
    }

    // Group filter persistence methods
    saveExcludedGroups(groupIds) {
        try {
            const validGroups = Array.isArray(groupIds) ? groupIds.filter(id => !isNaN(parseInt(id))) : [];
            localStorage.setItem('eveMarketExcludedGroups', JSON.stringify(validGroups));
            return true;
        } catch (error) {
            console.error('Failed to save excluded groups:', error);
            return false;
        }
    }

    getExcludedGroups() {
        try {
            const stored = localStorage.getItem('eveMarketExcludedGroups');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('Failed to load excluded groups:', error);
            return [];
        }
    }

    clearExcludedGroups() {
        try {
            localStorage.removeItem('eveMarketExcludedGroups');
            return true;
        } catch (error) {
            console.error('Failed to clear excluded groups:', error);
            return false;
        }
    }

    // Add token validation helper
    validateToken(token) {
        if (!token) return false;
        if (!token.startsWith('eyJ')) {
            console.warn('Invalid token format - not a V2 JWT token');
            return false;
        }
        return true;
    }
}

// Create global instance
window.marketAPI = new EVEMarketAPI();

// Add this line at the very end of the file, after the window.marketAPI = new EVEMarketAPI(); line
window.getMarketIdInfo = function(marketId) {
    return window.marketAPI.getMarketIdInfo(marketId);
};