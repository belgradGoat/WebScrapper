const express = require('express');
const cors = require('cors');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const path = require('path');

const app = express();
app.use(cors({
    origin: 'http://localhost:8085',
    credentials: true,
    allowedHeaders: ['Content-Type', 'Authorization']
}));
app.use(express.json());

// Serve static files from the src directory
app.use(express.static(path.join(__dirname)));
app.use('/js', express.static(path.join(__dirname, 'js')));
app.use('/css', express.static(path.join(__dirname, 'css')));

// Handle the callback route explicitly
app.get('/callback', (req, res) => {
    console.log('Callback route hit with query:', req.query);
    res.sendFile(path.join(__dirname, 'callback.html'));
});

// Serve index.html at root
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

const CLIENT_ID = 'b1ee25b8600a462bbe94c23defd64eeb';
const CLIENT_SECRET = 'vqVoMi6dRfgRJh03GSH77q2boukqqUgIb99tkeho'; // Replace with your actual secret

app.post('/api/token', async (req, res) => {
    const { code } = req.body;
    
    console.log('Token exchange request received');
    
    if (!code) {
        return res.status(400).json({ error: 'Authorization code is required' });
    }
    
    try {
        // Only use V2 endpoint
        const tokenUrl = 'https://login.eveonline.com/v2/oauth/token';
        const body = new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            redirect_uri: 'http://localhost:8085/callback'
        });
        
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'login.eveonline.com'
            },
            body: body.toString()
        });
        
        if (!response.ok) {
            throw new Error(`Token exchange failed: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Verify it's a V2 token
        if (!data.access_token?.startsWith('eyJ')) {
            throw new Error('Received non-V2 token format');
        }
        
        res.json(data);
        
    } catch (error) {
        console.error('Token exchange error:', error);
        res.status(500).json({
            error: 'Token exchange failed',
            details: error.message
        });
    }
});

// Proxy for public market orders
app.get('/api/markets/:regionId/orders', async (req, res) => {
    try {
        const { regionId } = req.params;
        const { type_ids } = req.query; // Get type_ids from query params
        console.log(`Fetching orders for region ${regionId}${type_ids ? ` with type_ids: ${type_ids}` : ''}...`);
        
        let allOrders = [];
        let page = 1;
        let hasMorePages = true;
        
        // Process typeIds parameter properly
        let processedTypeIds = null;
        if (type_ids) {
            // Check if it's a comma-separated list
            if (type_ids.includes(',')) {
                // Split and handle as multiple IDs
                processedTypeIds = type_ids.split(',').map(id => id.trim());
                console.log(`Processing multiple type_ids: ${processedTypeIds.length} IDs`);
                console.log(`Sample IDs: ${processedTypeIds.slice(0, 5).join(', ')}${processedTypeIds.length > 5 ? '...' : ''}`);
            } else {
                // Single ID
                processedTypeIds = [type_ids];
                console.log(`Processing single type_id: ${type_ids}`);
            }
        }
        
        while (hasMorePages) {
            let baseUrl = `https://esi.evetech.net/latest/markets/${regionId}/orders/?page=${page}`;
            
            // Add type_ids filter if provided - note that ESI expects type_id (singular)
            // For multiple types, we need to make separate requests for each
            
            if (processedTypeIds && processedTypeIds.length > 0) {
                // For multiple IDs, we need to do separate requests
                // Process in smaller batches to avoid too many parallel requests
                const batchSize = 10; // Process 10 type IDs at a time
                const typeIdBatches = [];
                
                for (let i = 0; i < processedTypeIds.length; i += batchSize) {
                    typeIdBatches.push(processedTypeIds.slice(i, i + batchSize));
                }
                
                console.log(`Dividing ${processedTypeIds.length} type IDs into ${typeIdBatches.length} batches of ${batchSize}`);
                
                let allPageData = [];
                
                for (const batchTypeIds of typeIdBatches) {
                    const pagePromises = batchTypeIds.map(typeId => {
                        // EVE ESI API expects "type_id" (singular), not "type_ids"
                        const url = `${baseUrl}&type_id=${typeId}`;
                        
                        // Logging only for the first few requests to avoid console flood
                        if (batchTypeIds.indexOf(typeId) < 2) {
                            console.log(`Fetching page ${page} for type_id ${typeId} with URL: ${url}...`);
                        }
                        
                        return fetch(url, {
                            method: 'GET',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                                'User-Agent': 'EVE-Market-Comparison/2.0'
                            }
                        })
                        .then(response => {
                            if (!response.ok && !(response.status === 404 && page > 1)) {
                                throw new Error(`ESI returned status ${response.status} for type_id ${typeId}`);
                            }
                            return response.ok ? response.json() : [];
                        })
                        .catch(err => {
                            console.error(`Error fetching type_id ${typeId}:`, err);
                            return []; // Return empty array on error for this type
                        });
                    });
                    
                    const batchResults = await Promise.all(pagePromises);
                    // Flatten the batch results and add to all data
                    const batchData = batchResults.flat();
                    allPageData = allPageData.concat(batchData);
                    
                    // Add a small delay between batches to avoid rate limiting
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                
                // Use all collected data as this page's data, but first validate it
                const pageData = allPageData.filter(order => {
                    // Filter out invalid orders
                    if (!order || typeof order !== 'object') {
                        console.error('Invalid order object received', order);
                        return false;
                    }
                    if (!('type_id' in order) || !('price' in order) || !('is_buy_order' in order)) {
                        console.error('Order missing required fields', order);
                        return false;
                    }
                    return true;
                });
                
                console.log(`Received ${allPageData.length} orders, ${pageData.length} are valid`);
                
                if (pageData.length === 0 && page > 1) {
                    // No more data for any type
                    hasMorePages = false;
                    break;
                }
                
                allOrders = allOrders.concat(pageData);
                // For multi-type requests, we don't reliably know if there are more pages
                // so we'll just check if we got any data back
                if (pageData.length === 0) {
                    hasMorePages = false;
                } else {
                    page++;
                }
            } else {
                // No type filter, get all orders for the region
                console.log(`Fetching page ${page} with URL: ${baseUrl}...`);
                
                const response = await fetch(baseUrl, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                });
                
                if (!response.ok) {
                    if (response.status === 404 && page > 1) {
                        // No more pages
                        hasMorePages = false;
                        break;
                    }
                    return res.status(response.status).json({
                        error: 'Failed to fetch market data',
                        details: `ESI returned status ${response.status} on page ${page}`
                    });
                }
                
                const pageData = await response.json();
                allOrders = allOrders.concat(pageData);
                
                // Check if there are more pages (ESI sends X-Pages header)
                const totalPages = parseInt(response.headers.get('x-pages') || '1');
                if (page >= totalPages) {
                    hasMorePages = false;
                } else {
                    page++;
                }
            }
            
            // Add small delay to avoid rate limiting
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        console.log(`Fetched ${allOrders.length} total orders from ${page-1} pages`);
        res.json(allOrders);
        
    } catch (error) {
        console.error('Public market error:', error);
        res.status(500).json({
            error: 'Market data retrieval failed',
            details: error.message
        });
    }
});

