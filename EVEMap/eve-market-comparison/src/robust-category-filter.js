/**
 * CATEGORY FILTERING FIX
 * This file contains the definitive solution for the category filtering issue
 */

// Enhanced debugging for excluded categories
function debugExcludedCategories() {
    console.log('🔍 EXCLUDED CATEGORIES DEBUG');
    console.log('============================');
    console.log('marketFilters exists:', !!window.marketFilters);
    console.log('marketFilters.excludedCategoryIds:', window.marketFilters?.excludedCategoryIds);
    console.log('localStorage value:', localStorage.getItem('eveMarketExcludedCategories'));
    console.log('filterOpportunities exists:', !!window.filterOpportunities);
    console.log('setFilter exists:', !!window.setFilter);
}

// Robust setExcludedCategories function
function setExcludedCategories(categoryIds, skipPersistence = false) {
    console.log('🔧 ROBUST SET: Setting excluded categories to:', categoryIds);
    
    // Ensure marketFilters exists
    if (!window.marketFilters) {
        window.marketFilters = {};
    }
    
    // Validate and normalize categories
    const validCategories = Array.isArray(categoryIds) 
        ? categoryIds.filter(id => id !== null && id !== undefined).map(id => id.toString())
        : [];
    
    // Set in memory
    window.marketFilters.excludedCategoryIds = validCategories;
    
    // Persist to localStorage if requested
    if (!skipPersistence) {
        try {
            localStorage.setItem('eveMarketExcludedCategories', JSON.stringify(validCategories));
            console.log('💾 ROBUST SET: Saved to localStorage:', validCategories);
        } catch (error) {
            console.error('❌ ROBUST SET: Failed to save to localStorage:', error);
        }
    }
    
    console.log('✅ ROBUST SET: Categories set successfully:', window.marketFilters.excludedCategoryIds);
    
    // Trigger UI update if available
    if (window.updateExcludedCategoriesUI) {
        window.updateExcludedCategoriesUI();
    }
    
    return validCategories;
}

// Robust getExcludedCategories function
function getExcludedCategories() {
    // Try memory first
    if (window.marketFilters?.excludedCategoryIds) {
        return window.marketFilters.excludedCategoryIds;
    }
    
    // Try localStorage
    try {
        const stored = localStorage.getItem('eveMarketExcludedCategories');
        if (stored) {
            const parsed = JSON.parse(stored);
            return Array.isArray(parsed) ? parsed : [];
        }
    } catch (error) {
        console.warn('Failed to load excluded categories from localStorage:', error);
    }
    
    return [];
}

// Enhanced filterOpportunities that's more defensive
function robustFilterOpportunities(opportunities) {
    console.log(`🔍 ROBUST FILTER: Starting with ${opportunities.length} opportunities`);
    
    // Get excluded categories robustly
    const excludedCategories = getExcludedCategories().map(id => id.toString());
    console.log(`🔍 ROBUST FILTER: Excluded categories:`, excludedCategories);
    
    if (excludedCategories.length === 0) {
        console.log('🔍 ROBUST FILTER: No categories excluded, returning all opportunities');
        return opportunities;
    }
    
    const filtered = opportunities.filter((opp, index) => {
        // Skip items without category info
        if (!opp.categoryId) {
            console.log(`🔍 ROBUST FILTER: Item ${index} has no categoryId, keeping it`);
            return true;
        }
        
        const categoryId = opp.categoryId.toString();
        const shouldExclude = excludedCategories.includes(categoryId);
        
        if (shouldExclude) {
            console.log(`🚫 ROBUST FILTER: Excluding ${opp.itemName || opp.typeId} from category ${categoryId}`);
            return false;
        }
        
        return true;
    });
    
    console.log(`✅ ROBUST FILTER: Filtered ${opportunities.length} → ${filtered.length} opportunities`);
    return filtered;
}

// Test function to verify everything works
function testRobustCategoryFiltering() {
    console.log('🧪 TESTING ROBUST CATEGORY FILTERING');
    console.log('====================================');
    
    const testData = [
        { typeId: 1001, itemName: "Test Ship", categoryId: 6, profit: 100, profitPercent: 10 },
        { typeId: 1002, itemName: "Test Module", categoryId: 7, profit: 50, profitPercent: 5 },
        { typeId: 1003, itemName: "Test Commodity", categoryId: 43, profit: 75, profitPercent: 8 }
    ];
    
    // Test 1: No exclusions
    setExcludedCategories([]);
    const result1 = robustFilterOpportunities(testData);
    console.log(`Test 1 (no exclusions): ${result1.length}/3 ${result1.length === 3 ? '✅' : '❌'}`);
    
    // Test 2: Exclude ships
    setExcludedCategories(['6']);
    const result2 = robustFilterOpportunities(testData);
    console.log(`Test 2 (exclude ships): ${result2.length}/3 ${result2.length === 2 ? '✅' : '❌'}`);
    
    // Test 3: Exclude multiple
    setExcludedCategories(['6', '43']);
    const result3 = robustFilterOpportunities(testData);
    console.log(`Test 3 (exclude ships & commodities): ${result3.length}/3 ${result3.length === 1 ? '✅' : '❌'}`);
    
    return result1.length === 3 && result2.length === 2 && result3.length === 1;
}

// Export functions
if (typeof window !== 'undefined') {
    window.setExcludedCategories = setExcludedCategories;
    window.getExcludedCategories = getExcludedCategories;
    window.robustFilterOpportunities = robustFilterOpportunities;
    window.testRobustCategoryFiltering = testRobustCategoryFiltering;
    window.debugExcludedCategories = debugExcludedCategories;
    
    console.log('✅ Robust category filtering functions loaded');
}
