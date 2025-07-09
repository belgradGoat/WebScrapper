// Market comparison logic - enhanced version with filtering and memory optimization
// Uses global marketFilters object and IndexedDB storage

// Global state for current filter settings and market data
const marketFilters = {
    categoryId: null,
    groupId: null,
    typeIds: [],
    minPrice: null,
    maxPrice: null,
    minProfit: 100000,
    minProfitPercent: 5,
    searchQuery: '',
    savedFilterName: '',
    showMissingItems: true,
    excludedCategoryIds: [], // Initialize as empty array
    firstLocationOrderType: 'sell',
    secondLocationOrderType: 'sell'
};

// Helper function to initialize market filters
function initializeMarketFilters() {
    try {
        // Check if marketAPI exists
        if (!window.marketAPI) {
            console.warn('marketAPI not available, using default filter values');
            return;
        }

        // Load excluded categories if the method exists
        if (typeof window.marketAPI.getExcludedCategories === 'function') {
            marketFilters.excludedCategoryIds = window.marketAPI.getExcludedCategories() || [];
        }

        console.log('Market filters initialized:', marketFilters);
    } catch (error) {
        console.error('Error initializing market filters:', error);
        marketFilters.excludedCategoryIds = []; // Fallback to empty array
    }
}

// Export to window immediately
window.marketFilters = marketFilters;
window.initializeMarketFilters = initializeMarketFilters;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeMarketFilters();
});

// Function to set a filter value with proper persistence
function setFilter(filterType, value) {
    marketFilters[filterType] = value;
    
    // Handle special case for excluded categories
    if (filterType === 'excludedCategoryIds') {
        // Save to persistent storage
        window.marketAPI.saveExcludedCategories(value);
    }
    
    // Update UI
    if (window.updateFilterUI) {
        window.updateFilterUI();
    }
}

// Main compareMarkets function - optimized version
async function compareMarkets(buyLocationId, sellLocationId, forceRefetch = false) {
    const resultsDiv = document.getElementById('comparisonResults');
    try {
        if (!buyLocationId || !sellLocationId) {
            throw new Error('Please enter both market IDs');
        }

        if (marketFilters.categoryId) {
            return compareCategoryMarkets(buyLocationId, sellLocationId, marketFilters.categoryId);
        }

        console.log('Starting market comparison:', { buyLocationId, sellLocationId });
        
        resultsDiv.innerHTML = `
            <div class="loading-status">
                <h3>Loading Market Data (Memory Optimized)</h3>
                <p id="buy-location-status">Initializing buy location...</p>
                <p id="sell-location-status">Initializing sell location...</p>
                <p id="memory-status">Memory usage will be optimized using IndexedDB storage</p>
                <button id="cancel-operation-btn" class="cancel-btn">Cancel Operation</button>
            </div>
        `;

        // Clear previous data from IndexedDB to free memory
        if (window.marketStorage) {
            await window.marketStorage.clearAll();
        }

        // Use optimized market data fetching with IndexedDB storage
        const [buyMarket, sellMarket] = await Promise.all([
            fetchMarketDataOptimized(buyLocationId, 'buy-location-status'),
            fetchMarketDataOptimized(sellLocationId, 'sell-location-status')
        ]);

        if (!buyMarket || !sellMarket) {
            throw new Error('Failed to fetch market data');
        }

        // Process opportunities using IndexedDB storage
        const opportunities = await processMarketOpportunities(buyLocationId, sellLocationId);
        
        // Display results
        displayOptimizedResults(opportunities, resultsDiv);

    } catch (error) {
        console.error('Market comparison error:', error);
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>Error Processing Market Data</h3>
                <p>${error.message}</p>
                <button onclick="location.reload()" class="retry-btn">Reload Page</button>
            </div>`;
    }
}

// Category-specific market comparison with early filtering
async function compareCategoryMarkets(buyLocationId, sellLocationId, categoryId) {
    const resultsDiv = document.getElementById('comparisonResults');
    
    try {
        console.log('Comparing category markets:', { buyLocationId, sellLocationId, categoryId });
        
        resultsDiv.innerHTML = `
            <div class="loading-status">
                <h3>Loading Category Market Data</h3>
                <p>Category ID: ${categoryId}</p>
                <p id="category-status">Fetching item types for category...</p>
                <button id="cancel-operation-btn" class="cancel-btn">Cancel Operation</button>
            </div>
        `;

        // Early category exclusion check
        if (marketFilters.excludedCategoryIds.includes(parseInt(categoryId))) {
            resultsDiv.innerHTML = `
                <div class="error">
                    <h3>Category Excluded</h3>
                    <p>This category (${categoryId}) is in your excluded categories list and will not be processed.</p>
                </div>`;
            return [];
        }

        // Get item types for this category from API
        const categoryTypes = await window.marketAPI.getCategoryTypes(categoryId);
        console.log(`Found ${categoryTypes.length} types in category ${categoryId}`);

        // Update status
        const statusElement = document.getElementById('category-status');
        if (statusElement) {
            statusElement.textContent = `Found ${categoryTypes.length} item types. Fetching market data...`;
        }

        // Fetch market data for specific types only (memory optimization)
        const [buyOrders, sellOrders] = await Promise.all([
            fetchMarketOrdersForTypes(buyLocationId, categoryTypes.map(t => t.id)),
            fetchMarketOrdersForTypes(sellLocationId, categoryTypes.map(t => t.id))
        ]);

        // Process opportunities
        const opportunities = await calculateOpportunities(buyOrders, sellOrders, categoryTypes);
        
        // Filter based on current filter settings
        const filteredOpportunities = filterOpportunities(opportunities);
        
        // Display results
        displayOptimizedResults(filteredOpportunities, resultsDiv);

        return filteredOpportunities;

    } catch (error) {
        console.error('Category market comparison error:', error);
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>Error Processing Category Market Data</h3>
                <p>${error.message}</p>
            </div>`;
        return [];
    }
}

