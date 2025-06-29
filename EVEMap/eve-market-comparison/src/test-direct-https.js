const https = require('https');
const querystring = require('querystring');

const CLIENT_ID = 'b1ee25b8600a462bbe94c23defd64eeb';
const CLIENT_SECRET = 'vqVoMi6dRfgRJh03GSH77q2boukqqUgIb99tkeho';

function testDirectHttps(code) {
    const postData = querystring.stringify({
        grant_type: 'authorization_code',
        code: code,
        redirect_uri: 'http://localhost:8085/callback'
    });

    const auth = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');

    const options = {
        hostname: 'login.eveonline.com',
        port: 443,
        path: '/oauth/token',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': postData.length,
            'Authorization': `Basic ${auth}`
        }
    };

    const req = https.request(options, (res) => {
        console.log('Status Code:', res.statusCode);
        console.log('Headers:', res.headers);

        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });

        res.on('end', () => {
            console.log('Response:', data);
            try {
                const parsed = JSON.parse(data);
                console.log('Parsed:', JSON.stringify(parsed, null, 2));
                if (parsed.access_token) {
                    console.log('Token starts with eyJ?', parsed.access_token.startsWith('eyJ'));
                }
            } catch (e) {
                console.log('Failed to parse JSON');
            }
        });
    });

    req.on('error', (e) => {
        console.error('Request error:', e);
    });

    req.write(postData);
    req.end();
}

const code = process.argv[2];
if (code) {
    testDirectHttps(code);
} else {
    console.log('Usage: node src/test-direct-https.js YOUR_AUTH_CODE');
}