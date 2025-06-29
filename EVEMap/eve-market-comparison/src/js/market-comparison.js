// Market comparison logic - clean version

async function compareMarkets(publicMarketId, privateStructureId) {
    const resultsDiv = document.getElementById('comparisonResults');
    resultsDiv.innerHTML = '<div class="loading">Loading market data...</div>';
    
    try {
        // Validate inputs
        if (!publicMarketId || !privateStructureId) {
            throw new Error('Please enter both market IDs');
        }

        // Fetch both markets
        const [publicOrders, privateOrders] = await Promise.all([
            window.marketAPI.getPublicMarketOrders(publicMarketId),
            window.marketAPI.getPrivateStructureMarket(privateStructureId)
        ]);
        
        // Process and compare
        const comparison = await processMarketComparison(publicOrders, privateOrders);
        window.displayComparisonResults(comparison);
        
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        console.error('Market comparison error:', error);
    }
}

async function processMarketComparison(publicOrders, privateOrders) {
    // Group orders by type_id
    const publicByType = groupOrdersByType(publicOrders);
    const privateByType = groupOrdersByType(privateOrders);
    
    const comparison = [];
    const allTypeIds = new Set([...Object.keys(publicByType), ...Object.keys(privateByType)]);
    
    // Find profitable opportunities
    for (const typeId of allTypeIds) {
        const publicData = publicByType[typeId] || { buyOrders: [], sellOrders: [] };
        const privateData = privateByType[typeId] || { buyOrders: [], sellOrders: [] };
        
        const opportunity = {
            typeId,
            publicBuyMax: publicData.buyOrders[0]?.price || 0,
            publicSellMin: publicData.sellOrders[0]?.price || Infinity,
            privateBuyMax: privateData.buyOrders[0]?.price || 0,
            privateSellMin: privateData.sellOrders[0]?.price || Infinity
        };
        
        // Calculate profit margins
        opportunity.buyFromPublicProfit = opportunity.privateBuyMax - opportunity.publicSellMin;
        opportunity.buyFromPrivateProfit = opportunity.publicBuyMax - opportunity.privateSellMin;
        
        if (opportunity.buyFromPublicProfit > 0 || opportunity.buyFromPrivateProfit > 0) {
            comparison.push(opportunity);
        }
    }
    
    // Sort by highest profit
    comparison.sort((a, b) => 
        Math.max(b.buyFromPublicProfit, b.buyFromPrivateProfit) - 
        Math.max(a.buyFromPublicProfit, a.buyFromPrivateProfit)
    );
    
    // Get item names for top results
    const topResults = comparison.slice(0, 50);
    for (const opp of topResults) {
        try {
            const itemInfo = await window.marketAPI.getItemInfo(opp.typeId);
            opp.itemName = itemInfo.name;
        } catch (e) {
            opp.itemName = `Unknown Item (${opp.typeId})`;
        }
    }
    
    return topResults;
}

function groupOrdersByType(orders) {
    const grouped = {};
    
    orders.forEach(order => {
        if (!grouped[order.type_id]) {
            grouped[order.type_id] = {
                buyOrders: [],
                sellOrders: []
            };
        }
        
        if (order.is_buy_order) {
            grouped[order.type_id].buyOrders.push(order);
        } else {
            grouped[order.type_id].sellOrders.push(order);
        }
    });
    
    // Sort orders by price
    Object.values(grouped).forEach(data => {
        data.buyOrders.sort((a, b) => b.price - a.price); // Highest first
        data.sellOrders.sort((a, b) => a.price - b.price); // Lowest first
    });
    
    return grouped;
}

// Make compareMarkets available globally
window.compareMarkets = compareMarkets;