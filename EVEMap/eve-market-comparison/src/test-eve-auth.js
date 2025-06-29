const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const CLIENT_ID = 'b1ee25b8600a462bbe94c23defd64eeb';
const CLIENT_SECRET = 'vqVoMi6dRfgRJh03GSH77q2boukqqUgIb99tkeho';

async function testDirectAuth() {
    // First, you need to get a fresh auth code by visiting this URL in your browser:
    const authUrl = `https://login.eveonline.com/oauth/authorize?response_type=code&client_id=${CLIENT_ID}&redirect_uri=http://localhost:8085/callback&scope=esi-markets.structure_markets.v1`;
    
    console.log('Visit this URL to get an auth code:');
    console.log(authUrl);
    console.log('\nAfter authorization, copy the "code" parameter from the redirect URL');
    console.log('Then run: node src/test-eve-auth.js YOUR_CODE_HERE\n');
    
    const code = process.argv[2];
    if (!code) {
        return;
    }
    
    console.log('Testing with code:', code.substring(0, 10) + '...');
    
    try {
        const tokenUrl = 'https://login.eveonline.com/oauth/token';
        const authHeader = 'Basic ' + Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');
        
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': authHeader,
                'Host': 'login.eveonline.com',
                'User-Agent': 'EVE-Market-Test/1.0'
            },
            body: `grant_type=authorization_code&code=${code}&redirect_uri=http://localhost:8085/callback`
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', JSON.stringify(Object.fromEntries(response.headers), null, 2));
        
        const text = await response.text();
        console.log('Raw response:', text);
        
        try {
            const data = JSON.parse(text);
            console.log('\nParsed response:', JSON.stringify(data, null, 2));
            
            if (data.access_token) {
                console.log('\nToken preview:', data.access_token.substring(0, 50) + '...');
                console.log('Token starts with "eyJ"?:', data.access_token.startsWith('eyJ'));
            }
        } catch (e) {
            console.log('Could not parse as JSON');
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

testDirectAuth();