// Optimized market data fetching using IndexedDB storage
async function fetchMarketDataOptimized(locationId, statusElementId) {
    const statusElement = document.getElementById(statusElementId);
    const maxRetries = 3;
    let retryCount = 0;
    
    while (retryCount < maxRetries) {
        try {
            if (statusElement) {
                statusElement.textContent = `Fetching orders for location ${locationId}...`;
            }

            const locationInfo = getMarketIdInfo(locationId);
            if (!locationInfo) {
                throw new Error(`Invalid market location ID: ${locationId}`);
            }

            // Add delay between retries
            if (retryCount > 0) {
                await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount)));
            }

            const orders = await window.marketAPI.getMarketOrders(
                locationId, 
                locationInfo.type
            );
            
            if (statusElement) {
                statusElement.textContent = `✓ Loaded ${orders.length} orders`;
            }

            return {
                locationId: locationId,
                orders: orders,
                timestamp: Date.now()
            };

        } catch (error) {
            retryCount++;
            
            if (error.message.includes('Already fetching orders')) {
                console.log(`Location ${locationId} is being fetched, retrying... (${retryCount}/${maxRetries})`);
                continue;
            }

            if (retryCount >= maxRetries) {
                if (statusElement) {
                    statusElement.textContent = `✗ Error loading location ${locationId}: ${error.message}`;
                }
                console.error(`Error fetching market data for ${locationId}:`, error);
                throw error;
            }
        }
    }
}

// Fetch market orders for specific type IDs (for category filtering)
async function fetchMarketOrdersForTypes(locationId, typeIds) {
    const orders = [];
    const batchSize = 50; // Process in smaller batches to avoid memory issues
    
    for (let i = 0; i < typeIds.length; i += batchSize) {
        const batch = typeIds.slice(i, i + batchSize);
        
        try {
            // Fetch orders for this batch of types
            const batchOrders = await window.marketAPI.getMarketOrdersBatch(locationId, batch);
            orders.push(...batchOrders);
            
            // Add small delay to prevent overwhelming the API
            await new Promise(resolve => setTimeout(resolve, 100));
            
        } catch (error) {
            console.warn(`Error fetching batch ${i}-${i + batchSize} for location ${locationId}:`, error);
            // Continue with next batch instead of failing completely
        }
    }
    
    return orders;
}

