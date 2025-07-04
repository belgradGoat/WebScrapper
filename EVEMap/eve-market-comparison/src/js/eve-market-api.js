// EVE Market API handler for browser use
class EVEMarketAPI {
    constructor() {
        this.baseUrl = '/api'; // Use local proxy instead of direct ESI
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        
        // Initialize cache
        this.cache = {};
        this.cacheExpiry = {};
        this.cacheTTL = 15 * 60 * 1000; // 15 minutes default
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

    // Original market data methods
    async getPublicMarketOrders(regionId) {
        console.log('Getting public market orders for region ID:', regionId);
        
        const url = `${this.baseUrl}/markets/${regionId}/orders`;
        console.log('Fetching from URL:', url);
        
        try {
            const response = await fetch(url, { headers: this.headers });
            console.log('Public market response status:', response.status);
            
            if (!response.ok) {
                const responseText = await response.text();
                console.error('Error response text:', responseText);
                throw new Error(`Failed to fetch public market data: ${response.status} - ${responseText || 'Unknown error'}`);
            }
            
            const data = await response.json();
            console.log('Successfully fetched public market data, entries:', data.length);
            return data;
        } catch (error) {
            console.error('Error in getPublicMarketOrders:', error);
            throw error;
        }
    }

    async getPrivateStructureMarket(structureId) {
        console.log('Getting private structure market for ID:', structureId);
        
        const token = localStorage.getItem('eveAccessToken');
        console.log('Token exists:', !!token);
        console.log('Token length:', token ? token.length : 0);
        console.log('Token starts with:', token ? token.substring(0, 10) + '...' : 'N/A');
        
        if (!token) throw new Error('No access token found. Please login first.');
        
        // Create headers object
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': `Bearer ${token}`
        };
        
        console.log('Making request with auth header:', headers.Authorization.substring(0, 50) + '...');
        
        try {
            console.log('Fetching from URL:', `${this.baseUrl}/markets/structures/${structureId}`);
            const response = await fetch(
                `${this.baseUrl}/markets/structures/${structureId}`,
                {
                    method: 'GET',
                    headers: headers
                }
            );
            
            console.log('Structure response status:', response.status);
            console.log('Structure response headers:', JSON.stringify([...response.headers.entries()]));
            
            if (!response.ok) {
                const responseText = await response.text();
                console.error('Error response text:', responseText);
                
                let errorData = {};
                try {
                    errorData = JSON.parse(responseText);
                    console.error('Parsed error data:', errorData);
                } catch (e) {
                    console.error('Failed to parse error response as JSON');
                }
                
                if (response.status === 403) {
                    throw new Error('No access to this structure. Make sure you have docking access.');
                }
                if (response.status === 401) {
                    throw new Error('Authentication failed. Try logging in again.');
                }
                
                throw new Error(`Failed to fetch structure market data: ${response.status} - ${errorData.error || responseText || 'Unknown error'}`);
            }
            
            const data = await response.json();
            console.log('Successfully fetched structure market data, entries:', data.length);
            return data;
        } catch (error) {
            console.error('Error in getPrivateStructureMarket:', error);
            throw error;
        }
    }

    async getItemInfo(typeId) {
        const response = await fetch(
            `${this.baseUrl}/universe/types/${typeId}`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error('Failed to fetch item info');
        return response.json();
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
}

// Create global instance
window.marketAPI = new EVEMarketAPI();