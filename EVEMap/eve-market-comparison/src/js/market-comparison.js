// Market comparison logic - enhanced version with filtering

// Global state for current filter settings
const marketFilters = {
    categoryId: null,
    groupId: null,
    typeIds: [],
    minPrice: null,
    maxPrice: null,
    minProfit: 100000, // Default 100k ISK minimum profit
    minProfitPercent: 5, // Default 5% minimum profit percentage
    searchQuery: '',
    savedFilterName: ''
};

function getMarketIdInfo(marketId) {
    const id = marketId.toString();
    
    if (id.startsWith('600')) {
        // Station ID - need to convert to region
        const stationToRegion = {
            '60003760': '10000002', // Jita 4-4 -> The Forge
            '60008494': '10000043', // Amarr VIII -> Domain
            '60011866': '10000032', // Dodixie IX -> Sinq Laison
            '60004588': '10000042', // Rens VI -> Metropolis
            '60005686': '10000030'  // Hek VIII -> Heimatar
        };
        
        return {
            type: 'station',
            stationId: marketId,
            regionId: stationToRegion[marketId] || '10000002', // Default to The Forge
            usePublicAPI: true
        };
    } else if (id.startsWith('100000')) {
        // Region ID
        return {
            type: 'region',
            regionId: marketId,
            usePublicAPI: true
        };
    } else if (id.startsWith('10')) {
        // Structure ID
        return {
            type: 'structure',
            structureId: marketId,
            usePublicAPI: false
        };
    } else {
        throw new Error(`Unknown market ID format: ${marketId}`);
    }
}

async function compareMarkets(publicMarketId, privateMarketId) {
    const resultsDiv = document.getElementById('comparisonResults');
    resultsDiv.innerHTML = '<div class="loading">Loading market data...</div>';
    
    try {
        console.log('=== MARKET COMPARISON START ===');
        console.log('Market 1 ID:', publicMarketId);
        console.log('Market 2 ID:', privateMarketId);
        
        // Validate inputs
        if (!publicMarketId || !privateMarketId) {
            throw new Error('Please enter both market IDs');
        }

        // Determine market types
        const market1Info = getMarketIdInfo(publicMarketId);
        const market2Info = getMarketIdInfo(privateMarketId);
        
        console.log('Market 1 Info:', market1Info);
        console.log('Market 2 Info:', market2Info);
        
        // Check if we need authentication for structures
        if (!market1Info.usePublicAPI || !market2Info.usePublicAPI) {
            const token = localStorage.getItem('eveAccessToken');
            if (!token) {
                resultsDiv.innerHTML = `
                    <div class="error">
                        <h3>Login Required</h3>
                        <p>You need to log in with EVE Online to access structure market data.</p>
                        <button onclick="redirectToLogin()" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Login Now
                        </button>
                    </div>`;
                return;
            }
        }
        
        // Fetch market data using appropriate endpoints
        const [market1Orders, market2Orders] = await Promise.all([
            market1Info.usePublicAPI 
                ? window.marketAPI.getPublicMarketOrders(market1Info.regionId)
                : window.marketAPI.getPrivateStructureMarket(market1Info.structureId),
            market2Info.usePublicAPI 
                ? window.marketAPI.getPublicMarketOrders(market2Info.regionId)
                : window.marketAPI.getPrivateStructureMarket(market2Info.structureId)
        ]);
        
        console.log('Market data fetched:', {
            market1: market1Orders.length,
            market2: market2Orders.length
        });
        
        // If comparing station vs region, filter station orders to that specific station
        let filteredMarket1Orders = market1Orders;
        let filteredMarket2Orders = market2Orders;
        
        if (market1Info.type === 'station') {
            filteredMarket1Orders = market1Orders.filter(order => 
                order.location_id.toString() === market1Info.stationId
            );
            console.log(`Filtered market 1 to station ${market1Info.stationId}: ${filteredMarket1Orders.length} orders`);
        }
        
        if (market2Info.type === 'station') {
            filteredMarket2Orders = market2Orders.filter(order => 
                order.location_id.toString() === market2Info.stationId
            );
            console.log(`Filtered market 2 to station ${market2Info.stationId}: ${filteredMarket2Orders.length} orders`);
        }
        
        // Continue with comparison
        const comparison = await processMarketComparison(filteredMarket1Orders, filteredMarket2Orders);
        
        if (!comparison || comparison.length === 0) {
            resultsDiv.innerHTML = `
                <div class="info">
                    <h3>No Profitable Opportunities Found</h3>
                    <p>No profitable opportunities found between:</p>
                    <ul>
                        <li><strong>Market 1:</strong> ${market1Info.type} ${publicMarketId}</li>
                        <li><strong>Market 2:</strong> ${market2Info.type} ${privateMarketId}</li>
                    </ul>
                    <p><strong>Orders found:</strong></p>
                    <ul>
                        <li>Market 1: ${filteredMarket1Orders.length} orders</li>
                        <li>Market 2: ${filteredMarket2Orders.length} orders</li>
                    </ul>
                    <p><strong>Current filters:</strong></p>
                    <ul>
                        <li>Minimum profit: ${window.marketFilters.minProfit.toLocaleString()} ISK</li>
                        <li>Minimum profit %: ${window.marketFilters.minProfitPercent}%</li>
                    </ul>
                </div>`;
            return;
        }
        
        window.displayComparisonResults(comparison);
        
    } catch (error) {
        console.error('Market comparison error:', error);
        resultsDiv.innerHTML = `<div class="error"><h3>Error</h3><p>${error.message}</p></div>`;
    }
}

