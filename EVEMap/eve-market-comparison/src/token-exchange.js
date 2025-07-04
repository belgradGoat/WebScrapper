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
    
    console.log('Token exchange request received (V2 only)');
    console.log('Code:', code ? 'Present' : 'Missing');
    
    if (!code) {
        return res.status(400).json({ error: 'Authorization code is required' });
    }
    
    try {
        // Use V2 OAuth endpoint only
        console.log('Using V2 token endpoint exclusively...');
        
        const v2TokenUrl = 'https://login.eveonline.com/v2/oauth/token';
        const v2Body = new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            redirect_uri: 'http://localhost:8085/callback'
        });
        
        const response = await fetch(v2TokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'EVE-Market-Comparison/2.0',
                'Host': 'login.eveonline.com',
                'Accept': 'application/json'
            },
            body: v2Body.toString()
        });
        
        console.log('V2 Response Status:', response.status);
        console.log('V2 Response Headers:', JSON.stringify([...response.headers.entries()]));
        
        const responseText = await response.text();
        console.log('V2 Raw response:', responseText);
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse V2 response as JSON:', e);
            return res.status(500).json({
                error: 'Invalid response from EVE OAuth V2 server',
                details: 'Response was not valid JSON'
            });
        }
        
        if (!response.ok) {
            console.error('EVE OAuth V2 Error Response:', data);
            return res.status(response.status).json({
                error: data.error || 'V2 Token exchange failed',
                error_description: data.error_description || 'Unknown V2 OAuth error'
            });
        }
        
        // Strict validation of V2 JWT token
        const validateJWTToken = (token) => {
            if (!token) {
                throw new Error('No token provided');
            }
            
            // Check JWT token format
            if (!token.startsWith('eyJ')) {
                throw new Error('Invalid token format: Not a JWT');
            }
            
            // Basic JWT structure validation
            const parts = token.split('.');
            if (parts.length !== 3) {
                throw new Error('Invalid JWT: Incorrect number of parts');
            }
            
            // Optional: Base64 decoding validation (without revealing sensitive info)
            try {
                const header = JSON.parse(Buffer.from(parts[0], 'base64').toString('utf-8'));
                if (header.typ !== 'JWT') {
                    throw new Error('Invalid JWT header');
                }
            } catch (e) {
                throw new Error('JWT header validation failed');
            }
            
            return true;
        };
        
        try {
            // Validate access token
            validateJWTToken(data.access_token);
        } catch (validationError) {
            console.error('JWT Token Validation Error:', validationError.message);
            return res.status(401).json({
                error: 'Invalid V2 JWT Token',
                details: validationError.message
            });
        }
        
        console.log('V2 Token exchange successful');
        console.log('Token type:', data.token_type);
        console.log('Token format check - starts with eyJ (JWT)?:', data.access_token?.startsWith('eyJ'));
        console.log('Token length:', data.access_token?.length);
        
        res.json(data);
        
    } catch (error) {
        console.error('V2 Token exchange error:', error);
        res.status(500).json({
            error: 'V2 Token exchange failed',
            details: error.message
        });
    }
});

// Proxy for public market orders
app.get('/api/markets/:regionId/orders', async (req, res) => {
    try {
        const { regionId } = req.params;
        console.log(`Fetching ALL orders for region ${regionId}...`);
        
        let allOrders = [];
        let page = 1;
        let hasMorePages = true;
        
        while (hasMorePages) {
            const url = `https://esi.evetech.net/latest/markets/${regionId}/orders/?page=${page}`;
            console.log(`Fetching page ${page}...`);
            
            const response = await fetch(url, {
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

// Update structure endpoint to fetch all pages too:
app.get('/api/markets/structures/:structureId', async (req, res) => {
    try {
        const { structureId } = req.params;
        const authHeader = req.headers.authorization;
        console.log('Structure request - Auth header:', authHeader ? 'Present' : 'Missing');
        
        const token = authHeader?.replace('Bearer ', '');
        
        if (!token) {
            return res.status(401).json({ error: 'No authorization token provided' });
        }

        if (!token.startsWith('eyJ')) {
            console.error('Invalid token format: Not a V2 JWT');
            return res.status(401).json({
                error: 'Invalid authentication token',
                details: 'Only V2 JWT tokens are supported'
            });
        }
        
        console.log(`Fetching ALL orders for structure ${structureId}...`);
        
        let allOrders = [];
        let page = 1;
        let hasMorePages = true;
        
        while (hasMorePages) {
            const url = `https://esi.evetech.net/latest/markets/structures/${structureId}/?page=${page}`;
            console.log(`Fetching structure page ${page}...`);
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'User-Agent': 'EVE-Market-Comparison/2.0'
                }
            });
            
            console.log(`Structure page ${page} response status:`, response.status);
            
            if (response.ok) {
                const pageData = await response.json();
                allOrders = allOrders.concat(pageData);
                
                // Check if there are more pages
                const totalPages = parseInt(response.headers.get('x-pages') || '1');
                if (page >= totalPages) {
                    hasMorePages = false;
                } else {
                    page++;
                }
                
                // Add small delay to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 100));
            } else if (response.status === 404 && page > 1) {
                // No more pages
                hasMorePages = false;
            } else {
                // Error on first page or auth error
                const errorText = await response.text();
                console.error('Structure market error:', errorText);
                
                if (response.status === 401) {
                    return res.status(401).json({
                        error: 'Failed to authenticate with ESI',
                        details: 'V2 JWT token authentication failed. Please re-login.'
                    });
                }
                
                return res.status(response.status).json({
                    error: 'Failed to fetch structure market data',
                    details: `ESI returned status ${response.status}`
                });
            }
        }
        
        console.log(`Fetched ${allOrders.length} total structure orders from ${page-1} pages`);
        return res.json(allOrders);
        
    } catch (error) {
        console.error('Structure market error:', error);
        res.status(500).json({ error: error.message });
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
        const url = `https://esi.evetech.net/latest/universe/types/${typeId}/`;
        
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
                error: 'Failed to fetch item info',
                details: `ESI returned status ${response.status}`
            });
        }
        
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Item info error:', error);
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

function setInCache(key, data, ttlMs) {
    cache[key] = {
        data,
        expiry: Date.now() + ttlMs
    };
}

app.listen(8085, () => {
    console.log('Server running on http://localhost:8085');
    console.log('Make sure your EVE app callback URL is: http://localhost:8085/callback');
});