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
    console.log('Code:', code ? 'Present' : 'Missing');
    
    if (!code) {
        return res.status(400).json({ error: 'Authorization code is required' });
    }
    
    try {
        // Try v2 endpoint first (without Basic auth, using client_id and client_secret in body)
        console.log('Trying V2 token endpoint...');
        
        const v2TokenUrl = 'https://login.eveonline.com/v2/oauth/token';
        const v2Body = new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            redirect_uri: 'http://localhost:8085/callback'
        });
        
        let response = await fetch(v2TokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'EVE-Market-Comparison/1.0',
                'Host': 'login.eveonline.com'
            },
            body: v2Body.toString()
        });
        
        console.log('V2 Response Status:', response.status);
        
        if (response.status === 404 || response.status === 400) {
            // V2 endpoint not available or failed, try V1
            console.log('V2 failed, trying V1 endpoint...');
            
            const tokenUrl = 'https://login.eveonline.com/oauth/token';
            const authHeader = 'Basic ' + Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');
            const body = new URLSearchParams({
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: 'http://localhost:8085/callback'
            });
            
            response = await fetch(tokenUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': authHeader,
                    'User-Agent': 'EVE-Market-Comparison/1.0'
                },
                body: body.toString()
            });
        }
        
        console.log('Final Response Status:', response.status);
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
        console.log('Token type:', data.token_type);
        console.log('Token format check - starts with eyJ?:', data.access_token?.startsWith('eyJ'));
        
        // If we still get opaque tokens, warn about it
        if (data.access_token && !data.access_token.startsWith('eyJ')) {
            console.warn('WARNING: Received opaque token instead of JWT!');
            console.warn('This is a known issue with EVE OAuth. ESI may not accept this token.');
            
            // Add a flag to the response
            data._tokenFormatWarning = 'Token is in opaque format, not JWT. ESI authentication may fail.';
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