async function processMarketComparison(publicOrders, privateOrders) {
    try {
        console.log('Processing market comparison...');
        console.log('Public orders:', publicOrders ? publicOrders.length : 0);
        console.log('Private orders:', privateOrders ? privateOrders.length : 0);
        
        // Validate inputs
        if (!Array.isArray(publicOrders)) {
            console.error('Public orders is not an array:', publicOrders);
            publicOrders = [];
        }
        
        if (!Array.isArray(privateOrders)) {
            console.error('Private orders is not an array:', privateOrders);
            privateOrders = [];
        }
        
        // Group orders by type_id
        const publicByType = groupOrdersByType(publicOrders);
        const privateByType = groupOrdersByType(privateOrders);
        
        console.log('Public order types:', Object.keys(publicByType).length);
        console.log('Private order types:', Object.keys(privateByType).length);
        
        const comparison = [];
        const allTypeIds = new Set([...Object.keys(publicByType), ...Object.keys(privateByType)]);
        console.log('Total unique type IDs:', allTypeIds.size);
        
        // Find profitable opportunities
        for (const typeId of allTypeIds) {
            try {
                const publicData = publicByType[typeId] || { buyOrders: [], sellOrders: [] };
                const privateData = privateByType[typeId] || { buyOrders: [], sellOrders: [] };
                
                const opportunity = {
                    typeId,
                    publicBuyMax: publicData.buyOrders[0]?.price || 0,
                    publicSellMin: publicData.sellOrders[0]?.price || Infinity,
                    privateBuyMax: privateData.buyOrders[0]?.price || 0,
                    privateSellMin: privateData.sellOrders[0]?.price || Infinity,
                    publicBuyVolume: publicData.buyOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0),
                    publicSellVolume: publicData.sellOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0),
                    privateBuyVolume: privateData.buyOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0),
                    privateSellVolume: privateData.sellOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0)
                };
                
                // Calculate profit margins for arbitrage and station trading
                opportunity.buyFromPublicProfit = opportunity.privateBuyMax - opportunity.publicSellMin;
                opportunity.buyFromPrivateProfit = opportunity.publicBuyMax - opportunity.privateSellMin;
                opportunity.stationTradePublicProfit = opportunity.publicBuyMax - opportunity.publicSellMin;
                opportunity.stationTradePrivateProfit = opportunity.privateBuyMax - opportunity.privateSellMin;

                // Calculate profit percentages
                opportunity.buyFromPublicProfitPercent = opportunity.publicSellMin > 0
                    ? (opportunity.buyFromPublicProfit / opportunity.publicSellMin) * 100
                    : 0;
                opportunity.buyFromPrivateProfitPercent = opportunity.privateSellMin > 0
                    ? (opportunity.buyFromPrivateProfit / opportunity.privateSellMin) * 100
                    : 0;
                opportunity.stationTradePublicProfitPercent = opportunity.publicSellMin > 0
                    ? (opportunity.stationTradePublicProfit / opportunity.publicSellMin) * 100
                    : 0;
                opportunity.stationTradePrivateProfitPercent = opportunity.privateSellMin > 0
                    ? (opportunity.stationTradePrivateProfit / opportunity.privateSellMin) * 100
                    : 0;

                // Apply profit filters (now includes station trading)
                const meetsMinProfit = (
                    (opportunity.buyFromPublicProfit >= marketFilters.minProfit &&
                     opportunity.buyFromPublicProfitPercent >= marketFilters.minProfitPercent) ||
                    (opportunity.buyFromPrivateProfit >= marketFilters.minProfit &&
                     opportunity.buyFromPrivateProfitPercent >= marketFilters.minProfitPercent) ||
                    (opportunity.stationTradePublicProfit >= marketFilters.minProfit &&
                     opportunity.stationTradePublicProfitPercent >= marketFilters.minProfitPercent) ||
                    (opportunity.stationTradePrivateProfit >= marketFilters.minProfit &&
                     opportunity.stationTradePrivateProfitPercent >= marketFilters.minProfitPercent)
                );
                
                if (meetsMinProfit) {
                    comparison.push(opportunity);
                }
            } catch (itemError) {
                console.error(`Error processing item ${typeId}:`, itemError);
                // Continue with next item
            }
        }
        
        console.log('Profitable opportunities found:', comparison.length);
        
        // Sort by highest profit
        comparison.sort((a, b) =>
            Math.max(b.buyFromPublicProfit || 0, b.buyFromPrivateProfit || 0) -
            Math.max(a.buyFromPublicProfit || 0, a.buyFromPrivateProfit || 0)
        );
        
        // Get item names and additional info for top results
        const topResults = comparison.slice(0, 100); // Increased from 50 to 100
        console.log('Getting item info for top results:', topResults.length);
        
        if (topResults.length === 0) {
            console.log('No profitable opportunities found that meet the criteria');
            return [];
        }
        
        const itemInfoPromises = topResults.map(opp =>
            window.marketAPI.getItemInfo(opp.typeId)
                .then(info => {
                    opp.itemName = info.name;
                    opp.groupId = info.group_id;
                    opp.categoryId = info.category_id;
                    opp.volume = info.volume;
                    opp.description = info.description;
                    return opp;
                })
                .catch((error) => {
                    console.error(`Error getting item info for ${opp.typeId}:`, error);
                    opp.itemName = `Unknown Item (${opp.typeId})`;
                    return opp;
                })
        );
        
        await Promise.all(itemInfoPromises);
        console.log('Item info fetched for all opportunities');
        
        return topResults;
    } catch (error) {
        console.error('Error in processMarketComparison:', error);
        throw new Error(`Failed to process market comparison: ${error.message}`);
    }
}

