/**
 * Quick console test for group-based filtering
 * Run this in the browser console on any page with the updated scripts
 */

function quickGroupFilterTest() {
    console.log('🧪 QUICK GROUP FILTER TEST');
    console.log('==========================');
    
    // Check if functions exist
    if (!window.marketFilters || !window.filterOpportunities) {
        console.error('❌ Required functions not available');
        return false;
    }
    
    // Test data with different groups
    const testData = [
        { typeId: 587, itemName: "Rifter", groupId: 25, profit: 100000, profitPercent: 10 },        // Frigate
        { typeId: 589, itemName: "Slasher", groupId: 25, profit: 80000, profitPercent: 8 },        // Frigate  
        { typeId: 2048, itemName: "Damage Control II", groupId: 60, profit: 50000, profitPercent: 5 }, // Module
        { typeId: 34, itemName: "Tritanium", groupId: 18, profit: 1000, profitPercent: 2 }         // Mineral
    ];
    
    console.log('Test data:', testData.map(t => `${t.itemName} (group ${t.groupId})`));
    
    // Test 1: No filters
    window.marketFilters.groupIds = [];
    window.marketFilters.excludedGroupIds = [];
    const result1 = window.filterOpportunities(testData);
    console.log(`✅ No filters: ${result1.length}/4 items`);
    
    // Test 2: Include only frigates (group 25)
    window.marketFilters.groupIds = [25];
    window.marketFilters.excludedGroupIds = [];
    const result2 = window.filterOpportunities(testData);
    console.log(`✅ Include frigates only: ${result2.length}/4 items (expected: 2)`);
    
    // Test 3: Exclude frigates
    window.marketFilters.groupIds = [];
    window.marketFilters.excludedGroupIds = [25];
    const result3 = window.filterOpportunities(testData);
    console.log(`✅ Exclude frigates: ${result3.length}/4 items (expected: 2)`);
    
    // Reset filters
    window.marketFilters.groupIds = [];
    window.marketFilters.excludedGroupIds = [];
    
    const success = result1.length === 4 && result2.length === 2 && result3.length === 2;
    console.log(`\n🎯 Overall result: ${success ? '✅ SUCCESS' : '❌ FAILED'}`);
    
    return success;
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
    window.quickGroupFilterTest = quickGroupFilterTest;
}
