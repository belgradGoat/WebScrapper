// This file handles the authentication process with the EVE Online SSO.
// It includes functions for redirecting users to the login page, receiving the authorization code, and exchanging it for access tokens.

const clientId = 'b1ee25b8600a462bbe94c23defd64eeb';
const redirectUri = 'http://localhost:8085/callback';

// Updated with correct EVE Online ESI scopes for market comparison
const scope = [
    'esi-markets.structure_markets.v1',    // Read market data in structures
    'esi-universe.read_structures.v1',      // Read structure information
    'esi-markets.read_character_orders.v1', // Read character market orders
    'esi-wallet.read_character_wallet.v1'   // Read wallet for trade tracking (optional)
].join(' ');

function redirectToLogin() {
    // Generate state for security
    const state = Math.random().toString(36).substring(7);
    sessionStorage.setItem('oauth_state', state);
    
    // Use v2 OAuth endpoint
    const authUrl = `https://login.eveonline.com/v2/oauth/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&state=${state}`;
    
    console.log('Redirecting to EVE Online v2 auth URL:', authUrl);
    window.location.href = authUrl;
}

function getAuthorizationCode() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('code');
}

async function exchangeCodeForToken(code) {
    const response = await fetch('/api/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
    });

    if (!response.ok) {
        throw new Error('Failed to exchange code for token');
    }

    const data = await response.json();
    return data;
}

async function authenticate() {
    const code = getAuthorizationCode();
    if (code) {
        try {
            const tokenData = await exchangeCodeForToken(code);
            console.log('Full token data received:', tokenData);
            console.log('Token data keys:', Object.keys(tokenData));
            
            if (tokenData.access_token) {
                localStorage.setItem('eveAccessToken', tokenData.access_token);
                console.log('Token stored successfully');
                
                // Redirect to main page
                window.location.href = '/';
            } else {
                throw new Error('No access token received');
            }
        } catch (error) {
            console.error('Authentication error:', error);
            alert('Authentication failed: ' + error.message);
        }
    } else {
        console.log('No authorization code found in URL');
    }
}

// Initialize login button and check authentication status
document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        // Check if already logged in
        const token = localStorage.getItem('eveAccessToken');
        if (token) {
            loginBtn.textContent = 'Logged In ✓';
            loginBtn.style.backgroundColor = '#4CAF50';
            loginBtn.onclick = () => {
                if (confirm('Do you want to logout?')) {
                    localStorage.removeItem('eveAccessToken');
                    window.location.reload();
                }
            };
        } else {
            loginBtn.textContent = 'Login with EVE Online';
            loginBtn.onclick = redirectToLogin;
        }
    }
    
    // Auto-authenticate if we're on callback page
    if (window.location.pathname.includes('callback')) {
        authenticate();
    }
});