// Add health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

// Update structure endpoint with better error handling
app.get('/api/markets/structures/:structureId', async (req, res) => {
    try {
        const { structureId } = req.params;
        const page = parseInt(req.query.page) || 1;
        const authHeader = req.headers.authorization;
        
        if (!authHeader) {
            return res.status(401).json({ error: 'Authentication required' });
        }

        console.log(`Fetching structure ${structureId} page ${page}...`);

        const token = authHeader.replace('Bearer ', '');
        
        // Validate V2 token
        if (!token.startsWith('eyJ')) {
            return res.status(401).json({
                error: 'Invalid token format',
                details: 'V2 JWT token required'
            });
        }

        const url = `https://esi.evetech.net/latest/markets/structures/${structureId}/`;
        console.log(`Fetching structure page ${page}...`);
        
        const response = await fetch(`${url}?page=${page}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });

        console.log(`Structure page ${page} response status:`, response.status);

        // Handle specific error cases
        if (response.status === 403) {
            return res.status(403).json({
                error: 'Access forbidden',
                details: 'You do not have access to this structure'
            });
        }

        if (response.status === 404 && page > 1) {
            // No more pages - return empty array
            return res.json([]);
        }

        if (!response.ok) {
            throw new Error(`ESI returned status ${response.status}`);
        }

        const data = await response.json();
        
        // Validate response data
        if (!Array.isArray(data)) {
            console.error('Invalid response data:', data);
            throw new Error('Invalid response format from ESI');
        }

        // Log success
        console.log(`Page ${page}: Received ${data.length} orders, ${data.filter(o => o && o.type_id).length} valid`);

        // Add delay based on remaining error limit
        const errorLimit = parseInt(response.headers.get('x-esi-error-limit-remain') || '100');
        const waitTime = errorLimit < 50 ? 1000 : 500;
        console.log(`Waiting ${waitTime}ms before next request (error limit: ${errorLimit}, reset: ${response.headers.get('x-esi-error-limit-reset')}s)`);
        await new Promise(resolve => setTimeout(resolve, waitTime));

        res.json(data);

    } catch (error) {
        console.error('Structure market error:', error);
        res.status(500).json({
            error: 'Structure market data retrieval failed',
            details: error.message,
            structureId: req.params.structureId,
            page: req.query.page
        });
    }
});

// Add a test endpoint to verify V2 JWT token
app.get('/api/verify-token', async (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        const token = authHeader?.replace('Bearer ', '');
        
        if (!token) {
            return res.status(401).json({ error: 'No token provided' });
        }

        // Validate JWT token format
        if (!token.startsWith('eyJ')) {
            console.error('Invalid token format: Not a V2 JWT');
            return res.status(401).json({
                error: 'Invalid authentication token',
                details: 'Only V2 JWT tokens are supported'
            });
        }
        
        // Try to verify the token using the latest ESI endpoint
        const response = await fetch('https://esi.evetech.net/latest/verify/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        console.log('Verify response status:', response.status);
        const text = await response.text();
        console.log('Verify response:', text);
        
        if (response.ok) {
            try {
                const data = JSON.parse(text);
                res.json({
                    valid: true,
                    data,
                    details: 'V2 JWT token successfully verified'
                });
            } catch (e) {
                res.status(500).json({
                    valid: false,
                    error: 'Invalid response format from ESI verification endpoint'
                });
            }
        } else {
            res.status(response.status).json({
                valid: false,
                error: 'Token verification failed',
                details: text
            });
        }
        
    } catch (error) {
        console.error('Verify error:', error);
        res.status(500).json({
            error: 'Token verification process failed',
            details: error.message
        });
    }
});

// Proxy for item info
app.get('/api/universe/types/:typeId', async (req, res) => {
    try {
        const { typeId } = req.params;
        
        // Check if this is a force refresh request
        const forceRefresh = req.query.refresh === 'true';
        
        // Check cache first to reduce API calls and improve reliability (unless force refresh)
        const cacheKey = `item_type_${typeId}`;
        const cachedData = forceRefresh ? null : getFromCache(cacheKey);
        
        if (cachedData) {
            // If this is a placeholder item and it's been in cache for a while, try to refresh
            if (cachedData.name === `Item ${typeId}` || cachedData.name === `Unknown Item (${typeId})`) {
                const cacheTimeLeft = getCacheTimeLeft(cacheKey);
                // Only refresh if the cache is older than 1 hour
                if (cacheTimeLeft < 23 * 60 * 60 * 1000) { // If less than 23 hours left in 24 hour cache
                    console.log(`Refreshing stale placeholder data for item ${typeId}`);
                    // We'll continue with the fetch, but still return the cached data if fetch fails
                } else {
                    return res.json(cachedData);
                }
            } else {
                // Valid item data, return from cache
                return res.json(cachedData);
            }
        }
        
        // Not in cache or refreshing, fetch from ESI API
        const url = `https://esi.evetech.net/latest/universe/types/${typeId}/`;
        
        // Add retry logic for improved reliability
        const maxRetries = 3;
        let retryCount = 0;
        let lastError = null;
        
        while (retryCount < maxRetries) {
            try {
                console.log(`Fetching item data for ${typeId} from ESI (attempt ${retryCount + 1}/${maxRetries})`);
                
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0',
                        'Cache-Control': 'no-cache'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Enhanced validation
                    if (!data || typeof data !== 'object') {
                        throw new Error('Invalid item data received - not an object');
                    }
                    
                    if (!data.name) {
                        throw new Error('Invalid item data received - missing name property');
                    }
                    
                    if (!data.type_id) {
                        // Add type_id if it's missing
                        data.type_id = parseInt(typeId);
                    }
                    
                    // Store in cache for 24 hours (items rarely change)
                    setInCache(cacheKey, data, 24 * 60 * 60 * 1000);
                    
                    return res.json(data);
                }
                
                // Special case for 404 - item doesn't exist
                if (response.status === 404) {
                    console.log(`Item ${typeId} not found in ESI database`);
                    // Create a more user-friendly placeholder item
                    const placeholderItem = {
                        type_id: parseInt(typeId),
                        name: `Unknown Item (${typeId})`,
                        description: 'This item ID is not available in the EVE ESI API. It might be a new item or a restricted item.',
                        group_id: 0
                    };
                    
                    // Cache the placeholder to prevent repeated lookups, but for less time
                    setInCache(cacheKey, placeholderItem, 1 * 60 * 60 * 1000); // 1 hour
                    return res.json(placeholderItem);
                }
                
                // For other errors, try again
                lastError = new Error(`ESI returned status ${response.status}`);
                
            } catch (fetchError) {
                console.error(`Retry ${retryCount + 1}/${maxRetries} failed for item ${typeId}:`, fetchError);
                lastError = fetchError;
            }
            
            retryCount++;
            if (retryCount < maxRetries) {
                // Add exponential backoff
                const delay = 500 * Math.pow(2, retryCount);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        // All retries failed
        throw lastError || new Error('Failed to fetch item info after retries');
        
    } catch (error) {
        console.error(`Item info error for typeId ${req.params.typeId}:`, error);
        res.status(500).json({
            error: 'Item information retrieval failed',
            details: error.message
        });
    }
});

// Proxy for universe categories
app.get('/api/universe/categories', async (req, res) => {
    try {
        // Check cache first
        const cacheKey = 'universe_categories';
        const cachedData = getFromCache(cacheKey);
        
        if (cachedData) {
            return res.json(cachedData);
        }
        
        const url = 'https://esi.evetech.net/latest/universe/categories/';
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Failed to fetch categories',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const categoryIds = await response.json();
        
        // Fetch details for each category (in batches to avoid rate limiting)
        const categories = [];
        const batchSize = 10;
        
        for (let i = 0; i < categoryIds.length; i += batchSize) {
            const batch = categoryIds.slice(i, i + batchSize);
            const batchPromises = batch.map(categoryId =>
                fetch(`https://esi.evetech.net/latest/universe/categories/${categoryId}/`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                })
                .then(resp => resp.ok ? resp.json() : null)
                .catch(() => null)
            );
            
            const results = await Promise.all(batchPromises);
            categories.push(...results.filter(Boolean));
        }
        
        // Store in cache
        setInCache(cacheKey, categories, 24 * 60 * 60 * 1000); // 24 hours
        
        res.json(categories);
    } catch (error) {
        console.error('Categories error:', error);
        res.status(500).json({
            error: 'Category retrieval failed',
            details: error.message
        });
    }
});

// Proxy for universe groups in a category
app.get('/api/universe/groups/:categoryId', async (req, res) => {
    try {
        const { categoryId } = req.params;
        
        // Check cache first
        const cacheKey = `universe_groups_${categoryId}`;
        const cachedData = getFromCache(cacheKey);
        
        if (cachedData) {
            return res.json(cachedData);
        }
        
        // First get the category to verify it exists and get its groups
        const categoryUrl = `https://esi.evetech.net/latest/universe/categories/${categoryId}/`;
        
        const categoryResponse = await fetch(categoryUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!categoryResponse.ok) {
            return res.status(categoryResponse.status).json({
                error: 'Failed to fetch category',
                details: `ESI returned status ${categoryResponse.status}`
            });
        }
        
        const category = await categoryResponse.json();
        const groupIds = category.groups || [];
        
        // Fetch details for each group (in batches to avoid rate limiting)
        const groups = [];
        const batchSize = 10;
        
        for (let i = 0; i < groupIds.length; i += batchSize) {
            const batch = groupIds.slice(i, i + batchSize);
            const batchPromises = batch.map(groupId =>
                fetch(`https://esi.evetech.net/latest/universe/groups/${groupId}/`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                })
                .then(resp => resp.ok ? resp.json() : null)
                .catch(() => null)
            );
            
            const results = await Promise.all(batchPromises);
            groups.push(...results.filter(Boolean));
        }
        
        // Store in cache
        setInCache(cacheKey, groups, 24 * 60 * 60 * 1000); // 24 hours
        
        res.json(groups);
    } catch (error) {
        console.error('Groups error:', error);
        res.status(500).json({
            error: 'Group retrieval failed',
            details: error.message
        });
    }
});

