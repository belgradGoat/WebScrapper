const https = require('https');

function testESIDirect() {
    console.log('Testing ESI endpoints directly...\n');
    
    // Test 1: Public endpoint (no auth required)
    testPublicEndpoint();
    
    // Test 2: Get server status
    setTimeout(() => testServerStatus(), 1000);
}

function testPublicEndpoint() {
    console.log('--- Testing Public Market Orders (The Forge) ---');
    
    const options = {
        hostname: 'esi.evetech.net',
        port: 443,
        path: '/latest/markets/10000002/orders/?type_id=34',  // Tritanium in The Forge
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'User-Agent': 'EVE-Market-Test/1.0'
        }
    };
    
    const req = https.request(options, (res) => {
        console.log(`Status: ${res.statusCode}`);
        
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            try {
                const orders = JSON.parse(data);
                console.log(`Found ${orders.length} orders for Tritanium in The Forge`);
                if (orders.length > 0) {
                    console.log('First order:', JSON.stringify(orders[0], null, 2));
                }
            } catch (e) {
                console.log('Response:', data.substring(0, 200));
            }
        });
    });
    
    req.on('error', (e) => {
        console.error('Request error:', e);
    });
    
    req.end();
}

function testServerStatus() {
    console.log('\n--- Testing Server Status ---');
    
    const options = {
        hostname: 'esi.evetech.net',
        port: 443,
        path: '/latest/status/',
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'User-Agent': 'EVE-Market-Test/1.0'
        }
    };
    
    const req = https.request(options, (res) => {
        console.log(`Status: ${res.statusCode}`);
        
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            console.log('Response:', data);
        });
    });
    
    req.on('error', (e) => {
        console.error('Request error:', e);
    });
    
    req.end();
}

testESIDirect();