// Process market opportunities using IndexedDB storage
async function processMarketOpportunities(buyLocationId, sellLocationId) {
    try {
        // Retrieve market data from IndexedDB storage
        const firstLocationOrders = await window.marketStorage.getMarketOrders(buyLocationId);
        const secondLocationOrders = await window.marketStorage.getMarketOrders(sellLocationId);

        if (!firstLocationOrders || !secondLocationOrders) {
            throw new Error('Market data not found in storage');
        }

        // Filter orders based on selected order types
        const filteredFirstLocationOrders = firstLocationOrders.filter(order => 
            marketFilters.firstLocationOrderType === 'buy' ? order.is_buy_order : !order.is_buy_order
        );
        
        const filteredSecondLocationOrders = secondLocationOrders.filter(order => 
            marketFilters.secondLocationOrderType === 'buy' ? order.is_buy_order : !order.is_buy_order
        );

        console.log(`Processing ${filteredFirstLocationOrders.length} first location orders and ${filteredSecondLocationOrders.length} second location orders`);

        // Calculate opportunities using the stored data
        const opportunities = await calculateOpportunities(filteredFirstLocationOrders, filteredSecondLocationOrders);
        
        // Apply category exclusion filter AFTER processing opportunities
        const filteredOpportunities = opportunities.filter(opp => {
            return !marketFilters.excludedCategoryIds.includes(opp.categoryId);
        });

        console.log(`Found ${opportunities.length} total opportunities, ${filteredOpportunities.length} after category filtering`);
        
        return filteredOpportunities;

    } catch (error) {
        console.error('Error processing market opportunities:', error);
        throw error;
    }
}

// Calculate trading opportunities from buy and sell orders
async function calculateOpportunities(buyOrders, sellOrders, itemTypes = null) {
    const opportunities = [];
    const sellOrdersByType = new Map();
    
    // Group sell orders by type ID for efficient lookup
    sellOrders.forEach(order => {
        if (!sellOrdersByType.has(order.type_id)) {
            sellOrdersByType.set(order.type_id, []);
        }
        sellOrdersByType.get(order.type_id).push(order);
    });

    // Process buy orders and find matching sell opportunities
    for (const buyOrder of buyOrders) {
        const sellOrdersForType = sellOrdersByType.get(buyOrder.type_id);
        
        if (!sellOrdersForType || sellOrdersForType.length === 0) {
            // Item not available in sell location
            if (marketFilters.showMissingItems) {
                opportunities.push({
                    typeId: buyOrder.type_id,
                    buyPrice: buyOrder.price,
                    sellPrice: null,
                    profit: null,
                    profitPercent: null,
                    buyVolume: buyOrder.volume_remain,
                    sellVolume: 0,
                    status: 'missing_in_sell_location'
                });
            }
            continue;
        }

        // Find best sell price (lowest price)
        const bestSellOrder = sellOrdersForType.reduce((best, current) => 
            current.price < best.price ? current : best
        );

        // Calculate profit
        const profit = bestSellOrder.price - buyOrder.price;
        const profitPercent = (profit / buyOrder.price) * 100;

        // Apply profit filters
        if (profit >= (marketFilters.minProfit || 0) && 
            profitPercent >= (marketFilters.minProfitPercent || 0)) {
            
            opportunities.push({
                typeId: buyOrder.type_id,
                buyPrice: buyOrder.price,
                sellPrice: bestSellOrder.price,
                profit: profit,
                profitPercent: profitPercent,
                buyVolume: buyOrder.volume_remain,
                sellVolume: bestSellOrder.volume_remain,
                status: 'profitable'
            });
        }
    }

    // If we have item types data, add item information
    if (itemTypes) {
        const typeMap = new Map(itemTypes.map(type => [type.id, type]));
        
        opportunities.forEach(opp => {
            const typeInfo = typeMap.get(opp.typeId);
            if (typeInfo) {
                opp.itemName = typeInfo.name;
                opp.groupId = typeInfo.group_id;
                opp.categoryId = typeInfo.category_id;
            }
        });
    } else {
        // Fetch item info from storage/API for display names
        await addItemInfoToOpportunities(opportunities);
    }

    return opportunities;
}

// Add item information to opportunities for display
async function addItemInfoToOpportunities(opportunities) {
    const uniqueTypeIds = [...new Set(opportunities.map(opp => opp.typeId))];
    const batchSize = 100;
    
    for (let i = 0; i < uniqueTypeIds.length; i += batchSize) {
        const batch = uniqueTypeIds.slice(i, i + batchSize);
        
        try {
            // Use the optimized getItemInfo method that uses IndexedDB storage
            const itemInfoPromises = batch.map(typeId => 
                window.marketAPI.getItemInfo(typeId).catch(error => {
                    console.warn(`Failed to get info for type ${typeId}:`, error);
                    return { name: `Item ${typeId}`, group_id: null, category_id: null };
                })
            );
            
            const itemInfoResults = await Promise.all(itemInfoPromises);
            
            // Map item info to opportunities
            batch.forEach((typeId, index) => {
                const itemInfo = itemInfoResults[index];
                opportunities.forEach(opp => {
                    if (opp.typeId === typeId) {
                        opp.itemName = itemInfo.name || `Item ${typeId}`;
                        opp.groupId = itemInfo.group_id;
                        opp.categoryId = itemInfo.category_id;
                    }
                });
            });
            
            // Add delay to prevent API rate limiting
            await new Promise(resolve => setTimeout(resolve, 200));
            
        } catch (error) {
            console.warn(`Error processing batch ${i}-${i + batchSize}:`, error);
        }
    }
}