// Proxy for universe market groups
app.get('/api/universe/market-groups', async (req, res) => {
    try {
        // Check cache first
        const cacheKey = 'universe_market_groups';
        const cachedData = getFromCache(cacheKey);
        
        if (cachedData) {
            return res.json(cachedData);
        }
        
        const url = 'https://esi.evetech.net/latest/markets/groups/';
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Failed to fetch market groups',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const groupIds = await response.json();
        
        // Fetch details for each market group (in batches to avoid rate limiting)
        const marketGroups = [];
        const batchSize = 10;
        
        for (let i = 0; i < groupIds.length; i += batchSize) {
            const batch = groupIds.slice(i, i + batchSize);
            const batchPromises = batch.map(groupId =>
                fetch(`https://esi.evetech.net/latest/markets/groups/${groupId}/`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                })
                .then(resp => resp.ok ? resp.json() : null)
                .catch(() => null)
            );
            
            const results = await Promise.all(batchPromises);
            marketGroups.push(...results.filter(Boolean));
        }
        
        // Build hierarchy
        const groupsById = {};
        marketGroups.forEach(group => {
            groupsById[group.market_group_id] = group;
        });
        
        // Add children property to each group
        marketGroups.forEach(group => {
            if (group.parent_group_id) {
                const parent = groupsById[group.parent_group_id];
                if (parent) {
                    if (!parent.children) parent.children = [];
                    parent.children.push(group);
                }
            }
        });
        
        // Filter to only return root groups (those without parents)
        const rootGroups = marketGroups.filter(group => !group.parent_group_id);
        
        // Store in cache
        setInCache(cacheKey, rootGroups, 24 * 60 * 60 * 1000); // 24 hours
        
        res.json(rootGroups);
    } catch (error) {
        console.error('Market groups error:', error);
        res.status(500).json({
            error: 'Market group retrieval failed',
            details: error.message
        });
    }
});

