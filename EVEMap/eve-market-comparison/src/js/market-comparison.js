// Market comparison logic - enhanced version with filtering

// Global state for current filter settings and market data
const marketFilters = {
    categoryId: null,
    groupId: null,
    typeIds: [],
    minPrice: null,
    maxPrice: null,
    minProfit: 100000, // Default 100k ISK minimum profit
    minProfitPercent: 5, // Default 5% minimum profit percentage
    searchQuery: '',
    savedFilterName: '',
    showMissingItems: true, // Default to showing items missing in sell location
    excludedCategoryIds: [] // Categories to exclude from searches and downloads
};


async function compareMarkets(buyLocationId, sellLocationId, forceRefetch = false) {
    console.log('compareMarkets called with:', {buyLocationId, sellLocationId, forceRefetch});
    
    try {
        const resultsDiv = document.getElementById('comparisonResults');
        if (!resultsDiv) {
            console.error('comparisonResults element not found!');
            alert('Error: Could not find results container');
            return;
        }
        
        resultsDiv.innerHTML = `
            <div class="loading-status">
                <h3>Loading Market Data</h3>
                <p id="buy-location-status">Initializing buy location...</p>
                <p id="sell-location-status">Initializing sell location...</p>
                <button id="cancel-operation-btn" class="cancel-btn">Cancel Operation</button>
            </div>
            <div class="results-grid-container">
                <div class="partial-results-notice">Displaying partial results while analysis continues...</div>
                <table class="results-grid" id="live-results">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Buy Price</th>
                            <th>Sell Price</th>
                            <th>Profit</th>
                            <th>Profit %</th>
                        </tr>
                    </thead>
                    <tbody id="results-body">
                        <!-- Live results will appear here -->
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error in initial compareMarkets setup:', error);
        alert('Error setting up comparison: ' + error.message);
        return;
    }
    
    // Add event listener for cancel button
    const cancelBtn = document.getElementById('cancel-operation-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            window.cancelOperation = true;
            cancelBtn.textContent = 'Cancelling...';
            cancelBtn.disabled = true;
        });
    }
    
    // Reset cancel flag
    window.cancelOperation = false;

    try {
        console.log('=== MARKET COMPARISON START ===');
        console.log('Buy Location ID:', buyLocationId);
        console.log('Sell Location ID:', sellLocationId);
        console.log('Current Category Filter:', marketFilters.categoryId || 'None');
        
        // Check if marketAPI is initialized
        if (!window.marketAPI) {
            console.error('marketAPI is not initialized!');
            resultsDiv.innerHTML = `<div class="error"><h3>Error</h3><p>Market API is not initialized. Please refresh the page and try again.</p></div>`;
            return;
        }

        // Validate inputs
        if (!buyLocationId || !sellLocationId) {
            throw new Error('Please enter both market IDs');
        }

        if (marketFilters.categoryId) {
            return compareCategoryMarkets(buyLocationId, sellLocationId, marketFilters.categoryId);
        }

        // Determine market types using auto-detection
        const buyLocationInfo = getMarketIdInfo(buyLocationId);
        const sellLocationInfo = getMarketIdInfo(sellLocationId);

        console.log('Market 1 Info:', buyLocationInfo);
        console.log('Market 2 Info:', sellLocationInfo);

        // Check authentication for both market locations
        const privateMarketTypes = ['structure', 'corporation', 'alliance'];
        const buyLocationRequiresAuth = privateMarketTypes.includes(buyLocationInfo.type);
        const sellLocationRequiresAuth = privateMarketTypes.includes(sellLocationInfo.type);

        // Require authentication if either market is a private type
        if (buyLocationRequiresAuth || sellLocationRequiresAuth) {
            const token = localStorage.getItem('eveAccessToken');
            if (!token) {
                resultsDiv.innerHTML = `
                    <div class="error">
                        <h3>Login Required</h3>
                        <p>You need to log in with EVE Online to access ${buyLocationRequiresAuth ? 'Buy Location' : 'Sell Location'} market data.</p>
                        <button onclick="redirectToLogin()" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Login Now
                        </button>
                    </div>`;
                return;
            }
        }

        let buyLocationOrders, sellLocationOrders;
        const isSameMarket = window.lastMarketComparisonParams && window.lastMarketComparisonParams[0] === buyLocationId && window.lastMarketComparisonParams[1] === sellLocationId;
        const lastExcludedCategories = window.lastMarketComparisonParams && window.lastMarketComparisonParams[2] ? window.lastMarketComparisonParams[2] : [];
        const currentExcludedCategories = marketFilters.excludedCategoryIds || [];
        const excludedCategoriesChanged = JSON.stringify(lastExcludedCategories.sort()) !== JSON.stringify(currentExcludedCategories.sort());

        if (!forceRefetch && isSameMarket && !excludedCategoriesChanged) {
            buyLocationOrders = window.lastPublicMarketOrders;
            sellLocationOrders = window.lastPrivateMarketOrders;
            console.log('Using cached market data.');
        } else {
            [buyLocationOrders, sellLocationOrders] = await Promise.all([
                window.marketAPI.getMarketOrders(buyLocationInfo.locationId, buyLocationInfo.type, { statusElementId: 'buy-location-status' }),
                window.marketAPI.getMarketOrders(sellLocationInfo.locationId, sellLocationInfo.type, { statusElementId: 'sell-location-status' })
            ]);
            
            window.lastPublicMarketOrders = buyLocationOrders;
            window.lastPrivateMarketOrders = sellLocationOrders;
            window.lastMarketComparisonParams = [buyLocationId, sellLocationId, [...currentExcludedCategories]];
        }

        console.log('Market data available:', {
            buyLocation: buyLocationOrders.length,
            sellLocation: sellLocationOrders.length
        });

        const comparison = await processMarketComparison(buyLocationOrders, sellLocationOrders);

        if (!comparison || comparison.length === 0) {
            const categoryFilterText = marketFilters.categoryId
                ? `Category ID: ${marketFilters.categoryId}`
                : 'No category filter applied';

            resultsDiv.innerHTML = `
                <div class="info">
                    <h3>No Profitable Opportunities Found</h3>
                    <p>No profitable opportunities found between:</p>
                    <ul>
                        <li><strong>Buy Location:</strong> ${buyLocationInfo.type} ${buyLocationId}</li>
                        <li><strong>Sell Location:</strong> ${sellLocationInfo.type} ${sellLocationId}</li>
                    </ul>
                    <p><strong>Current filters:</strong></p>
                    <ul>
                        <li>Minimum profit: ${window.marketFilters.minProfit.toLocaleString()} ISK</li>
                        <li>Minimum profit %: ${window.marketFilters.minProfitPercent}%</li>
                        <li>${categoryFilterText}</li>
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

async function processMarketComparison(buyLocationOrders, sellLocationOrders) {
    try {
        console.log('Processing market comparison...');

        // Initialize results container
        const resultsDiv = document.getElementById('comparisonResults');
        resultsDiv.innerHTML = `
            <div class="processing-status">
                <h3>Processing Market Data</h3>
                <div class="progress-container">
                    <div class="progress-bar" id="comparison-progress" style="width: 0%"></div>
                </div>
                <p id="comparison-status">Analyzing market data...</p>
            </div>
            <div class="results-grid-container">
                <table class="results-grid" id="live-results">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Buy Price</th>
                            <th>Sell Price</th>
                            <th>Profit</th>
                            <th>Profit %</th>
                        </tr>
                    </thead>
                    <tbody id="results-body"></tbody>
                </table>
            </div>`;

        // Group orders by type_id
        const buyLocationByType = groupOrdersByType(buyLocationOrders);
        const sellLocationByType = groupOrdersByType(sellLocationOrders);

        const comparison = [];
        const allTypeIds = new Set([...Object.keys(buyLocationByType), ...Object.keys(sellLocationByType)]);
        const allTypeIdsArray = Array.from(allTypeIds);
        const totalItems = allTypeIdsArray.length;
        const statusElement = document.getElementById('comparison-status');
        const progressBar = document.getElementById('comparison-progress');
        
        // Process in batches for smoother UI updates
        const batchSize = 100;
        for (let i = 0; i < totalItems; i += batchSize) {
            // Check if operation was cancelled
            if (window.cancelOperation) {
                console.log('Market comparison operation cancelled by user');
                return [];
            }
            
            // Update progress
            const progress = Math.round((i / totalItems) * 100);
            if (progressBar) progressBar.style.width = `${progress}%`;
            if (statusElement) statusElement.textContent = `Analyzing market data... ${i}/${totalItems} items (${progress}%)`;
            
            // Process a batch of items
            const batch = allTypeIdsArray.slice(i, i + batchSize);
            for (const typeId of batch) {
                try {
                    const buyLocationData = buyLocationByType[typeId] || { buyOrders: [], sellOrders: [] };
                    const sellLocationData = sellLocationByType[typeId] || { buyOrders: [], sellOrders: [] };

                    // Filter and sort orders
                    buyLocationData.sellOrders = buyLocationData.sellOrders.filter(order => 
                        order && typeof order === 'object' && 'price' in order && typeof order.price === 'number' && !isNaN(order.price)
                    );
                    
                    sellLocationData.sellOrders = sellLocationData.sellOrders.filter(order => 
                        order && typeof order === 'object' && 'price' in order && typeof order.price === 'number' && !isNaN(order.price)
                    );
                    
                    buyLocationData.sellOrders.sort((a, b) => a.price - b.price);
                    sellLocationData.sellOrders.sort((a, b) => a.price - b.price);

                    // Skip if no sell orders at buy location
                    if (!buyLocationData.sellOrders.length) {
                        continue;
                    }

                    const buyPrice = buyLocationData.sellOrders[0].price;
                    
                    // Check if this item is not available in the sell location
                    if (!sellLocationData.sellOrders.length) {
                        if (marketFilters.showMissingItems) {
                            const opportunity = {
                                typeId,
                                buyPrice,
                                sellPrice: null,
                                profit: null,
                                profitPercent: null,
                                buyVolume: buyLocationData.sellOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0),
                                sellVolume: 0,
                                isMissingInSellLocation: true
                            };
                            comparison.push(opportunity);
                        }
                        continue;
                    }

                    // Calculate profit using sell orders in sell location
                    const sellPrice = sellLocationData.sellOrders[0].price;
                    const profit = sellPrice - buyPrice;
                    const profitPercent = buyPrice > 0 ? (profit / buyPrice) * 100 : 0;

                    if (profit > 0 && profit >= marketFilters.minProfit && profitPercent >= marketFilters.minProfitPercent) {
                        const opportunity = {
                            typeId,
                            buyPrice,
                            sellPrice,
                            profit,
                            profitPercent,
                            buyVolume: buyLocationData.sellOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0),
                            sellVolume: sellLocationData.sellOrders.reduce((sum, order) => sum + (order.volume_remain || 0), 0),
                        };
                        comparison.push(opportunity);
                    }
                } catch (itemError) {
                    console.error(`Error processing item ${typeId}:`, itemError);
                }
            }
            
            // Allow UI to update
            await new Promise(resolve => setTimeout(resolve, 0));
        }

        // Final progress update
        if (progressBar) progressBar.style.width = '100%';
        if (statusElement) statusElement.textContent = `Found ${comparison.length} opportunities. Getting item details...`;
        
        // Sort by highest profit
        comparison.sort((a, b) => b.profit - a.profit);
        
        // Get item names for top results only (limit to 100 to save memory)
        const topResults = comparison.slice(0, 100);
        
        if (topResults.length === 0) {
            console.log('No profitable opportunities found');
            return [];
        }
        
        // NOW apply excluded category filtering - only fetch item info for opportunities
        if (statusElement) statusElement.textContent = `Getting item details for ${topResults.length} opportunities...`;
        
        const filteredResults = [];
        const excludedCategoryIds = marketFilters.excludedCategoryIds || [];
        
        // Process in small batches to avoid memory issues
        const itemBatchSize = 20;
        for (let i = 0; i < topResults.length; i += itemBatchSize) {
            const batch = topResults.slice(i, i + itemBatchSize);
            
            const itemInfoPromises = batch.map(async (opp) => {
                try {
                    const info = await window.marketAPI.getItemInfo(opp.typeId);
                    
                    // Check if this item belongs to an excluded category
                    if (excludedCategoryIds.length > 0 && info.category_id && excludedCategoryIds.includes(info.category_id.toString())) {
                        console.log(`Excluding ${info.name} (category ${info.category_id})`);
                        return null; // Exclude this item
                    }
                    
                    opp.itemName = info.name;
                    opp.groupId = info.group_id;
                    opp.categoryId = info.category_id;
                    opp.volume = info.volume;
                    opp.description = info.description;
                    return opp;
                } catch (error) {
                    console.warn(`Error getting item info for ${opp.typeId}:`, error);
                    opp.itemName = `Item ${opp.typeId}`;
                    opp.description = 'Item information could not be retrieved';
                    return opp;
                }
            });
            
            const batchResults = await Promise.all(itemInfoPromises);
            filteredResults.push(...batchResults.filter(result => result !== null));
            
            // Rate limiting between batches
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        console.log(`Final results after excluded category filtering: ${filteredResults.length}`);
        return filteredResults;
        
    } catch (error) {
        console.error('Error in processMarketComparison:', error);
        throw error;
    }
}

// Helper function to update the live results table
function updateLiveResults(items, progressInfo = null) {
    const tbody = document.getElementById('results-body');
    if (!tbody) return;
    
    // Update progress notification if provided
    if (progressInfo) {
        const notice = document.querySelector('.partial-results-notice');
        if (notice) {
            if (progressInfo.inProgress) {
                const percent = Math.round((progressInfo.currentItem / progressInfo.totalItems) * 100);
                notice.innerHTML = `
                    <div class="progress-info">
                        <span>Analyzing markets: ${percent}% complete (${progressInfo.currentItem}/${progressInfo.totalItems} items)</span>
                        <div class="mini-progress-bar">
                            <div class="mini-progress-fill" style="width: ${percent}%"></div>
                        </div>
                    </div>
                    <p>Displaying top ${items.length} profitable items found so far...</p>
                `;
                notice.classList.add('active');
            } else {
                notice.innerHTML = `Analysis complete. Showing ${items.length} most profitable items.`;
                notice.classList.remove('active');
            }
        }
    }
    
    tbody.innerHTML = '';
    
    items.forEach(item => {
        const row = document.createElement('tr');
        
        // Highlight rows with unknown items
        const isUnknownItem = !item.itemName || item.itemName.includes('Unknown Item') || item.itemName.includes(`Item ${item.typeId}`);
        if (isUnknownItem) {
            row.className = 'unknown-item-row';
        }
        
        row.innerHTML = `
            <td>
                <div class="item-name ${isUnknownItem ? 'unknown-item' : ''}">
                    ${item.itemName || `Unknown Item (${item.typeId})`}
                    ${isUnknownItem ? `
                        <button class="refresh-item-btn" data-type-id="${item.typeId}" title="Attempt to refresh item information">
                            🔄
                        </button>
                    ` : ''}
                </div>
            </td>
            <td>${item.buyPrice.toLocaleString()} ISK</td>
            <td>${item.sellPrice.toLocaleString()} ISK</td>
            <td>${item.profit.toLocaleString()} ISK</td>
            <td>${item.profitPercent.toFixed(2)}%</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Add event listeners to the refresh buttons
    const refreshButtons = tbody.querySelectorAll('.refresh-item-btn');
    refreshButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.stopPropagation();
            const typeId = this.getAttribute('data-type-id');
            this.textContent = '⏳';
            this.disabled = true;
            
            try {
                // Clear the cache for this item
                window.marketAPI.clearItemCache(typeId);
                // Try to get updated item info
                const updatedInfo = await window.marketAPI.getItemInfo(typeId);
                
                // Update the display
                const nameElement = this.parentElement;
                if (updatedInfo && updatedInfo.name && updatedInfo.name !== `Unknown Item (${typeId})` && updatedInfo.name !== `Item ${typeId}`) {
                    nameElement.innerHTML = updatedInfo.name;
                    nameElement.classList.remove('unknown-item');
                    this.parentElement.parentElement.parentElement.classList.remove('unknown-item-row');
                } else {
                    this.textContent = '🔄';
                    this.disabled = false;
                }
            } catch (error) {
                console.error(`Failed to refresh item ${typeId}:`, error);
                this.textContent = '❌';
                setTimeout(() => {
                    this.textContent = '🔄';
                    this.disabled = false;
                }, 2000);
            }
        });
    });
}

// Helper function to update the list of items that exist in buy location but not in sell location
function updateMissingItemsList(items) {
    // Remove existing missing items section if it exists
    const existingSection = document.getElementById('missing-items-section');
    if (existingSection) {
        existingSection.remove();
    }
    
    if (!items || items.length === 0) {
        return; // No items to display
    }
    
    // Filter out items from excluded categories
    const excludedCategoryIds = marketFilters.excludedCategoryIds || [];
    items = items.filter(item => 
        !item.categoryId || !excludedCategoryIds.includes(item.categoryId.toString())
    );
    
    // If no items left after filtering, return
    if (items.length === 0) {
        return;
    }
    
    const resultsDiv = document.getElementById('comparisonResults');
    if (!resultsDiv) return;
    
    // Create a new section for missing items
    const section = document.createElement('div');
    section.id = 'missing-items-section';
    section.className = 'missing-items-section';
    section.innerHTML = `
        <div class="missing-items-header">
            <h3>Items Available Only in Buy Location (${items.length})</h3>
            <div class="toggle-container">
                <input type="checkbox" id="showMissingItemsToggle" class="toggle-checkbox" ${window.marketFilters.showMissingItems ? 'checked' : ''}>
                <label for="showMissingItemsToggle" class="toggle-label">Show Missing Items</label>
            </div>
        </div>
        <p class="info-text">These items are available for purchase in the first location but have no sell orders in the second location. They could be potential market opportunities.</p>
        <table class="results-grid" id="missing-items-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Buy Price</th>
                    <th>Available Volume</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="missing-items-body">
                <!-- Missing items will appear here -->
            </tbody>
        </table>
    `;
    
    // Insert at the beginning of the results div
    resultsDiv.insertBefore(section, resultsDiv.firstChild);
    
    // Add event listener for the toggle
    const toggle = document.getElementById('showMissingItemsToggle');
    if (toggle) {
        toggle.addEventListener('change', () => {
            window.setFilter('showMissingItems', toggle.checked);
        });
    }
    
    // Update the table with items
    const tbody = document.getElementById('missing-items-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    // Sort by name by default, but can be modified to sort by price or volume
    items.sort((a, b) => {
        if (a.itemName && b.itemName) {
            return a.itemName.localeCompare(b.itemName);
        }
        return 0;
    });
    
    items.forEach(item => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td class="item-cell">
                <div class="item-name">${item.itemName || `Item ${item.typeId}`}</div>
                <div class="item-category">${item.categoryId || ''}</div>
            </td>
            <td>${item.buyPrice.toLocaleString()} ISK</td>
            <td>
                <div class="volume-info">${item.buyVolume.toLocaleString()}</div>
                <div class="volume-note">${item.buyVolume > 100 ? 'High supply' : item.buyVolume > 10 ? 'Medium supply' : 'Low supply'}</div>
            </td>
            <td>
                <button class="opportunity-btn" data-type-id="${item.typeId}" data-price="${item.buyPrice}" data-name="${item.itemName || `Item ${item.typeId`}">
                    Market Details
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Add event listeners to the buttons
    const buttons = tbody.querySelectorAll('.opportunity-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const typeId = this.dataset.typeId;
            const buyPrice = parseFloat(this.dataset.price);
            const itemName = this.dataset.name;
            
            // Create a modal with more detailed information
            const modal = document.createElement('div');
            modal.className = 'market-detail-modal';
            modal.innerHTML = `
                <div class="market-detail-content">
                    <div class="market-detail-header">
                        <h3>Market Opportunity: ${itemName}</h3>
                        <span class="close-modal">&times;</span>
                    </div>
                    <div class="market-detail-body">
                        <p>This item is available for purchase at <strong>${buyPrice.toLocaleString()} ISK</strong> in the buy location.</p>
                        <p>There are currently no sell orders for this item in the sell location, which could represent a potential market opportunity.</p>
                        
                        <h4>Potential Strategies:</h4>
                        <ul>
                            <li><strong>New Market Entry:</strong> Be the first to sell this item in the destination.</li>
                            <li><strong>Price Assessment:</strong> Research typical margins for this item in other markets.</li>
                            <li><strong>Volume Consideration:</strong> Check if the available volume justifies transportation.</li>
                        </ul>
                        
                        <div class="market-actions">
                            <button class="action-btn copy-btn" data-type-id="${typeId}">Copy Item ID</button>
                            <button class="action-btn close-btn">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to the page
            document.body.appendChild(modal);
            
            // Add event listeners for modal buttons
            const closeBtn = modal.querySelector('.close-modal');
            const closeBtnAction = modal.querySelector('.close-btn');
            const copyBtn = modal.querySelector('.copy-btn');
            
            closeBtn.addEventListener('click', () => modal.remove());
            closeBtnAction.addEventListener('click', () => modal.remove());
            copyBtn.addEventListener('click', function() {
                const typeId = this.dataset.typeId;
                navigator.clipboard.writeText(typeId).then(() => {
                    this.textContent = 'Copied!';
                    setTimeout(() => {
                        this.textContent = 'Copy Item ID';
                    }, 2000);
                });
            });
            
            // Close modal when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.remove();
            });
        });
    });
}

