// EVE Market API handler for browser use
class EVEMarketAPI {
    constructor() {
        this.baseUrl = '/api'; // Use local proxy instead of direct ESI
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    async getPublicMarketOrders(regionId) {
        const url = `${this.baseUrl}/markets/${regionId}/orders`;
        
        const response = await fetch(url, { headers: this.headers });
        if (!response.ok) throw new Error('Failed to fetch public market data');
        return response.json();
    }

    async getPrivateStructureMarket(structureId) {
        const token = localStorage.getItem('eveAccessToken');
        console.log('Token exists:', !!token); // Debug log
        
        if (!token) throw new Error('No access token found. Please login first.');
        
        // Create headers object
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': `Bearer ${token}`
        };
        
        console.log('Making request with auth header:', headers.Authorization.substring(0, 50) + '...'); // Debug log
        
        const response = await fetch(
            `${this.baseUrl}/markets/structures/${structureId}`,
            { 
                method: 'GET',
                headers: headers
            }
        );
        
        console.log('Structure response status:', response.status); // Debug log
        
        if (!response.ok) {
            if (response.status === 403) {
                throw new Error('No access to this structure. Make sure you have docking access.');
            }
            if (response.status === 401) {
                throw new Error('Authentication failed. Try logging in again.');
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`Failed to fetch structure market data: ${response.status} - ${errorData.error || 'Unknown error'}`);
        }
        
        return response.json();
    }

    async getItemInfo(typeId) {
        const response = await fetch(
            `${this.baseUrl}/universe/types/${typeId}`,
            { headers: this.headers }
        );
        
        if (!response.ok) throw new Error('Failed to fetch item info');
        return response.json();
    }
}

// Create global instance
window.marketAPI = new EVEMarketAPI();