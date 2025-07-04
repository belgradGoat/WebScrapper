// This file handles the authentication process with the EVE Online SSO.
// It includes functions for redirecting users to the login page, receiving the authorization code, and exchanging it for access tokens.

// This file handles the authentication process with the EVE Online SSO.
// It includes functions for redirecting users to the login page, receiving the authorization code, and exchanging it for access tokens.

const clientId = 'b1ee25b8600a462bbe94c23defd64eeb'; // Replace with your EVE Online application client ID
const redirectUri = 'http://localhost:8085/callback'; // Replace with your redirect URI

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
    
    // Try v2 OAuth endpoint
    const authUrl = `https://login.eveonline.com/v2/oauth/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&state=${state}`;
    
    console.log('Redirecting to v2 auth URL:', authUrl);
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
            
            // Store the access token and refresh token
            localStorage.setItem('eveAccessToken', tokenData.access_token);
            localStorage.setItem('eveRefreshToken', tokenData.refresh_token);
            localStorage.setItem('eveTokenExpiry', Date.now() + (tokenData.expires_in * 1000));
            
            // Redirect to the main application page
            window.location.href = '/index.html';
        } catch (error) {
            console.error('Authentication error:', error);
            alert('Authentication failed. Please try again.');
        }
    } else {
        console.log('No authorization code found in URL');
    }
}

// Update the authenticateUser function to match what's called from index.html
function authenticateUser() {
    redirectToLogin();
}

// Call authenticate on page load only if we're on the callback page
if (window.location.pathname.includes('callback')) {
    document.addEventListener('DOMContentLoaded', authenticate);
}