window.updateMissingItemsList = updateMissingItemsList;

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

// Helper function to initialize market filters
function initializeMarketFilters() {
    // Load excluded categories from storage
    marketFilters.excludedCategoryIds = window.marketAPI.getExcludedCategories();
}

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

// Helper function to get market ID info
function getMarketIdInfo(marketId) {
    if (window.marketAPI && window.marketAPI.getMarketIdInfo) {
        return window.marketAPI.getMarketIdInfo(marketId);
    }
    
    // Fallback basic detection
    const id = parseInt(marketId);
    if (id >= 10000000 && id <= 10999999) return { locationId: id, type: 'region' };
    if (id >= 60000000 && id <= 69999999) return { locationId: id, type: 'station' };
    if (id >= 30000000 && id <= 39999999) return { locationId: id, type: 'solar_system' };
    if (id >= 20000000 && id <= 29999999) return { locationId: id, type: 'constellation' };
    return { locationId: id, type: 'structure' };
}

// Export functions to global scope
window.marketFilters = marketFilters;
window.initializeMarketFilters = initializeMarketFilters;
window.setFilter = setFilter;
window.compareMarkets = compareMarkets;
window.getMarketIdInfo = getMarketIdInfo;

async function compareCategoryMarkets(buyLocationId, sellLocationId, categoryId) {
    const resultsDiv = document.getElementById('comparisonResults');
    
    // First, check if the category is excluded
    const excludedCategoryIds = window.marketFilters.excludedCategoryIds || [];
    if (excludedCategoryIds.includes(categoryId?.toString())) {
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>Category Excluded</h3>
                <p>This category is in your excluded categories list. Remove it from the excluded list to analyze it.</p>
            </div>`;
        return;
    }
    
    resultsDiv.innerHTML = `
        <div class="loading">
            <h3>Processing Market Data</h3>
            <div class="progress-container">
                <div class="progress-bar" id="category-progress" style="width: 0%"></div>
            </div>
            <p id="category-status">Starting analysis...</p>
        </div>`;

    const statusElement = document.getElementById('category-status');
    const progressBar = document.getElementById('category-progress');

    try {
        if (!buyLocationId || !sellLocationId || !categoryId) {
            throw new Error('Missing required parameters');
        }

        // Get market location info
        const buyLocationInfo = getMarketIdInfo(buyLocationId);
        const sellLocationInfo = getMarketIdInfo(sellLocationId);

        statusElement.textContent = 'Getting all items in category...';

        // Get all item types in the category
        const groups = await window.marketAPI.getGroupsInCategory(categoryId);
        if (!groups || groups.length === 0) {
            throw new Error(`No item groups found in category ${categoryId}`);
        }

        // Get all type IDs first, filtering by excluded categories
        const allTypeIds = [];
        let processedGroups = 0;
        const excludedCategoryIds = window.marketFilters.excludedCategoryIds || [];

        for (const group of groups) {
            try {
                const groupItems = await window.marketAPI.searchItemsByGroup(group.group_id);
                if (groupItems?.length) {
                    allTypeIds.push(...groupItems.map(item => item.type_id));
                }

                processedGroups++;
                const progress = Math.round((processedGroups / groups.length) * 40);
                progressBar.style.width = `${progress}%`;
                statusElement.textContent = `Found ${allTypeIds.length} items in ${processedGroups} groups...`;
                
                await new Promise(resolve => setTimeout(resolve, 0));
            } catch (error) {
                console.warn(`Error processing group ${group.group_id}:`, error);
            }
        }

        if (allTypeIds.length === 0) {
            throw new Error(`No items found in category ${categoryId}`);
        }

        // Process market data in smaller batches with rate limiting
        const batchSize = 50;
        const batches = [];
        for (let i = 0; i < allTypeIds.length; i += batchSize) {
            batches.push(allTypeIds.slice(i, i + batchSize));
        }

        let opportunities = [];
        let processedBatches = 0;

        for (const batch of batches) {
            try {
                const buyOrders = await window.marketAPI.getMarketOrders(
                    buyLocationId,
                    'market',
                    { typeIds: batch }
                );

                const sellOrders = await window.marketAPI.getMarketOrders(
                    sellLocationId,
                    'market',
                    { typeIds: batch }
                );

                // Process orders for this batch without fetching item info yet
                for (const typeId of batch) {                const buyLocationData = buyOrders.find(order => order.type_id === typeId);
                const sellLocationData = sellOrders.find(order => order.type_id === typeId);

                // Skip if item doesn't meet our basic criteria
                if (!buyLocationData?.sellOrders?.length) continue;

                // For items missing in sell location
                if (!sellLocationData?.sellOrders?.length) {
                    opportunities.push({
                        typeId,
                        buyPrice: buyLocationData.sellOrders[0].price,
                        sellPrice: null,
                        profit: null,
                        profitPercent: null,
                        buyVolume: buyLocationData.sellOrders.reduce((sum, order) => sum + order.volume_remain, 0),
                        sellVolume: 0,
                        isMissingInSellLocation: true
                    });
                    continue;
                }

                // For regular opportunities, apply price filters early
                const buyPrice = buyLocationData.sellOrders[0].price;
                const sellPrice = sellLocationData.buyOrders[0]?.price;
                
                if (!sellPrice) continue;

                const profit = sellPrice - buyPrice;
                const profitPercent = (profit / buyPrice) * 100;

                // Apply price and profit filters
                if (marketFilters.minPrice && buyPrice < marketFilters.minPrice) continue;
                if (marketFilters.maxPrice && buyPrice > marketFilters.maxPrice) continue;
                if (marketFilters.minProfit && profit < marketFilters.minProfit) continue;
                if (marketFilters.minProfitPercent && profitPercent < marketFilters.minProfitPercent) continue;

                opportunities.push({
                    typeId,
                    buyPrice,
                    sellPrice,
                    profit,
                    profitPercent,
                    buyVolume: buyLocationData.sellOrders.reduce((sum, order) => sum + order.volume_remain, 0),
                    sellVolume: sellLocationData.buyOrders.reduce((sum, order) => sum + order.volume_remain, 0)
                });
                }

                processedBatches++;
                const progress = 40 + Math.round((processedBatches / batches.length) * 60);
                progressBar.style.width = `${progress}%`;
                statusElement.textContent = `Processed ${processedBatches}/${batches.length} batches... Found ${opportunities.length} items`;

                await new Promise(resolve => setTimeout(resolve, 1000)); // Rate limiting

            } catch (batchError) {
                console.error(`Batch processing error:`, batchError);
            }
        }

        // After all market data is processed, fetch item info only for the opportunities we found
        if (opportunities.length > 0) {
            statusElement.textContent = 'Fetching item details...';
            
            // Get unique type IDs from opportunities
            const uniqueTypeIds = [...new Set(opportunities.map(opp => opp.typeId))];
            
            // Fetch item info in smaller batches
            const itemBatchSize = 20;
            const itemInfoMap = new Map();
            
            for (let i = 0; i < uniqueTypeIds.length; i += itemBatchSize) {
                const itemBatch = uniqueTypeIds.slice(i, i + itemBatchSize);
                const itemInfoPromises = itemBatch.map(typeId => 
                    window.marketAPI.getItemInfo(typeId)
                        .catch(() => ({ type_id: typeId, name: `Item ${typeId}` }))
                );
                
                const itemInfos = await Promise.all(itemInfoPromises);
                itemInfos.forEach(info => itemInfoMap.set(info.type_id, info));
                
                // Rate limiting
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            // Add item info to opportunities
            opportunities = opportunities.map(opp => ({
                ...opp,
                itemName: itemInfoMap.get(opp.typeId)?.name || `Item ${opp.typeId}`,
                description: itemInfoMap.get(opp.typeId)?.description || '',
                groupId: itemInfoMap.get(opp.typeId)?.group_id,
                categoryId: itemInfoMap.get(opp.typeId)?.category_id,
            }));
        }

        // Sort opportunities
        opportunities.sort((a, b) => b.buyVolume - a.buyVolume);

        return opportunities;

    } catch (error) {
        console.error('Market comparison error:', error);
        resultsDiv.innerHTML = `
            <div class="error">
                <h3>Error Processing Market Data</h3>
                <p>${error.message}</p>
            </div>`;
        return [];
    }
}

// Helper function to initialize market filters
function initializeMarketFilters() {
    // Load excluded categories from storage
    marketFilters.excludedCategoryIds = window.marketAPI.getExcludedCategories();
}

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

// Helper function to get market ID info
function getMarketIdInfo(marketId) {
    if (window.marketAPI && window.marketAPI.getMarketIdInfo) {
        return window.marketAPI.getMarketIdInfo(marketId);
    }
    
    // Fallback basic detection
    const id = parseInt(marketId);
    if (id >= 10000000 && id <= 10999999) return { locationId: id, type: 'region' };
    if (id >= 60000000 && id <= 69999999) return { locationId: id, type: 'station' };
    if (id >= 30000000 && id <= 39999999) return { locationId: id, type: 'solar_system' };
    if (id >= 20000000 && id <= 29999999) return { locationId: id, type: 'constellation' };
    return { locationId: id, type: 'structure' };
}

// Export functions to global scope
window.marketFilters = marketFilters;
window.initializeMarketFilters = initializeMarketFilters;
window.setFilter = setFilter;
window.compareMarkets = compareMarkets;
window.getMarketIdInfo = getMarketIdInfo;