// Filter opportunities based on current filter settings
function filterOpportunities(opportunities) {
    return opportunities.filter(opp => {
        // Category filter
        if (marketFilters.categoryId && opp.categoryId !== marketFilters.categoryId) {
            return false;
        }
        
        // Group filter
        if (marketFilters.groupId && opp.groupId !== marketFilters.groupId) {
            return false;
        }
        
        // Type IDs filter
        if (marketFilters.typeIds.length > 0 && !marketFilters.typeIds.includes(opp.typeId)) {
            return false;
        }
        
        // Price filters
        if (marketFilters.minPrice && opp.buyPrice < marketFilters.minPrice) {
            return false;
        }
        
        if (marketFilters.maxPrice && opp.buyPrice > marketFilters.maxPrice) {
            return false;
        }
        
        // Profit filters
        if (marketFilters.minProfit && opp.profit < marketFilters.minProfit) {
            return false;
        }
        
        if (marketFilters.minProfitPercent && opp.profitPercent < marketFilters.minProfitPercent) {
            return false;
        }
        
        // Search query filter
        if (marketFilters.searchQuery && opp.itemName) {
            const query = marketFilters.searchQuery.toLowerCase();
            if (!opp.itemName.toLowerCase().includes(query)) {
                return false;
            }
        }
        
        // Missing items filter
        if (!marketFilters.showMissingItems && opp.status === 'missing_in_sell_location') {
            return false;
        }
        
        // Excluded categories filter
        if (marketFilters.excludedCategoryIds.includes(opp.categoryId)) {
            return false;
        }
        
        return true;
    });
}

// Display optimized results with memory-efficient rendering
function displayOptimizedResults(opportunities, resultsDiv) {
    // Sort opportunities by profit (descending)
    opportunities.sort((a, b) => (b.profit || 0) - (a.profit || 0));
    
    // Show summary
    const profitableCount = opportunities.filter(opp => opp.profit > 0).length;
    const totalProfit = opportunities.reduce((sum, opp) => sum + (opp.profit || 0), 0);
    
    // Render results with pagination for better performance
    const pageSize = 100;
    const totalPages = Math.ceil(opportunities.length / pageSize);
    
    let currentPage = 1;
    
    const renderPage = (page) => {
        const startIdx = (page - 1) * pageSize;
        const endIdx = Math.min(startIdx + pageSize, opportunities.length);
        const pageOpportunities = opportunities.slice(startIdx, endIdx);
        
        const tableRows = pageOpportunities.map(opp => `
            <tr class="${opp.status === 'missing_in_sell_location' ? 'missing-item' : 'profitable-item'}">
                <td class="item-name">${opp.itemName || `Item ${opp.typeId}`}</td>
                <td class="price">${opp.buyPrice ? formatNumber(opp.buyPrice) : 'N/A'} ISK</td>
                <td class="price">${opp.sellPrice ? formatNumber(opp.sellPrice) : 'Not Available'}</td>
                <td class="profit ${opp.profit > 0 ? 'positive' : 'neutral'}">${opp.profit ? formatNumber(opp.profit) : 'N/A'} ISK</td>
                <td class="profit-percent ${opp.profitPercent > 0 ? 'positive' : 'neutral'}">${opp.profitPercent ? opp.profitPercent.toFixed(2) : 'N/A'}%</td>
                <td class="volume">${formatNumber(opp.buyVolume || 0)}</td>
            </tr>
        `).join('');
        
        resultsDiv.innerHTML = `
            <div class="results-summary">
                <h3>Market Comparison Results</h3>
                <div class="summary-stats">
                    <span>Total Opportunities: ${opportunities.length}</span>
                    <span>Profitable: ${profitableCount}</span>
                    <span>Total Potential Profit: ${formatNumber(totalProfit)} ISK</span>
                </div>
            </div>
            <div class="results-controls">
                <div class="pagination">
                    <button onclick="changePage(${page - 1})" ${page <= 1 ? 'disabled' : ''}>Previous</button>
                    <span>Page ${page} of ${totalPages}</span>
                    <button onclick="changePage(${page + 1})" ${page >= totalPages ? 'disabled' : ''}>Next</button>
                </div>
                <div class="export-controls">
                    <button onclick="exportResults('csv')">Export CSV</button>
                    <button onclick="clearResults()">Clear Results</button>
                </div>
            </div>
            <div class="results-table-container">
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Item Name</th>
                            <th>Buy Price</th>
                            <th>Sell Price</th>
                            <th>Profit</th>
                            <th>Profit %</th>
                            <th>Buy Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
        `;
    };
    
    // Global functions for pagination
    window.changePage = (newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            currentPage = newPage;
            renderPage(currentPage);
        }
    };
    
    window.exportResults = (format) => {
        if (format === 'csv') {
            exportToCSV(opportunities);
        }
    };
    
    window.clearResults = () => {
        if (window.marketStorage) {
            window.marketStorage.clearAll();
        }
        resultsDiv.innerHTML = '<div class="initial-message"><p>Results cleared. Enter market IDs to start a new comparison.</p></div>';
    };
    
    // Render first page
    renderPage(1);
}

