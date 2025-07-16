/**
 * Comprehensive Group Filter Test Script
 * Tests the complete group-based filtering pipeline
 */

function runComprehensiveGroupFilterTest() {
    console.log('🚀 COMPREHENSIVE GROUP FILTER TEST');
    console.log('=====================================');
    
    // Test 1: System availability
    console.log('\n📋 Test 1: System Availability');
    const systemCheck = {
        marketAPI: !!window.marketAPI,
        marketFilters: !!window.marketFilters,
        createGroupFilterUI: typeof window.createGroupFilterUI === 'function',
        setFilter: typeof window.setFilter === 'function',
        filterOpportunities: typeof window.filterOpportunities === 'function',
        getGroupInfo: !!(window.marketAPI && window.marketAPI.getGroupInfo),
        saveExcludedGroups: !!(window.marketAPI && window.marketAPI.saveExcludedGroups)
    };
    
    Object.entries(systemCheck).forEach(([key, value]) => {
        console.log(`   ${key}: ${value ? '✅' : '❌'}`);
    });
    
    const systemReady = Object.values(systemCheck).every(v => v);
    console.log(`\n   System Status: ${systemReady ? '✅ READY' : '❌ NOT READY'}`);
    
    if (!systemReady) {
        console.error('❌ Cannot proceed - system not ready');
        return false;
    }
    
    // Test 2: Data structure verification
    console.log('\n📋 Test 2: Data Structure Verification');
    console.log('   marketFilters structure:', window.marketFilters);
    console.log('   Expected group fields:', {
        groupIds: Array.isArray(window.marketFilters.groupIds),
        excludedGroupIds: Array.isArray(window.marketFilters.excludedGroupIds)
    });
    
    // Test 3: Group API functionality
    console.log('\n📋 Test 3: Group API Functionality');
    
    const testGroupIds = [25, 26, 27, 18]; // Frigates, Cruisers, Battleships, Minerals
    
    Promise.all(testGroupIds.map(id => 
        window.marketAPI.getGroupInfo(id).catch(error => ({ error: error.message, id }))
    )).then(results => {
        console.log('   Group API test results:');
        results.forEach(result => {
            if (result.error) {
                console.log(`     Group ${result.id}: ❌ ${result.error}`);
            } else {
                console.log(`     Group ${result.group_id}: ✅ ${result.name}`);
            }
        });
    });
    
    // Test 4: Filter setting and persistence
    console.log('\n📋 Test 4: Filter Setting and Persistence');
    
    // Save original state
    const originalGroupIds = [...(window.marketFilters.groupIds || [])];
    const originalExcludedGroupIds = [...(window.marketFilters.excludedGroupIds || [])];
    
    // Test include groups
    console.log('   Testing include groups...');
    window.setFilter('groupIds', [25, 26]);
    console.log(`     Set groupIds to [25, 26]: ${JSON.stringify(window.marketFilters.groupIds)}`);
    console.log(`     Success: ${JSON.stringify(window.marketFilters.groupIds) === JSON.stringify([25, 26]) ? '✅' : '❌'}`);
    
    // Test exclude groups
    console.log('   Testing exclude groups...');
    window.setFilter('excludedGroupIds', [60, 40]);
    console.log(`     Set excludedGroupIds to [60, 40]: ${JSON.stringify(window.marketFilters.excludedGroupIds)}`);
    console.log(`     Success: ${JSON.stringify(window.marketFilters.excludedGroupIds) === JSON.stringify([60, 40]) ? '✅' : '❌'}`);
    
    // Test persistence
    console.log('   Testing localStorage persistence...');
    const savedGroups = window.marketAPI.getExcludedGroups();
    console.log(`     Saved to localStorage: ${JSON.stringify(savedGroups)}`);
    console.log(`     Persistence working: ${JSON.stringify(savedGroups) === JSON.stringify([60, 40]) ? '✅' : '❌'}`);
    
    // Test 5: Filtering logic
    console.log('\n📋 Test 5: Filtering Logic');
    
    const testOpportunities = [
        {
            typeId: 1001,
            itemName: "Rifter",
            groupId: 25, // Frigate
            categoryId: 6, // Ship
            profit: 1000000,
            profitPercent: 10
        },
        {
            typeId: 1002,
            itemName: "Caracal",
            groupId: 26, // Cruiser
            categoryId: 6, // Ship
            profit: 2000000,
            profitPercent: 15
        },
        {
            typeId: 1003,
            itemName: "Damage Control II",
            groupId: 60, // Modules
            categoryId: 7, // Module
            profit: 500000,
            profitPercent: 20
        },
        {
            typeId: 1004,
            itemName: "Tritanium",
            groupId: 18, // Mineral
            categoryId: 4, // Material
            profit: 100000,
            profitPercent: 5
        }
    ];
    
    console.log('   Test data:', testOpportunities.map(o => `${o.itemName} (group: ${o.groupId})`));
    
    // Test with include groups [25, 26] (Frigates and Cruisers)
    window.marketFilters.groupIds = [25, 26];
    window.marketFilters.excludedGroupIds = [];
    const includeFiltered = window.filterOpportunities(testOpportunities);
    console.log(`   Include groups [25, 26]: ${includeFiltered.length} items (should be 2)`);
    console.log(`     Items: ${includeFiltered.map(o => o.itemName).join(', ')}`);
    console.log(`     Success: ${includeFiltered.length === 2 ? '✅' : '❌'}`);
    
    // Test with exclude groups [60] (exclude modules)
    window.marketFilters.groupIds = [];
    window.marketFilters.excludedGroupIds = [60];
    const excludeFiltered = window.filterOpportunities(testOpportunities);
    console.log(`   Exclude groups [60]: ${excludeFiltered.length} items (should be 3)`);
    console.log(`     Items: ${excludeFiltered.map(o => o.itemName).join(', ')}`);
    console.log(`     Success: ${excludeFiltered.length === 3 ? '✅' : '❌'}`);
    
    // Test with no filters
    window.marketFilters.groupIds = [];
    window.marketFilters.excludedGroupIds = [];
    const noFilters = window.filterOpportunities(testOpportunities);
    console.log(`   No filters: ${noFilters.length} items (should be 4)`);
    console.log(`     Success: ${noFilters.length === 4 ? '✅' : '❌'}`);
    
    // Test 6: UI Integration
    console.log('\n📋 Test 6: UI Integration');
    
    const uiElements = {
        filterPanel: !!document.getElementById('filterPanel'),
        includeGroups: !!document.getElementById('includeGroups'),
        excludeGroups: !!document.getElementById('excludeGroups'),
        filterStatus: !!document.getElementById('filterStatus'),
        presetButtons: document.querySelectorAll('.preset-btn').length
    };
    
    Object.entries(uiElements).forEach(([key, value]) => {
        console.log(`   ${key}: ${typeof value === 'number' ? value + ' found' : (value ? '✅' : '❌')}`);
    });
    
    // Restore original state
    console.log('\n🔄 Restoring original filter state...');
    window.setFilter('groupIds', originalGroupIds);
    window.setFilter('excludedGroupIds', originalExcludedGroupIds);
    
    console.log('\n🎯 COMPREHENSIVE TEST COMPLETE');
    console.log('=====================================');
    
    return true;
}

// Auto-run the test
setTimeout(() => {
    runComprehensiveGroupFilterTest();
}, 2000);

// Make available globally for manual testing
window.runComprehensiveGroupFilterTest = runComprehensiveGroupFilterTest;
