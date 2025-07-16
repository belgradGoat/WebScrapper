// Temporary market data storage using IndexedDB to avoid memory issues

class MarketDataStorage {
    constructor() {
        this.dbName = 'EVEMarketTempStorage';
        this.dbVersion = 1;
        this.db = null;
        this.sessionId = Date.now().toString(); // Unique session ID
    }

    async initialize() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object stores
                if (!db.objectStoreNames.contains('marketOrders')) {
                    const ordersStore = db.createObjectStore('marketOrders', { keyPath: 'id' });
                    ordersStore.createIndex('sessionId', 'sessionId', { unique: false });
                    ordersStore.createIndex('locationId', 'locationId', { unique: false });
                }
                
                if (!db.objectStoreNames.contains('itemInfo')) {
                    const itemsStore = db.createObjectStore('itemInfo', { keyPath: 'type_id' });
                    itemsStore.createIndex('sessionId', 'sessionId', { unique: false });
                }
                
                if (!db.objectStoreNames.contains('opportunities')) {
                    const oppsStore = db.createObjectStore('opportunities', { keyPath: 'id' });
                    oppsStore.createIndex('sessionId', 'sessionId', { unique: false });
                }
            };
        });
    }

    // Store market orders in chunks to avoid memory issues
    async storeMarketOrders(locationId, orders) {
        if (!this.db) await this.initialize();
        
        const transaction = this.db.transaction(['marketOrders'], 'readwrite');
        const store = transaction.objectStore('marketOrders');
        
        // Split orders into chunks of 1000 to avoid large transactions
        const chunkSize = 1000;
        const chunks = [];
        for (let i = 0; i < orders.length; i += chunkSize) {
            chunks.push(orders.slice(i, i + chunkSize));
        }
        
        for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
            const chunk = chunks[chunkIndex];
            const chunkData = {
                id: `${this.sessionId}_${locationId}_${chunkIndex}`,
                sessionId: this.sessionId,
                locationId: locationId,
                chunkIndex: chunkIndex,
                orders: chunk,
                timestamp: Date.now()
            };
            
            await new Promise((resolve, reject) => {
                const request = store.put(chunkData);
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        }
        
        console.log(`Stored ${orders.length} orders for location ${locationId} in ${chunks.length} chunks`);
    }

    // Retrieve market orders
    async getMarketOrders(locationId) {
    if (!this.db) await this.initialize();
    
    const transaction = this.db.transaction(['marketOrders'], 'readonly');
    const store = transaction.objectStore('marketOrders');
    const index = store.index('locationId');
    
    return new Promise((resolve, reject) => {
        const allOrders = [];
        const request = index.openCursor(IDBKeyRange.only(locationId.toString()));
        
        request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                // Combine orders from this chunk
                if (cursor.value.orders && Array.isArray(cursor.value.orders)) {
                    allOrders.push(...cursor.value.orders);
                }
                cursor.continue();
            } else {
                console.log(`Retrieved ${allOrders.length} total orders for location ${locationId}`);
                resolve(allOrders);
            }
        };
        
        request.onerror = () => reject(request.error);
    });
}

