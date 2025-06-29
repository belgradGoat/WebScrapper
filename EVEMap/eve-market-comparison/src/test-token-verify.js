const https = require('https');

async function verifyToken(token) {
    // First, let's try the official ESI endpoint
    console.log('Testing token with ESI...\n');
    
    // Test 1: Try the verify endpoint
    await testEndpoint(
        'Verify Token',
        'esi.evetech.net',
        '/verify/',
        'GET',
        null,
        token
    );
    
    // Test 2: Try a simple public endpoint with auth
    await testEndpoint(
        'Character Info',
        'esi.evetech.net',
        '/latest/status/',
        'GET',
        null,
        token
    );
    
    // Test 3: Try the structure market endpoint
    const structureId = '1035466617946'; // Jita 4-4 CNAP
    await testEndpoint(
        'Structure Market',
        'esi.evetech.net',
        `/latest/markets/structures/${structureId}/`,
        'GET',
        null,
        token
    );
}

function testEndpoint(name, hostname, path, method, body, token) {
    return new Promise((resolve) => {
        console.log(`\n--- Testing: ${name} ---`);
        console.log(`Endpoint: https://${hostname}${path}`);
        
        const options = {
            hostname,
            port: 443,
            path,
            method,
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'EVE-Market-Test/1.0'
            }
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
        
        if (body) {
            options.headers['Content-Type'] = 'application/json';
            options.headers['Content-Length'] = body.length;
        }
        
        const req = https.request(options, (res) => {
            console.log(`Status: ${res.statusCode}`);
            console.log(`Headers: ${JSON.stringify(res.headers)}`);
            
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                console.log('Response:', data.substring(0, 200) + (data.length > 200 ? '...' : ''));
                resolve();
            });
        });
        
        req.on('error', (e) => {
            console.error('Request error:', e);
            resolve();
        });
        
        if (body) {
            req.write(body);
        }
        
        req.end();
    });
}

const token = process.argv[2];
if (token) {
    verifyToken(token);
} else {
    console.log('Usage: node src/test-token-verify.js YOUR_ACCESS_TOKEN');
    console.log('\nGet your token from localStorage:');
    console.log('localStorage.getItem("eveAccessToken")');
}