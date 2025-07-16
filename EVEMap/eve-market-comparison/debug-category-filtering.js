/**
 * Debug script to isolate category filtering issues
 * This script will test the filterOpportunities function directly
 */

async function debugCategoryFiltering() {
    console.log('🔍 DEBUGGING CATEGORY FILTERING');
    console.log('===============================');
    
    // Test data with known category IDs
    const testOpportunities = [
        {
            typeId: 1001,
            itemName: "Test Item 1",
            categoryId: 6, // Ships category
            buyPrice: 100,
            sellPrice: 150,
            profit: 50,
            profitPercent: 50
        },
        {
            typeId: 1002,
            itemName: "Test Item 2", 
            categoryId: 7, // Modules category
            buyPrice: 200,
            sellPrice: 250,
            profit: 50,
            profitPercent: 25
        },
        {
            typeId: 1003,
            itemName: "Test Item 3",
            categoryId: 6, // Ships category (should be excluded)
            buyPrice: 300,
            sellPrice: 400,
            profit: 100,
            profitPercent: 33.33
        }
    ];
    
    console.log('📊 Test data:', testOpportunities);
    
    // Test 1: No filters (should return all items)
    console.log('\n🧪 Test 1: No filters');
    window.marketFilters = {
        excludedCategoryIds: [],
        minPrice: null,
        maxPrice: null,
        minProfit: null,
        minProfitPercent: null
    };
    
    const noFilterResult = window.filterOpportunities(testOpportunities);
    console.log('Result (should be 3 items):', noFilterResult.length);
    console.log('Items:', noFilterResult.map(o => `${o.itemName} (cat: ${o.categoryId})`));
    
    // Test 2: Exclude category 6 (Ships)
    console.log('\n🧪 Test 2: Exclude category 6 (Ships)');
    window.marketFilters.excludedCategoryIds = ['6'];
    console.log('Excluded categories:', window.marketFilters.excludedCategoryIds);
    
    const excludedResult = window.filterOpportunities(testOpportunities);
    console.log('Result (should be 1 item - only category 7):', excludedResult.length);
    console.log('Items:', excludedResult.map(o => `${o.itemName} (cat: ${o.categoryId})`));
    
    // Test 3: Exclude category 6 and apply price filter
    console.log('\n🧪 Test 3: Exclude category 6 AND minimum price 150');
    window.marketFilters.minPrice = 150;
    
    const combinedResult = window.filterOpportunities(testOpportunities);
    console.log('Result (should be 1 item - category 7 with price >= 150):', combinedResult.length);
    console.log('Items:', combinedResult.map(o => `${o.itemName} (cat: ${o.categoryId}, price: ${o.buyPrice})`));
    
    // Test 4: Test with number vs string category IDs
    console.log('\n🧪 Test 4: Category ID type conversion test');
    const mixedData = [
        { typeId: 2001, itemName: "Numeric Cat", categoryId: 6, buyPrice: 100, sellPrice: 150, profit: 50, profitPercent: 50 },
        { typeId: 2002, itemName: "String Cat", categoryId: "6", buyPrice: 100, sellPrice: 150, profit: 50, profitPercent: 50 },
        { typeId: 2003, itemName: "Other Cat", categoryId: 7, buyPrice: 100, sellPrice: 150, profit: 50, profitPercent: 50 }
    ];
    
    window.marketFilters = { excludedCategoryIds: ['6'] };
    const typeResult = window.filterOpportunities(mixedData);
    console.log('Result (should exclude both numeric and string cat 6):', typeResult.length);
    console.log('Items:', typeResult.map(o => `${o.itemName} (cat: ${o.categoryId}, type: ${typeof o.categoryId})`));
    
    // Test 5: Check actual filtering logic step by step
    console.log('\n🧪 Test 5: Step-by-step filtering logic');
    const stepByStepData = [{
        typeId: 3001,
        itemName: "Debug Item",
        categoryId: 6,
        buyPrice: 100,
        sellPrice: 150,
        profit: 50,
        profitPercent: 50
    }];
    
    window.marketFilters = { excludedCategoryIds: ['6'] };
    
    // Manually check the filtering condition
    const testOpp = stepByStepData[0];
    const excludedCategories = (window.marketFilters.excludedCategoryIds || []).map(id => id.toString());
    
    console.log('Test opportunity:', testOpp);
    console.log('Excluded categories array:', excludedCategories);
    console.log('Opportunity categoryId:', testOpp.categoryId, '(type:', typeof testOpp.categoryId, ')');
    console.log('Opportunity categoryId as string:', testOpp.categoryId.toString());
    console.log('Is excluded?', excludedCategories.includes(testOpp.categoryId.toString()));
    
    // Test the actual filter function
    const stepResult = window.filterOpportunities(stepByStepData);
    console.log('Filter result:', stepResult.length, '(should be 0 if excluding works)');
    
    console.log('\n✅ Category filtering debug complete');
}

// Auto-run when loaded
if (typeof window !== 'undefined') {
    window.debugCategoryFiltering = debugCategoryFiltering;
    
    // Wait for the main scripts to load, then run debug
    setTimeout(() => {
        if (window.filterOpportunities && window.marketFilters) {
            debugCategoryFiltering();
        } else {
            console.error('❌ Required functions not available. Make sure market-comparison-optimized.js is loaded.');
        }
    }, 1000);
}
