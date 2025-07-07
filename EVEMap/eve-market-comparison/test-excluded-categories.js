// Integration test for excluded categories feature
// Run this in the browser console to test the functionality

console.log('🧪 Testing Excluded Categories Feature');

// 1. Test that the excluded categories array exists and is empty initially
console.log('1. Initial state:', window.marketFilters.excludedCategoryIds);

// 2. Test adding an excluded category
console.log('2. Adding category "6" (Ships) to excluded list...');
if (window.addExcludedCategory) {
    window.addExcludedCategory('6', 'Ships');
    console.log('   Excluded categories after adding:', window.marketFilters.excludedCategoryIds);
} else {
    console.error('   addExcludedCategory function not found');
}

// 3. Test persistence
console.log('3. Testing persistence...');
if (window.saveExcludedCategories) {
    window.saveExcludedCategories();
    console.log('   Saved to localStorage');
    
    // Clear and reload
    window.marketFilters.excludedCategoryIds = [];
    console.log('   Cleared in memory:', window.marketFilters.excludedCategoryIds);
    
    window.loadExcludedCategories();
    console.log('   Loaded from localStorage:', window.marketFilters.excludedCategoryIds);
} else {
    console.error('   Persistence functions not found');
}

// 4. Test UI update
console.log('4. Testing UI update...');
if (window.updateExcludedCategoriesUI) {
    window.updateExcludedCategoriesUI();
    console.log('   UI updated');
} else {
    console.error('   updateExcludedCategoriesUI function not found');
}

// 5. Test market API filtering
console.log('5. Testing market API filtering...');
console.log('   Current excluded categories will be applied to next market data fetch');
console.log('   Watch for console messages starting with "🔍" or "✅" during market operations');

// 6. Test removing excluded category
console.log('6. Testing category removal...');
if (window.removeExcludedCategory) {
    window.removeExcludedCategory('6');
    console.log('   Excluded categories after removal:', window.marketFilters.excludedCategoryIds);
} else {
    console.error('   removeExcludedCategory function not found');
}

console.log('✅ Excluded Categories Test Complete');
console.log('Next steps: Try adding categories via UI and running a market comparison');