// Helper function to format numbers with commas
function formatNumber(num) {
    return new Intl.NumberFormat().format(Math.round(num));
}

// Export opportunities to CSV
function exportToCSV(opportunities) {
    const csvHeader = 'Item Name,Type ID,Buy Price,Sell Price,Profit,Profit %,Buy Volume,Sell Volume,Status\n';
    const csvRows = opportunities.map(opp => [
        `"${opp.itemName || `Item ${opp.typeId}`}"`,
        opp.typeId,
        opp.buyPrice || '',
        opp.sellPrice || '',
        opp.profit || '',
        opp.profitPercent ? opp.profitPercent.toFixed(2) : '',
        opp.buyVolume || 0,
        opp.sellVolume || 0,
        opp.status || 'unknown'
    ].join(',')).join('\n');
    
    const csvContent = csvHeader + csvRows;
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `eve-market-comparison-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Helper function to get market ID info
function getMarketIdInfo(marketId) {
    // If marketAPI has the function, use it directly (no recursion)
    if (window.marketAPI && typeof window.marketAPI.getMarketIdInfo === 'function') {
        return window.marketAPI.getMarketIdInfo(marketId);
    }
    
    // Fallback basic detection (no recursion)
    const id = parseInt(marketId);
    if (isNaN(id)) {
        return null;
    }
    
    if (id >= 10000000 && id <= 10999999) return { locationId: id, type: 'region' };
    if (id >= 60000000 && id <= 69999999) return { locationId: id, type: 'station' };
    if (id >= 30000000 && id <= 39999999) return { locationId: id, type: 'solar_system' };
    if (id >= 20000000 && id <= 29999999) return { locationId: id, type: 'constellation' };
    if (id >= 1000000000) return { locationId: id, type: 'structure' };
    
    return null;
}

// Function to recalculate market comparison without fetching new data
async function recalculateMarketComparison(buyLocationId, sellLocationId) {
    const resultsDiv = document.getElementById('comparisonResults');
    try {
        resultsDiv.innerHTML = '<div class="loading-status"><h3>Recalculating opportunities...</h3></div>';
        
        // Process opportunities using existing data in storage
        const opportunities = await processMarketOpportunities(buyLocationId, sellLocationId);
        
        // Display results
        displayOptimizedResults(opportunities, resultsDiv);
    } catch (error) {
        console.error('Error recalculating market comparison:', error);
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>Error Recalculating Results</h3>
                <p>${error.message}</p>
            </div>`;
    }
}

// Export functions to global scope
window.marketFilters = marketFilters;
window.initializeMarketFilters = initializeMarketFilters;
window.setFilter = setFilter;
window.compareMarkets = compareMarkets;
window.compareCategoryMarkets = compareCategoryMarkets;
window.getMarketIdInfo = getMarketIdInfo;
window.recalculateMarketComparison = recalculateMarketComparison;

