/**
 * Comprehensive Category Filtering Test
 * Run this in browser console to debug the filtering issue
 */

function runComprehensiveCategoryTest() {
    console.log('🧪 COMPREHENSIVE CATEGORY FILTERING TEST');
    console.log('==========================================');
    
    // Step 1: Check if all required functions exist
    console.log('\n📋 Step 1: Function Availability Check');
    const checks = {
        marketFilters: !!window.marketFilters,
        filterOpportunities: !!window.filterOpportunities,
        setFilter: !!window.setFilter,
        marketAPI: !!window.marketAPI
    };
    
    Object.entries(checks).forEach(([name, available]) => {
        console.log(`   ${name}: ${available ? '✅' : '❌'}`);
    });
    
    if (!checks.filterOpportunities) {
        console.error('❌ Cannot proceed - filterOpportunities function not available');
        return;
    }
    
    // Step 2: Check current state
    console.log('\n📋 Step 2: Current Filter State');
    console.log('   marketFilters:', JSON.stringify(window.marketFilters, null, 2));
    
    // Step 3: Create test data
    console.log('\n📋 Step 3: Creating Test Data');
    const testData = [
        { typeId: 1001, itemName: "Test Ship Alpha", categoryId: 6, buyPrice: 1000000, sellPrice: 1500000, profit: 500000, profitPercent: 50 },
        { typeId: 1002, itemName: "Test Module Beta", categoryId: 7, buyPrice: 100000, sellPrice: 150000, profit: 50000, profitPercent: 50 },
        { typeId: 1003, itemName: "Test Ship Gamma", categoryId: 6, buyPrice: 2000000, sellPrice: 2500000, profit: 500000, profitPercent: 25 },
        { typeId: 1004, itemName: "Test Commodity Delta", categoryId: 43, buyPrice: 500000, sellPrice: 600000, profit: 100000, profitPercent: 20 },
        { typeId: 1005, itemName: "Test String Cat", categoryId: "6", buyPrice: 300000, sellPrice: 400000, profit: 100000, profitPercent: 33 }
    ];
    
    console.log('   Test data created:', testData.length, 'items');
    console.log('   Categories in test data:', [...new Set(testData.map(t => t.categoryId))]);
    
    // Step 4: Test without any filters
    console.log('\n📋 Step 4: Test Without Filters');
    window.marketFilters.excludedCategoryIds = [];
    const noFilterResult = window.filterOpportunities(testData);
    console.log(`   Result: ${noFilterResult.length}/${testData.length} items (expected: ${testData.length})`);
    console.log('   Items:', noFilterResult.map(t => `${t.itemName} (cat:${t.categoryId})`));
    
    // Step 5: Test with single category exclusion
    console.log('\n📋 Step 5: Test Excluding Category 6 (Ships)');
    
    // First, let's manually check the filtering logic
    const excludedCategories = ['6'];
    window.marketFilters.excludedCategoryIds = excludedCategories;
    
    console.log('   Before filtering:');
    console.log('     - Excluded categories:', window.marketFilters.excludedCategoryIds);
    console.log('     - Test items by category:');
    testData.forEach(item => {
        const categoryId = item.categoryId.toString();
        const shouldExclude = excludedCategories.includes(categoryId);
        console.log(`       ${item.itemName}: cat ${item.categoryId} (string: ${categoryId}) -> ${shouldExclude ? 'EXCLUDE' : 'KEEP'}`);
    });
    
    const singleExcludeResult = window.filterOpportunities(testData);
    console.log(`   Result: ${singleExcludeResult.length}/${testData.length} items (expected: 2 - only modules and commodities)`);
    console.log('   Remaining items:', singleExcludeResult.map(t => `${t.itemName} (cat:${t.categoryId})`));
    
    // Step 6: Test with multiple category exclusions
    console.log('\n📋 Step 6: Test Excluding Categories 6 and 43 (Ships and Commodities)');
    window.marketFilters.excludedCategoryIds = ['6', '43'];
    const multiExcludeResult = window.filterOpportunities(testData);
    console.log(`   Result: ${multiExcludeResult.length}/${testData.length} items (expected: 1 - only modules)`);
    console.log('   Remaining items:', multiExcludeResult.map(t => `${t.itemName} (cat:${t.categoryId})`));
    
    // Step 7: Test using setFilter function
    console.log('\n📋 Step 7: Test Using setFilter Function');
    if (window.setFilter) {
        window.setFilter('excludedCategoryIds', ['7']); // Exclude modules
        const setFilterResult = window.filterOpportunities(testData);
        console.log(`   Result: ${setFilterResult.length}/${testData.length} items (expected: 3 - ships and commodities)`);
        console.log('   Remaining items:', setFilterResult.map(t => `${t.itemName} (cat:${t.categoryId})`));
    } else {
        console.log('   ❌ setFilter function not available');
    }
    
    // Step 8: Test edge cases
    console.log('\n📋 Step 8: Edge Case Tests');
    
    // Reset filters
    window.marketFilters.excludedCategoryIds = [];
    
    // Test with empty exclusion list
    const emptyResult = window.filterOpportunities(testData);
    console.log(`   Empty exclusions: ${emptyResult.length}/${testData.length} items`);
    
    // Test with non-existent category
    window.marketFilters.excludedCategoryIds = ['999'];
    const nonExistentResult = window.filterOpportunities(testData);
    console.log(`   Non-existent category exclusion: ${nonExistentResult.length}/${testData.length} items`);
    
    // Step 9: Test with real filtering function behavior
    console.log('\n📋 Step 9: Real Function Behavior Test');
    
    // Test the actual filtering steps
    window.marketFilters.excludedCategoryIds = ['6'];
    
    // Simulate what happens inside filterOpportunities
    const excludedCategoriesArray = (window.marketFilters.excludedCategoryIds || []).map(id => id.toString());
    console.log('   Processed excluded categories:', excludedCategoriesArray);
    
    const manualFilterResult = testData.filter(opp => {
        if (opp.categoryId) {
            const categoryId = opp.categoryId.toString();
            if (excludedCategoriesArray.length > 0 && excludedCategoriesArray.includes(categoryId)) {
                console.log(`     Manual check: Excluding ${opp.itemName} from category ${categoryId}`);
                return false;
            }
        }
        return true;
    });
    
    console.log(`   Manual filtering result: ${manualFilterResult.length}/${testData.length} items`);
    
    // Compare with actual function
    const actualResult = window.filterOpportunities(testData);
    console.log(`   Actual function result: ${actualResult.length}/${testData.length} items`);
    console.log(`   Results match: ${manualFilterResult.length === actualResult.length ? '✅' : '❌'}`);
    
    // Final assessment
    console.log('\n🎯 FINAL ASSESSMENT');
    const allTestsPassed = (
        noFilterResult.length === testData.length &&
        singleExcludeResult.length === 2 &&
        multiExcludeResult.length === 1 &&
        manualFilterResult.length === actualResult.length
    );
    
    console.log(`Overall result: ${allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
    
    if (!allTestsPassed) {
        console.log('\n🔍 DEBUGGING RECOMMENDATIONS:');
        console.log('1. Check if filterOpportunities function has been modified');
        console.log('2. Verify marketFilters.excludedCategoryIds is not being reset');
        console.log('3. Look for timing issues in initialization');
        console.log('4. Check console for any error messages during filtering');
    }
    
    return {
        passed: allTestsPassed,
        results: {
            noFilter: noFilterResult.length,
            singleExclude: singleExcludeResult.length,
            multiExclude: multiExcludeResult.length,
            manual: manualFilterResult.length,
            actual: actualResult.length
        }
    };
}

// Also add a simple quick test
function quickCategoryTest() {
    console.log('🚀 QUICK CATEGORY TEST');
    if (!window.filterOpportunities) {
        console.error('❌ filterOpportunities not available');
        return;
    }
    
    const testItem = { typeId: 1001, itemName: "Test Ship", categoryId: 6, buyPrice: 100, profit: 50, profitPercent: 50 };
    
    // Test 1: No exclusions
    window.marketFilters.excludedCategoryIds = [];
    const result1 = window.filterOpportunities([testItem]);
    console.log(`No exclusions: ${result1.length} items (expected: 1)`);
    
    // Test 2: Exclude category 6
    window.marketFilters.excludedCategoryIds = ['6'];
    const result2 = window.filterOpportunities([testItem]);
    console.log(`Exclude category 6: ${result2.length} items (expected: 0)`);
    
    console.log(`Quick test ${result1.length === 1 && result2.length === 0 ? '✅ PASSED' : '❌ FAILED'}`);
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
    window.runComprehensiveCategoryTest = runComprehensiveCategoryTest;
    window.quickCategoryTest = quickCategoryTest;
}
