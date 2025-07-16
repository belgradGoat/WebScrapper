/**
 * Test Category Filtering with Real EVE Database
 * Copy and paste this into browser console when on the main application page
 */

async function testWithRealEVEData() {
    console.log('🚀 TESTING CATEGORY FILTERING WITH REAL EVE DATA');
    console.log('================================================');
    
    // Check if we're on the right page
    if (!window.marketFilters || !window.filterOpportunities) {
        console.error('❌ Please run this on the main application page (index.html) where market functions are loaded');
        return;
    }
    
    // Step 1: Check current state
    console.log('\n📋 Step 1: Current State Check');
    console.log('marketFilters:', window.marketFilters);
    console.log('excludedCategoryIds:', window.marketFilters.excludedCategoryIds);
    
    // Step 2: Clear any existing exclusions
    console.log('\n📋 Step 2: Clearing existing exclusions');
    if (window.setFilter) {
        window.setFilter('excludedCategoryIds', []);
        console.log('✅ Cleared exclusions using setFilter');
    } else {
        window.marketFilters.excludedCategoryIds = [];
        console.log('✅ Cleared exclusions directly');
    }
    
    // Step 3: Create realistic test data with real EVE item categories
    console.log('\n📋 Step 3: Creating realistic test data');
    const realTestData = [
        // Ships (Category 6)
        { typeId: 588, itemName: "Rifter", categoryId: 6, buyPrice: 500000, sellPrice: 750000, profit: 250000, profitPercent: 50 },
        { typeId: 589, itemName: "Breacher", categoryId: 6, buyPrice: 600000, sellPrice: 900000, profit: 300000, profitPercent: 50 },
        
        // Modules & Equipment (Category 7) 
        { typeId: 2048, itemName: "Damage Control II", categoryId: 7, buyPrice: 2000000, sellPrice: 2500000, profit: 500000, profitPercent: 25 },
        { typeId: 5973, itemName: "Small Shield Extender II", categoryId: 7, buyPrice: 150000, sellPrice: 200000, profit: 50000, profitPercent: 33 },
        
        // Ammunition & Charges (Category 8)
        { typeId: 278, itemName: "Fusion S", categoryId: 8, buyPrice: 5, sellPrice: 8, profit: 3, profitPercent: 60 },
        
        // Blueprints (Category 9) 
        { typeId: 1006, itemName: "Rifter Blueprint", categoryId: 9, buyPrice: 1000000, sellPrice: 1500000, profit: 500000, profitPercent: 50 },
        
        // Commodities (Category 43)
        { typeId: 34, itemName: "Tritanium", categoryId: 43, buyPrice: 5, sellPrice: 6, profit: 1, profitPercent: 20 }
    ];
    
    console.log('Test data created with categories:', [...new Set(realTestData.map(d => d.categoryId))]);
    console.log('Items per category:');
    [6, 7, 8, 9, 43].forEach(catId => {
        const items = realTestData.filter(d => d.categoryId === catId);
        console.log(`  Category ${catId}: ${items.length} items (${items.map(i => i.itemName).join(', ')})`);
    });
    
    // Step 4: Test without exclusions
    console.log('\n📋 Step 4: Test without exclusions');
    window.marketFilters.excludedCategoryIds = [];
    const result1 = window.filterOpportunities(realTestData);
    console.log(`Result: ${result1.length}/${realTestData.length} items (expected: ${realTestData.length})`);
    console.log('Items:', result1.map(r => `${r.itemName} (cat:${r.categoryId})`));
    
    // Step 5: Exclude Ships (Category 6) - Common use case
    console.log('\n📋 Step 5: Exclude Ships (Category 6)');
    if (window.setFilter) {
        window.setFilter('excludedCategoryIds', ['6']);
        console.log('✅ Set exclusion using setFilter function');
    } else {
        window.marketFilters.excludedCategoryIds = ['6'];
        console.log('✅ Set exclusion directly');
    }
    
    console.log('Current excluded categories:', window.marketFilters.excludedCategoryIds);
    const result2 = window.filterOpportunities(realTestData);
    const expectedCount2 = realTestData.filter(d => d.categoryId !== 6).length;
    console.log(`Result: ${result2.length}/${realTestData.length} items (expected: ${expectedCount2})`);
    console.log('Items:', result2.map(r => `${r.itemName} (cat:${r.categoryId})`));
    
    const test2Pass = result2.length === expectedCount2;
    console.log(`Ships exclusion test: ${test2Pass ? '✅ PASSED' : '❌ FAILED'}`);
    
    // Step 6: Exclude multiple categories
    console.log('\n📋 Step 6: Exclude Ships and Blueprints (Categories 6, 9)');
    if (window.setFilter) {
        window.setFilter('excludedCategoryIds', ['6', '9']);
    } else {
        window.marketFilters.excludedCategoryIds = ['6', '9'];
    }
    
    const result3 = window.filterOpportunities(realTestData);
    const expectedCount3 = realTestData.filter(d => !['6', '9'].includes(d.categoryId.toString())).length;
    console.log(`Result: ${result3.length}/${realTestData.length} items (expected: ${expectedCount3})`);
    console.log('Items:', result3.map(r => `${r.itemName} (cat:${r.categoryId})`));
    
    const test3Pass = result3.length === expectedCount3;
    console.log(`Multiple exclusion test: ${test3Pass ? '✅ PASSED' : '❌ FAILED'}`);
    
    // Step 7: Test with real market comparison if possible
    console.log('\n📋 Step 7: Testing with actual market comparison');
    const buyLocationInput = document.getElementById('buyLocationInput');
    const sellLocationInput = document.getElementById('sellLocationInput');
    
    if (buyLocationInput && sellLocationInput && buyLocationInput.value && sellLocationInput.value) {
        console.log('Found market inputs with values:', buyLocationInput.value, sellLocationInput.value);
        console.log('💡 You can now run a real market comparison to see if exclusions work with live data');
        console.log('💡 Current exclusions will be applied:', window.marketFilters.excludedCategoryIds);
    } else {
        console.log('⚠️ No market IDs set. Enter market IDs and run comparison to test with real data');
    }
    
    // Final assessment
    const allPass = (result1.length === realTestData.length) && test2Pass && test3Pass;
    console.log('\n🎯 FINAL ASSESSMENT');
    console.log(`Overall result: ${allPass ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
    
    if (!allPass) {
        console.log('\n🔍 TROUBLESHOOTING:');
        console.log('1. Check if filterOpportunities function is working correctly');
        console.log('2. Verify excludedCategoryIds is not being reset');
        console.log('3. Look for console errors during filtering');
        console.log('4. Try running: window.marketFilters.excludedCategoryIds = ["6"]; then test again');
    }
    
    return { passed: allPass, results: { noFilter: result1.length, excludeShips: result2.length, excludeMultiple: result3.length } };
}

// Quick test function
function quickRealDataTest() {
    console.log('🚀 QUICK REAL DATA TEST');
    
    if (!window.filterOpportunities) {
        console.error('❌ filterOpportunities function not available');
        return;
    }
    
    // Real EVE items
    const testItems = [
        { typeId: 588, itemName: "Rifter", categoryId: 6, profit: 100000, profitPercent: 10 },
        { typeId: 2048, itemName: "Damage Control II", categoryId: 7, profit: 50000, profitPercent: 5 }
    ];
    
    // Test without exclusions
    window.marketFilters.excludedCategoryIds = [];
    const result1 = window.filterOpportunities(testItems);
    console.log(`No exclusions: ${result1.length} items (expected: 2)`);
    
    // Test excluding ships
    window.marketFilters.excludedCategoryIds = ['6'];
    const result2 = window.filterOpportunities(testItems);
    console.log(`Exclude ships: ${result2.length} items (expected: 1)`);
    
    const passed = result1.length === 2 && result2.length === 1;
    console.log(`Quick test: ${passed ? '✅ PASSED' : '❌ FAILED'}`);
    
    return passed;
}

// Auto-export to window if in browser
if (typeof window !== 'undefined') {
    window.testWithRealEVEData = testWithRealEVEData;
    window.quickRealDataTest = quickRealDataTest;
    console.log('✅ Real data test functions loaded. Use:');
    console.log('   testWithRealEVEData() - Comprehensive test');
    console.log('   quickRealDataTest() - Quick verification');
}