// Search for items by name
app.get('/api/universe/types/search', async (req, res) => {
    try {
        const { query, category, group } = req.query;
        
        if (!query || query.length < 3) {
            return res.status(400).json({ error: 'Search query must be at least 3 characters' });
        }
        
        // This is a simplified search. In a production app, you would use a proper search index.
        // For now, we'll search using the public ESI search endpoint
        
        const searchUrl = `https://esi.evetech.net/latest/search/?categories=inventory_type&search=${encodeURIComponent(query)}&strict=false`;
        
        const searchResponse = await fetch(searchUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!searchResponse.ok) {
            return res.status(searchResponse.status).json({
                error: 'Failed to search items',
                details: `ESI returned status ${searchResponse.status}`
            });
        }
        
        const searchResults = await searchResponse.json();
        const typeIds = searchResults.inventory_type || [];
        
        if (typeIds.length === 0) {
            return res.json([]);
        }
        
        // Fetch details for each type (in batches to avoid rate limiting)
        const types = [];
        const batchSize = 10;
        
        for (let i = 0; i < typeIds.length && i < 100; i += batchSize) { // Limit to 100 results
            const batch = typeIds.slice(i, i + batchSize);
            const batchPromises = batch.map(typeId =>
                fetch(`https://esi.evetech.net/latest/universe/types/${typeId}/`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                })
                .then(resp => resp.ok ? resp.json() : null)
                .catch(() => null)
            );
            
            const results = await Promise.all(batchPromises);
            types.push(...results.filter(Boolean));
        }
        
        // Filter by category or group if specified
        let filteredTypes = types;
        
        if (category) {
            filteredTypes = filteredTypes.filter(type => type.category_id === parseInt(category));
        }
        
        if (group) {
            filteredTypes = filteredTypes.filter(type => type.group_id === parseInt(group));
        }
        
        res.json(filteredTypes);
    } catch (error) {
        console.error('Type search error:', error);
        res.status(500).json({
            error: 'Type search failed',
            details: error.message
        });
    }
});

