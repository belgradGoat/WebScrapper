// Simple test script to verify functionality
console.log('=== EVE Market Comparison Test ===');

// Test 1: Check if all required objects are available
console.log('\n1. Checking global objects:');
console.log('window.marketStorage:', !!window.marketStorage);
console.log('window.marketAPI:', !!window.marketAPI);
console.log('window.marketFilters:', !!window.marketFilters);

// Test 2: Check if all required functions are available
console.log('\n2. Checking global functions:');
const requiredFunctions = [
    'compareMarkets',
    'compareCategoryMarkets',
    'initializeMarketFilters',
    'setFilter',
    'getMarketIdInfo'
];

requiredFunctions.forEach(funcName => {
    console.log(`${funcName}:`, typeof window[funcName] === 'function' ? 'Available' : 'Missing');
});

// Test 3: Test market ID detection
console.log('\n3. Testing market ID detection:');
const testIds = ['10000002', '60003760', '30000142'];
testIds.forEach(id => {
    try {
        const info = window.getMarketIdInfo(id);
        console.log(`ID ${id}:`, info.type);
    } catch (error) {
        console.log(`ID ${id}: Error -`, error.message);
    }
});

// Test 4: Test IndexedDB storage
console.log('\n4. Testing IndexedDB storage:');
if (window.marketStorage) {
    window.marketStorage.clearAll().then(() => {
        console.log('Storage cleared successfully');
        
        // Test storing some data
        const testOrders = [
            { type_id: 34, price: 1000, volume_remain: 100 },
            { type_id: 35, price: 2000, volume_remain: 200 }
        ];
        
        return window.marketStorage.storeMarketOrders('test-location', testOrders);
    }).then(() => {
        console.log('Test orders stored successfully');
        
        return window.marketStorage.getMarketOrders('test-location');
    }).then(orders => {
        console.log('Retrieved orders:', orders ? orders.length : 'null');
        
        // Clean up
        return window.marketStorage.clearAll();
    }).then(() => {
        console.log('Storage test completed and cleaned up');
    }).catch(error => {
        console.error('Storage test failed:', error);
    });
} else {
    console.log('MarketStorage not available');
}

// Test 5: Test filter initialization
console.log('\n5. Testing filter initialization:');
if (typeof window.initializeMarketFilters === 'function') {
    try {
        window.initializeMarketFilters();
        console.log('Filter initialization successful');
        console.log('Excluded categories:', window.marketFilters.excludedCategoryIds);
    } catch (error) {
        console.log('Filter initialization failed:', error.message);
    }
} else {
    console.log('initializeMarketFilters function not available');
}

console.log('\n=== Test Complete ===');