function groupOrdersByType(orders) {
    try {
        console.log('Grouping orders by type...');
        
        if (!Array.isArray(orders)) {
            console.error('Orders is not an array:', orders);
            return {};
        }
        
        if (orders.length === 0) {
            console.log('No orders to group');
            return {};
        }
        
        const grouped = {};
        
        orders.forEach(order => {
            try {
                if (!order || typeof order !== 'object') {
                    console.error('Invalid order object:', order);
                    return; // Skip this order
                }
                
                const typeId = order.type_id;
                if (!typeId) {
                    console.error('Order missing type_id:', order);
                    return; // Skip this order
                }
                
                if (!grouped[typeId]) {
                    grouped[typeId] = {
                        buyOrders: [],
                        sellOrders: []
                    };
                }
                
                if (order.is_buy_order) {
                    grouped[typeId].buyOrders.push(order);
                } else {
                    grouped[typeId].sellOrders.push(order);
                }
            } catch (orderError) {
                console.error('Error processing order:', orderError, order);
                // Continue with next order
            }
        });
        
        // Sort orders by price
        Object.values(grouped).forEach(data => {
            try {
                data.buyOrders.sort((a, b) => (b.price || 0) - (a.price || 0)); // Highest first
                data.sellOrders.sort((a, b) => (a.price || 0) - (b.price || 0)); // Lowest first
            } catch (sortError) {
                console.error('Error sorting orders:', sortError);
                // Leave unsorted if there's an error
            }
        });
        
        console.log('Grouped orders by type, total types:', Object.keys(grouped).length);
        return grouped;
    } catch (error) {
        console.error('Error in groupOrdersByType:', error);
        return {}; // Return empty object on error
    }
}

