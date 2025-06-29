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
app.use(express.static(__dirname)); // Serve files from src directory

const CLIENT_ID = 'b1ee25b8600a462bbe94c23defd64eeb';
const CLIENT_SECRET = 'vqVoMi6dRfgRJh03GSH77q2boukqqUgIb99tkeho'; // Replace with your actual secret

// Handle the callback route
app.get('/callback', (req, res) => {
    res.sendFile(path.join(__dirname, 'callback.html'));
});

app.post('/api/token', async (req, res) => {
    const { code } = req.body;
    
    console.log('Token exchange request received');
    console.log('Code:', code ? 'Present' : 'Missing');
    
    if (!code) {
        return res.status(400).json({ error: 'Authorization code is required' });
    }
    
    try {
        const tokenUrl = 'https://login.eveonline.com/oauth/token';
        console.log('Token URL:', tokenUrl);
        console.log('Client ID:', CLIENT_ID);
        
        const authHeader = 'Basic ' + Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');
        const body = new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            redirect_uri: 'http://localhost:8085/callback'
        });
        
        console.log('Making request to EVE OAuth server...');
        console.log('Request body:', body.toString());
        
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': authHeader,
                'User-Agent': 'EVE-Market-Comparison/1.0'
            },
            body: body.toString()
        });
        
        console.log('EVE OAuth Response Status:', response.status);
        console.log('Response Headers:', JSON.stringify(Object.fromEntries(response.headers), null, 2));
        
        const responseText = await response.text();
        console.log('Raw response:', responseText);
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse response as JSON:', e);
            return res.status(500).json({ error: 'Invalid response from EVE OAuth server' });
        }
        
        if (!response.ok) {
            console.error('EVE OAuth Error Response:', data);
            return res.status(response.status).json({ 
                error: data.error || 'Token exchange failed',
                error_description: data.error_description || 'Unknown error'
            });
        }
        
        console.log('Token exchange successful');
        console.log('Full response from EVE:', JSON.stringify(data, null, 2));
        
        // Verify this is an EVE token
        if (data.access_token && !data.access_token.startsWith('eyJ')) {
            console.error('WARNING: Token does not appear to be a JWT!');
            console.error('Token starts with:', data.access_token.substring(0, 10));
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
        const url = `https://esi.evetech.net/latest/markets/${regionId}/orders/`;
        
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({ error: 'Failed to fetch market data' });
        }
        
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Public market error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Proxy for structure market orders - updated to handle new token format
app.get('/api/markets/structures/:structureId', async (req, res) => {
    try {
        const { structureId } = req.params;
        const authHeader = req.headers.authorization;
        console.log('Structure request - Auth header:', authHeader ? 'Present' : 'Missing');
        
        const token = authHeader?.replace('Bearer ', '');
        
        if (!token) {
            return res.status(401).json({ error: 'No authorization token provided' });
        }
        
        // Try multiple ESI endpoints
        const endpoints = [
            `https://esi.evetech.net/latest/markets/structures/${structureId}/`,
            `https://esi.evetech.net/v1/markets/structures/${structureId}/`
        ];
        
        for (const url of endpoints) {
            console.log('Trying ESI endpoint:', url);
            
            const response = await fetch(url, {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'User-Agent': 'EVE-Market-Comparison/1.0'
                }
            });
            
            console.log('ESI Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                return res.json(data);
            }
            
            if (response.status === 401) {
                const errorText = await response.text();
                console.error('Authentication error:', errorText);
                // Try to decode the error
                try {
                    const errorData = JSON.parse(errorText);
                    console.error('Error details:', errorData);
                } catch (e) {
                    // Not JSON
                }
            }
        }
        
        // If we get here, all endpoints failed
        return res.status(401).json({ 
            error: 'Failed to authenticate with ESI',
            details: 'The token format may have changed. Please check EVE developer updates.'
        });
        
    } catch (error) {
        console.error('Structure market error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Add a test endpoint to verify token
app.get('/api/verify-token', async (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        const token = authHeader?.replace('Bearer ', '');
        
        if (!token) {
            return res.status(401).json({ error: 'No token provided' });
        }
        
        // Try to verify the token
        const response = await fetch('https://esi.evetech.net/verify/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('Verify response status:', response.status);
        const text = await response.text();
        console.log('Verify response:', text);
        
        if (response.ok) {
            try {
                const data = JSON.parse(text);
                res.json({ valid: true, data });
            } catch (e) {
                res.json({ valid: false, error: 'Invalid response format' });
            }
        } else {
            res.status(response.status).json({ valid: false, error: text });
        }
        
    } catch (error) {
        console.error('Verify error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Proxy for item info
app.get('/api/universe/types/:typeId', async (req, res) => {
    try {
        const { typeId } = req.params;
        const url = `https://esi.evetech.net/latest/universe/types/${typeId}/`;
        
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            return res.status(response.status).json({ error: 'Failed to fetch item info' });
        }
        
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Item info error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.listen(8085, () => {
    console.log('Server running on http://localhost:8085');
    console.log('Make sure your EVE app callback URL is: http://localhost:8085/callback');
});