// Inside processMarketComparison function, modify the comparison logic:
async function processMarketComparison(buyLocationOrders, sellLocationOrders) {
    try {
        const buyLocationByType = groupOrdersByType(buyLocationOrders);
        const sellLocationByType = groupOrdersByType(sellLocationOrders);

        for (const typeId of batch) {
            try {
                const firstLocationData = buyLocationByType[typeId] || { buyOrders: [], sellOrders: [] };
                const secondLocationData = sellLocationByType[typeId] || { buyOrders: [], sellOrders: [] };

                // Get orders based on user selection
                const firstLocationOrders = marketFilters.firstLocationOrderType === 'buy' 
                    ? firstLocationData.buyOrders 
                    : firstLocationData.sellOrders;
                
                const secondLocationOrders = marketFilters.secondLocationOrderType === 'buy' 
                    ? secondLocationData.buyOrders 
                    : secondLocationData.sellOrders;

                // Filter and sort orders
                const firstLocationFilteredOrders = firstLocationOrders
                    .filter(order => order.price && !isNaN(order.price))
                    .sort((a, b) => marketFilters.firstLocationOrderType === 'buy' 
                        ? b.price - a.price  // Highest first for buy orders
                        : a.price - b.price  // Lowest first for sell orders
                    );

                const secondLocationFilteredOrders = secondLocationOrders
                    .filter(order => order.price && !isNaN(order.price))
                    .sort((a, b) => marketFilters.secondLocationOrderType === 'buy' 
                        ? b.price - a.price  // Highest first for buy orders
                        : a.price - b.price  // Lowest first for sell orders
                    );

                if (!firstLocationFilteredOrders.length) continue;

                const firstPrice = firstLocationFilteredOrders[0].price;

                if (!secondLocationFilteredOrders.length) {
                    if (marketFilters.showMissingItems) {
                        opportunities.push({
                            typeId,
                            firstPrice,
                            secondPrice: null,
                            profit: null,
                            profitPercent: null,
                            firstVolume: firstLocationFilteredOrders.reduce((sum, order) => 
                                sum + (order.volume_remain || 0), 0),
                            secondVolume: 0,
                            isMissingInSecondLocation: true,
                            firstOrderType: marketFilters.firstLocationOrderType,
                            secondOrderType: marketFilters.secondLocationOrderType
                        });
                    }
                    continue;
                }

                const secondPrice = secondLocationFilteredOrders[0].price;
                const profit = secondPrice - firstPrice;
                const profitPercent = (profit / firstPrice) * 100;

                if (profit > 0 && profit >= marketFilters.minProfit && 
                    profitPercent >= marketFilters.minProfitPercent) {
                    opportunities.push({
                        typeId,
                        firstPrice,
                        secondPrice,
                        profit,
                        profitPercent,
                        firstVolume: firstLocationFilteredOrders.reduce((sum, order) => 
                            sum + (order.volume_remain || 0), 0),
                        secondVolume: secondLocationFilteredOrders.reduce((sum, order) => 
                            sum + (order.volume_remain || 0), 0),
                        firstOrderType: marketFilters.firstLocationOrderType,
                        secondOrderType: marketFilters.secondOrderOrderType
                    });
                }
            } catch (itemError) {
                console.error(`Error processing item ${typeId}:`, itemError);
            }
        }
    } catch (error) {
        console.error('Error in processMarketComparison:', error);
        throw error;
    }
}

// Add event listeners for the order type selectors
document.addEventListener('DOMContentLoaded', () => {
    const firstLocationOrderType = document.getElementById('firstLocationOrderType');
    const secondLocationOrderType = document.getElementById('secondLocationOrderType');

    firstLocationOrderType.addEventListener('change', (e) => {
        console.log('First Location Order Type Changed:', e.target.value);
        setFilter('firstLocationOrderType', e.target.value);
        
        // Get the market IDs
        const buyLocationInput = document.getElementById('buyLocationInput');
        const sellLocationInput = document.getElementById('sellLocationInput');
        if (buyLocationInput && sellLocationInput && window.marketStorage) {
            recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
        }
    });

    secondLocationOrderType.addEventListener('change', (e) => {
        console.log('Second Location Order Type Changed:', e.target.value);
        setFilter('secondLocationOrderType', e.target.value);
        
        // Get the market IDs
        const buyLocationInput = document.getElementById('buyLocationInput');
        const sellLocationInput = document.getElementById('sellLocationInput');
        if (buyLocationInput && sellLocationInput && window.marketStorage) {
            recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
        }
    });

    // Debug logging for initial state
    console.log('Initial First Location Order Type:', firstLocationOrderType.value);
    console.log('Initial Second Location Order Type:', secondLocationOrderType.value);
});