// Filter management functions
function setFilter(filterType, value) {
    marketFilters[filterType] = value;
    
    // Update UI to reflect the change
    updateFilterUI();
}

function resetFilters() {
    // Reset to defaults
    marketFilters.categoryId = null;
    marketFilters.groupId = null;
    marketFilters.typeIds = [];
    marketFilters.minPrice = null;
    marketFilters.maxPrice = null;
    marketFilters.minProfit = 100000;
    marketFilters.minProfitPercent = 5;
    marketFilters.searchQuery = '';
    marketFilters.savedFilterName = '';
    
    // Update UI
    updateFilterUI();
}

function saveCurrentFilter(name) {
    if (!name) {
        name = `Filter ${new Date().toLocaleString()}`;
    }
    
    const filterData = { ...marketFilters, timestamp: Date.now() };
    window.marketAPI.saveFilterToLocalStorage(name, filterData);
    
    // Update saved filter name
    marketFilters.savedFilterName = name;
    
    // Update UI
    updateSavedFiltersUI();
}

function loadSavedFilter(name) {
    const filters = window.marketAPI.getFiltersFromLocalStorage();
    const filter = filters[name];
    
    if (filter) {
        // Apply the filter settings
        Object.assign(marketFilters, filter);
        marketFilters.savedFilterName = name;
        
        // Update UI
        updateFilterUI();
    }
}

function deleteSavedFilter(name) {
    window.marketAPI.deleteFilterFromLocalStorage(name);
    
    // If current filter is the deleted one, reset name
    if (marketFilters.savedFilterName === name) {
        marketFilters.savedFilterName = '';
    }
    
    // Update UI
    updateSavedFiltersUI();
}

// UI update functions
function updateFilterUI() {
    // This will be implemented in market-ui.js
    if (window.updateFilterUIDisplay) {
        window.updateFilterUIDisplay(marketFilters);
    }
}

function updateSavedFiltersUI() {
    // This will be implemented in market-ui.js
    if (window.updateSavedFiltersDisplay) {
        const filters = window.marketAPI.getFiltersFromLocalStorage();
        window.updateSavedFiltersDisplay(filters);
    }
}

// Make functions available globally
window.compareMarkets = compareMarkets;
window.marketFilters = marketFilters;
window.setFilter = setFilter;
window.resetFilters = resetFilters;
window.saveCurrentFilter = saveCurrentFilter;
window.loadSavedFilter = loadSavedFilter;
window.deleteSavedFilter = deleteSavedFilter;