async storePartialMarketData(locationId, orders, pageIndex) {
    if (!this.db) await this.initialize();
    
    // Split large pages into smaller chunks
    const maxChunkSize = 100; // Smaller chunks for better handling
    const chunks = [];
    
    for (let i = 0; i < orders.length; i += maxChunkSize) {
        chunks.push(orders.slice(i, i + maxChunkSize));
    }
    
    console.log(`Splitting page ${pageIndex} into ${chunks.length} chunks`);
    
    for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
        const chunk = chunks[chunkIndex];
        const subPageIndex = `${pageIndex}_${chunkIndex}`;
        
        const chunkData = {
            id: `${this.sessionId}_${locationId}_${subPageIndex}`,
            sessionId: this.sessionId,
            locationId: locationId,
            pageIndex: pageIndex,
            subChunkIndex: chunkIndex,
            orders: chunk,
            timestamp: Date.now()
        };
        
        try {
            const transaction = this.db.transaction(['marketOrders'], 'readwrite');
            const store = transaction.objectStore('marketOrders');
            
            await new Promise((resolve, reject) => {
                const request = store.put(chunkData);
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
            
            // Add small delay between chunks to prevent overwhelming IndexedDB
            await new Promise(resolve => setTimeout(resolve, 50));
            
        } catch (error) {
            console.error(`Error storing chunk ${chunkIndex} of page ${pageIndex}:`, error);
            throw error;
        }
    }
    
    console.log(`Successfully stored page ${pageIndex} in ${chunks.length} chunks`);
}

    // Store item info with better memory management
    async storeItemInfo(typeId, itemInfo) {
        if (!this.db) await this.initialize();
        
        const transaction = this.db.transaction(['itemInfo'], 'readwrite');
        const store = transaction.objectStore('itemInfo');
        
        const data = {
            ...itemInfo,
            sessionId: this.sessionId,
            timestamp: Date.now()
        };
        
        return new Promise((resolve, reject) => {
            const request = store.put(data);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // Get item info
    async getItemInfo(typeId) {
        if (!this.db) await this.initialize();
        
        const transaction = this.db.transaction(['itemInfo'], 'readonly');
        const store = transaction.objectStore('itemInfo');
        
        return new Promise((resolve, reject) => {
            const request = store.get(typeId);
            request.onsuccess = () => {
                const result = request.result;
                if (result && result.sessionId === this.sessionId) {
                    resolve(result);
                } else {
                    resolve(null);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    // Store opportunities
    async storeOpportunities(opportunities) {
        if (!this.db) await this.initialize();
        
        const transaction = this.db.transaction(['opportunities'], 'readwrite');
        const store = transaction.objectStore('opportunities');
        
        // Store in chunks to avoid large transactions
        const chunkSize = 500;
        const chunks = [];
        for (let i = 0; i < opportunities.length; i += chunkSize) {
            chunks.push(opportunities.slice(i, i + chunkSize));
        }
        
        for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
            const chunk = chunks[chunkIndex];
            const chunkData = {
                id: `${this.sessionId}_opportunities_${chunkIndex}`,
                sessionId: this.sessionId,
                chunkIndex: chunkIndex,
                opportunities: chunk,
                timestamp: Date.now()
            };
            
            await new Promise((resolve, reject) => {
                const request = store.put(chunkData);
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        }
        
        console.log(`Stored ${opportunities.length} opportunities in ${chunks.length} chunks`);
    }

    // Get opportunities
    async getOpportunities() {
        if (!this.db) await this.initialize();
        
        const transaction = this.db.transaction(['opportunities'], 'readonly');
        const store = transaction.objectStore('opportunities');
        const index = store.index('sessionId');
        
        return new Promise((resolve, reject) => {
            const request = index.getAll(this.sessionId);
            request.onsuccess = () => {
                const chunks = request.result;
                chunks.sort((a, b) => a.chunkIndex - b.chunkIndex);
                
                // Combine all chunks
                const allOpportunities = [];
                chunks.forEach(chunk => {
                    allOpportunities.push(...chunk.opportunities);
                });
                
                resolve(allOpportunities);
            };
            request.onerror = () => reject(request.error);
        });
    }

    // Clean up data from current session
    async cleanupSession() {
        if (!this.db) return;
        
        const stores = ['marketOrders', 'itemInfo', 'opportunities'];
        
        for (const storeName of stores) {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const index = store.index('sessionId');
            
            const request = index.openCursor(this.sessionId);
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    cursor.continue();
                }
            };
        }
        
        console.log(`Cleaned up session data: ${this.sessionId}`);
    }

    // Clean up old sessions (data older than 24 hours)
    async cleanupOldSessions() {
        if (!this.db) return;
        
        const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
        const stores = ['marketOrders', 'itemInfo', 'opportunities'];
        
        for (const storeName of stores) {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            const request = store.openCursor();
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    if (cursor.value.timestamp < oneDayAgo) {
                        cursor.delete();
                    }
                    cursor.continue();
                }
            };
        }
    }

    // Add this new method
    async clearAll() {
        if (!this.db) await this.initialize();
        
        const stores = ['marketOrders', 'itemInfo', 'opportunities'];
        
        for (const storeName of stores) {
            try {
                const transaction = this.db.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);
                await new Promise((resolve, reject) => {
                    const request = store.clear();
                    request.onsuccess = () => resolve();
                    request.onerror = () => reject(request.error);
                });
            } catch (error) {
                console.warn(`Error clearing store ${storeName}:`, error);
            }
        }
        
        console.log('Cleared all market storage data');
    }
}

// Create global instance
window.marketStorage = new MarketDataStorage();

// Cleanup when page unloads
window.addEventListener('beforeunload', () => {
    if (window.marketStorage) {
        window.marketStorage.cleanupSession();
    }
});