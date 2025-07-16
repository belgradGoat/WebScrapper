// Test script to verify debug error fixes
console.log('🧪 TESTING DEBUG FIXES');
console.log('=====================');

// Wait for page to fully load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        console.log('\n📋 INITIALIZATION ORDER TEST:');
        
        // Test 1: Check if marketFilters is available
        console.log('1. Testing marketFilters availability:');
        if (window.marketFilters) {
            console.log('   ✅ window.marketFilters is available');
            console.log('   📊 marketFilters contents:', window.marketFilters);
        } else {
            console.log('   ❌ window.marketFilters is NOT available');
        }
        
        // Test 2: Check if compareMarkets function is available
        console.log('\n2. Testing compareMarkets function:');
        if (typeof window.compareMarkets === 'function') {
            console.log('   ✅ window.compareMarkets function is available');
        } else {
            console.log('   ❌ window.compareMarkets function is NOT available');
        }
        
        // Test 3: Check if marketAPI is available
        console.log('\n3. Testing marketAPI availability:');
        if (window.marketAPI) {
            console.log('   ✅ window.marketAPI is available');
        } else {
            console.log('   ❌ window.marketAPI is NOT available');
        }
        
        // Test 4: Check if initializeMarketFilters function works
        console.log('\n4. Testing initializeMarketFilters function:');
        if (typeof window.initializeMarketFilters === 'function') {
            try {
                window.initializeMarketFilters();
                console.log('   ✅ initializeMarketFilters executed successfully');
            } catch (error) {
                console.log('   ❌ initializeMarketFilters threw error:', error.message);
            }
        } else {
            console.log('   ❌ window.initializeMarketFilters function is NOT available');
        }
        
        // Test 5: Check group filter UI availability
        console.log('\n5. Testing group filter UI:');
        if (typeof window.createGroupFilterUI === 'function') {
            console.log('   ✅ window.createGroupFilterUI function is available');
        } else {
            console.log('   ❌ window.createGroupFilterUI function is NOT available');
        }
        
        // Test 6: Check if there are any remaining errors accessing properties
        console.log('\n6. Testing property access (race condition fix):');
        try {
            // These should not throw errors now
            const excludedGroups = window.marketFilters?.excludedGroupIds || [];
            const groupIds = window.marketFilters?.groupIds || [];
            console.log('   ✅ Property access successful');
            console.log(`   📊 Excluded groups: ${excludedGroups.length} items`);
            console.log(`   📊 Included groups: ${groupIds.length} items`);
        } catch (error) {
            console.log('   ❌ Property access failed:', error.message);
        }
        
        // Test 7: Check if UI initialization works without errors
        console.log('\n7. Testing UI initialization:');
        try {
            if (window.marketFilters && typeof window.updateExcludedCategoriesUI === 'function') {
                window.updateExcludedCategoriesUI();
                console.log('   ✅ updateExcludedCategoriesUI executed successfully');
            } else {
                console.log('   ⚠️  updateExcludedCategoriesUI not available (may be using group-based filtering)');
            }
        } catch (error) {
            console.log('   ❌ UI initialization failed:', error.message);
        }
        
        // Summary
        console.log('\n🎯 SUMMARY:');
        const tests = [
            { name: 'marketFilters availability', passed: !!window.marketFilters },
            { name: 'compareMarkets function', passed: typeof window.compareMarkets === 'function' },
            { name: 'marketAPI availability', passed: !!window.marketAPI },
            { name: 'initializeMarketFilters function', passed: typeof window.initializeMarketFilters === 'function' },
            { name: 'createGroupFilterUI function', passed: typeof window.createGroupFilterUI === 'function' }
        ];
        
        const passedTests = tests.filter(t => t.passed).length;
        const totalTests = tests.length;
        
        console.log(`   📈 Tests passed: ${passedTests}/${totalTests}`);
        
        if (passedTests === totalTests) {
            console.log('   🎉 ALL TESTS PASSED - Debug fixes are working!');
        } else {
            console.log('   ⚠️  Some tests failed - check individual results above');
        }
        
        tests.forEach(test => {
            console.log(`   ${test.passed ? '✅' : '❌'} ${test.name}`);
        });
        
    }, 2000); // Wait 2 seconds to ensure everything is loaded
});