// Enhanced market orders endpoint with filtering
app.get('/api/markets/:regionId/orders/filtered', async (req, res) => {
    try {
        const { regionId } = req.params;
        const { typeIds, categoryId, groupId, minPrice, maxPrice } = req.query;
        
        // If specific type IDs are provided, use them
        if (typeIds) {
            const typeIdArray = typeIds.split(',').map(id => parseInt(id));
            
            // Fetch orders for each type ID
            const orderPromises = typeIdArray.map(typeId =>
                fetch(`https://esi.evetech.net/latest/markets/${regionId}/orders/?type_id=${typeId}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                })
                .then(resp => resp.ok ? resp.json() : [])
                .catch(() => [])
            );
            
            const ordersArrays = await Promise.all(orderPromises);
            let allOrders = [].concat(...ordersArrays);
            
            // Apply price filters if specified
            if (minPrice) {
                allOrders = allOrders.filter(order => order.price >= parseFloat(minPrice));
            }
            
            if (maxPrice) {
                allOrders = allOrders.filter(order => order.price <= parseFloat(maxPrice));
            }
            
            return res.json(allOrders);
        }
        
        // If category or group filtering is requested, we need to:
        // 1. Get all types in the category/group
        // 2. Fetch orders for each type
        
        if (categoryId || groupId) {
            let typeIds = [];
            
            if (groupId) {
                // Get types in the group
                const groupUrl = `https://esi.evetech.net/latest/universe/groups/${groupId}/`;
                const groupResponse = await fetch(groupUrl, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                });
                
                if (groupResponse.ok) {
                    const group = await groupResponse.json();
                    typeIds = group.types || [];
                }
            } else if (categoryId) {
                // Get all groups in the category
                const categoryUrl = `https://esi.evetech.net/latest/universe/categories/${categoryId}/`;
                const categoryResponse = await fetch(categoryUrl, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                });
                
                if (categoryResponse.ok) {
                    const category = await categoryResponse.json();
                    const groupIds = category.groups || [];
                    
                    // Get types for each group
                    for (const groupId of groupIds) {
                        const groupUrl = `https://esi.evetech.net/latest/universe/groups/${groupId}/`;
                        const groupResponse = await fetch(groupUrl, {
                            method: 'GET',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                                'User-Agent': 'EVE-Market-Comparison/2.0'
                            }
                        });
                        
                        if (groupResponse.ok) {
                            const group = await groupResponse.json();
                            typeIds.push(...(group.types || []));
                        }
                    }
                }
            }
            
            // Limit to a reasonable number of types to avoid excessive API calls
            typeIds = typeIds.slice(0, 50);
            
            // Fetch orders for each type ID
            const orderPromises = typeIds.map(typeId =>
                fetch(`https://esi.evetech.net/latest/markets/${regionId}/orders/?type_id=${typeId}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'EVE-Market-Comparison/2.0'
                    }
                })
                .then(resp => resp.ok ? resp.json() : [])
                .catch(() => [])
            );
            
            const ordersArrays = await Promise.all(orderPromises);
            let allOrders = [].concat(...ordersArrays);
            
            // Apply price filters if specified
            if (minPrice) {
                allOrders = allOrders.filter(order => order.price >= parseFloat(minPrice));
            }
            
            if (maxPrice) {
                allOrders = allOrders.filter(order => order.price <= parseFloat(maxPrice));
            }
            
            return res.json(allOrders);
        }
        
        // If no filtering is specified, return all orders (with a warning about performance)
        const url = `https://esi.evetech.net/latest/markets/${regionId}/orders/`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Failed to fetch market data',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Filtered market error:', error);
        res.status(500).json({
            error: 'Filtered market data retrieval failed',
            details: error.message
        });
    }
});

// User filter management endpoints
app.post('/api/user/filters', (req, res) => {
    try {
        // In a real app, this would be stored in a database with user authentication
        // For this prototype, we'll just return success
        res.json({ success: true, message: 'Filter saved' });
    } catch (error) {
        console.error('Save filter error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/user/filters', (req, res) => {
    try {
        // In a real app, this would fetch from a database with user authentication
        // For this prototype, we'll just return an empty array
        res.json([]);
    } catch (error) {
        console.error('Get filters error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Simple in-memory cache
const cache = {};

function getFromCache(key) {
    const item = cache[key];
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
        delete cache[key];
        return null;
    }
    
    return item.data;
}

function getCacheTimeLeft(key) {
    const item = cache[key];
    if (!item) return 0;
    
    const timeLeft = item.expiry - Date.now();
    return timeLeft > 0 ? timeLeft : 0;
}

function setInCache(key, data, ttlMs) {
    cache[key] = {
        data,
        expiry: Date.now() + ttlMs
    };
}

// Add this route to your server

app.get('/api/universe/groups/:groupId/types', async (req, res) => {
    try {
        const { groupId } = req.params;
        
        // Use ESI endpoint to get all types in a group
        const url = `https://esi.evetech.net/latest/universe/groups/${groupId}/`;
        
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'EVE Market Comparison Tool/2.0'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Failed to fetch group info',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const groupInfo = await response.json();
        
        // Return the types array from the group info
        if (!groupInfo.types || !Array.isArray(groupInfo.types)) {
            console.error('Invalid group info structure:', groupInfo);
            return res.json([]);
        }
        
        console.log(`Group ${groupId} has ${groupInfo.types.length} types`);
        res.json(groupInfo.types.map(typeId => ({ type_id: typeId })));
        
    } catch (error) {
        console.error('Error fetching group types:', error);
        res.status(500).json({
            error: 'Failed to fetch group types',
            details: error.message
        });
    }
});

// Add this route to handle individual category details
app.get('/api/universe/categories/:categoryId', async (req, res) => {
    try {
        const { categoryId } = req.params;
        
        // Check cache first
        const cacheKey = `category_${categoryId}`;
        const cachedData = getFromCache(cacheKey);
        
        if (cachedData) {
            return res.json(cachedData);
        }
        
        const url = `https://esi.evetech.net/latest/universe/categories/${categoryId}/`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Failed to fetch category details',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const data = await response.json();
        
        // Store in cache
        setInCache(cacheKey, data, 24 * 60 * 60 * 1000); // 24 hours
        
        res.json(data);
    } catch (error) {
        console.error('Category details error:', error);
        res.status(500).json({
            error: 'Category details retrieval failed',
            details: error.message
        });
    }
});

// Add this route after the /api/universe/groups/:categoryId route
app.get('/api/universe/groups/:groupId', async (req, res) => {
    try {
        const { groupId } = req.params;
        
        // Check cache first
        const cacheKey = `group_${groupId}`;
        const cachedData = getFromCache(cacheKey);
        
        if (cachedData) {
            return res.json(cachedData);
        }
        
        const url = `https://esi.evetech.net/latest/universe/groups/${groupId}/`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'EVE-Market-Comparison/2.0'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({
                error: 'Failed to fetch group details',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const data = await response.json();
        
        // Store in cache
        setInCache(cacheKey, data, 24 * 60 * 60 * 1000); // 24 hours
        
        res.json(data);
    } catch (error) {
        console.error('Group details error:', error);
        res.status(500).json({
            error: 'Group details retrieval failed',
            details: error.message
        });
    }
});

app.listen(8085, () => {
    console.log('Server running on http://localhost:8085');
    console.log('Make sure your EVE app callback URL is: http://localhost:8085/callback');
});