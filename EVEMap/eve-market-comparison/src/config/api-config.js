const apiConfig = {
    baseURL: 'https://api.eveonline.com', // Base URL for the EVE Swagger API
    marketEndpoint: '/markets', // Endpoint for market data
    privateStructureID: 'YOUR_PRIVATE_STRUCTURE_ID', // Replace with your private structure ID
    scopes: [
        'esi-markets.read_character_market.v1', // Scope for reading character market data
        'esi-markets.read_corporation_market.v1' // Scope for reading corporation market data
    ],
    clientId: 'YOUR_CLIENT_ID', // Replace with your EVE Online application client ID
    clientSecret: 'YOUR_CLIENT_SECRET', // Replace with your EVE Online application client secret
    redirectUri: 'YOUR_REDIRECT_URI' // Replace with your redirect URI
};

export default apiConfig;