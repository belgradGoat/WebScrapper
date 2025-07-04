const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const CLIENT_ID = 'b1ee25b8600a462bbe94c23defd64eeb';
const CLIENT_SECRET = 'vqVoMi6dRfgRJh03GSH77q2boukqqUgIb99tkeho';

async function testDirectAuth() {
    // Use V2 OAuth endpoint
    const authUrl = `https://login.eveonline.com/v2/oauth/authorize?response_type=code&client_id=${CLIENT_ID}&redirect_uri=http://localhost:8085/callback&scope=esi-markets.structure_markets.v1&state=testing123`;
    
    console.log('Visit this URL to get an auth code (V2 endpoint):');
    console.log(authUrl);
    console.log('\nAfter authorization, copy the "code" parameter from the redirect URL');
    console.log('Then run: node src/test-eve-auth.js YOUR_CODE_HERE\n');
    
    const code = process.argv[2];
    if (!code) {
        return;
    }
    
    console.log('Testing with code:', code.substring(0, 10) + '...');
    
    // Test only the v2 token endpoint
    console.log('\n--- Testing V2 Token Endpoint ---');
    await testTokenEndpoint('https://login.eveonline.com/v2/oauth/token', code);
}

async function testTokenEndpoint(tokenUrl, code) {
    try {
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
                'Host': 'login.eveonline.com',
                'User-Agent': 'EVE-Market-Test/2.0'
            },
            body: body.toString()
        });
        
        console.log('Response status:', response.status);
        
        const text = await response.text();
        console.log('Raw response:', text);
        
        try {
            const data = JSON.parse(text);
            
            if (data.access_token) {
                console.log('\nToken preview:', data.access_token.substring(0, 50) + '...');
                console.log('Token starts with "eyJ"?:', data.access_token.startsWith('eyJ'));
                console.log('Token format looks like JWT?:', data.access_token.split('.').length === 3);
            }
        } catch (e) {
            console.log('Could not parse as JSON');
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

testDirectAuth();