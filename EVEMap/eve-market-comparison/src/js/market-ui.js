// Enhanced UI display functions with advanced filtering

// Initialize UI components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeFilterUI();
    initializeResultsUI();
    
    // Check login status
    const token = localStorage.getItem('eveAccessToken');
    if (token) {
        updateUIForLoggedInUser();
    }
});

// Create and initialize the filter UI
function initializeFilterUI() {
    // Create filter panel container if it doesn't exist
    if (!document.getElementById('filterPanel')) {
        const marketComparison = document.getElementById('marketComparison');
        const inputGroup = document.querySelector('.input-group');
        
        if (marketComparison && inputGroup) {
            // Create filter panel
            const filterPanel = document.createElement('div');
            filterPanel.id = 'filterPanel';
            filterPanel.className = 'filter-panel';
            
            // Insert filter panel after input group
            inputGroup.parentNode.insertBefore(filterPanel, inputGroup.nextSibling);
            
            // Build filter UI
            buildFilterUI(filterPanel);
        }
    }
    
    // Load saved filters
    updateSavedFiltersDisplay(window.marketAPI.getFiltersFromLocalStorage());
}

// Build the complete filter UI
function buildFilterUI(container) {
    container.innerHTML = `
        <div class="filter-header">
            <h3>Advanced Filters</h3>
            <button id="toggleFiltersBtn" class="toggle-btn">▼</button>
        </div>
        
        <div class="filter-content">
            <div class="filter-section">
                <h4>Categories</h4>
                <div class="filter-row">
                    <select id="categorySelect" class="filter-select">
                        <option value="">Select Category...</option>
                        <!-- Categories will be loaded dynamically -->
                    </select>
                    
                    <select id="groupSelect" class="filter-select" disabled>
                        <option value="">Select Group...</option>
                        <!-- Groups will be loaded dynamically -->
                    </select>
                </div>
                
                <div class="filter-row">
                    <input type="text" id="itemSearch" class="filter-input" placeholder="Search items...">
                    <button id="searchItemsBtn" class="filter-btn">Search</button>
                </div>
                
                <div id="selectedItems" class="selected-items">
                    <!-- Selected items will appear here -->
                </div>
            </div>
            
            <div class="filter-section">
                <h4>Price Filters</h4>
                <div class="filter-row">
                    <label>Min Price:</label>
                    <input type="number" id="minPriceInput" class="filter-input" placeholder="Min Price">
                    
                    <label>Max Price:</label>
                    <input type="number" id="maxPriceInput" class="filter-input" placeholder="Max Price">
                </div>
                
                <div class="filter-row">
                    <label>Min Profit:</label>
                    <input type="number" id="minProfitInput" class="filter-input" value="100000">
                    
                    <label>Min Profit %:</label>
                    <input type="number" id="minProfitPercentInput" class="filter-input" value="5">
                </div>
            </div>
            
            <div class="filter-section">
                <h4>Saved Filters</h4>
                <div class="filter-row">
                    <input type="text" id="filterNameInput" class="filter-input" placeholder="Filter name">
                    <button id="saveFilterBtn" class="filter-btn">Save</button>
                </div>
                
                <div class="filter-row">
                    <select id="savedFiltersSelect" class="filter-select">
                        <option value="">Select Saved Filter...</option>
                        <!-- Saved filters will be loaded dynamically -->
                    </select>
                    <button id="loadFilterBtn" class="filter-btn">Load</button>
                    <button id="deleteFilterBtn" class="filter-btn delete-btn">Delete</button>
                </div>
            </div>
            
            <div class="filter-actions">
                <button id="applyFiltersBtn" class="filter-btn primary-btn">Apply Filters</button>
                <button id="resetFiltersBtn" class="filter-btn">Reset</button>
            </div>
        </div>
    `;
    
    // Add event listeners
    setupFilterEventListeners();
    
    // Load categories
    loadCategories();
}

// Set up event listeners for filter UI
function setupFilterEventListeners() {
    // Toggle filter panel
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const content = document.querySelector('.filter-content');
            if (content) {
                content.classList.toggle('collapsed');
                toggleBtn.textContent = content.classList.contains('collapsed') ? '▲' : '▼';
            }
        });
    }
    
    // Category selection
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect) {
        categorySelect.addEventListener('change', async () => {
            const categoryId = categorySelect.value;
            if (categoryId) {
                await loadGroups(categoryId);
                setFilter('categoryId', categoryId);
                
                // Enable group select
                const groupSelect = document.getElementById('groupSelect');
                if (groupSelect) {
                    groupSelect.disabled = false;
                }
            } else {
                setFilter('categoryId', null);
                
                // Disable and reset group select
                const groupSelect = document.getElementById('groupSelect');
                if (groupSelect) {
                    groupSelect.disabled = true;
                    groupSelect.innerHTML = '<option value="">Select Group...</option>';
                }
            }
        });
    }
    
    // Group selection
    const groupSelect = document.getElementById('groupSelect');
    if (groupSelect) {
        groupSelect.addEventListener('change', () => {
            const groupId = groupSelect.value;
            setFilter('groupId', groupId ? groupId : null);
        });
    }
    
    // Item search
    const searchBtn = document.getElementById('searchItemsBtn');
    const searchInput = document.getElementById('itemSearch');
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => searchItems());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchItems();
            }
        });
    }
    
    // Price filters
    const minPriceInput = document.getElementById('minPriceInput');
    const maxPriceInput = document.getElementById('maxPriceInput');
    const minProfitInput = document.getElementById('minProfitInput');
    const minProfitPercentInput = document.getElementById('minProfitPercentInput');
    
    if (minPriceInput) {
        minPriceInput.addEventListener('change', () => {
            setFilter('minPrice', minPriceInput.value ? parseFloat(minPriceInput.value) : null);
        });
    }
    
    if (maxPriceInput) {
        maxPriceInput.addEventListener('change', () => {
            setFilter('maxPrice', maxPriceInput.value ? parseFloat(maxPriceInput.value) : null);
        });
    }
    
    if (minProfitInput) {
        minProfitInput.addEventListener('change', () => {
            setFilter('minProfit', minProfitInput.value ? parseFloat(minProfitInput.value) : 100000);
        });
    }
    
    if (minProfitPercentInput) {
        minProfitPercentInput.addEventListener('change', () => {
            setFilter('minProfitPercent', minProfitPercentInput.value ? parseFloat(minProfitPercentInput.value) : 5);
        });
    }
    
    // Saved filters
    const saveFilterBtn = document.getElementById('saveFilterBtn');
    const filterNameInput = document.getElementById('filterNameInput');
    if (saveFilterBtn && filterNameInput) {
        saveFilterBtn.addEventListener('click', () => {
            saveCurrentFilter(filterNameInput.value);
        });
    }
    
    const loadFilterBtn = document.getElementById('loadFilterBtn');
    const savedFiltersSelect = document.getElementById('savedFiltersSelect');
    if (loadFilterBtn && savedFiltersSelect) {
        loadFilterBtn.addEventListener('click', () => {
            if (savedFiltersSelect.value) {
                loadSavedFilter(savedFiltersSelect.value);
            }
        });
    }
    
    const deleteFilterBtn = document.getElementById('deleteFilterBtn');
    if (deleteFilterBtn && savedFiltersSelect) {
        deleteFilterBtn.addEventListener('click', () => {
            if (savedFiltersSelect.value) {
                if (confirm(`Delete filter "${savedFiltersSelect.value}"?`)) {
                    deleteSavedFilter(savedFiltersSelect.value);
                }
            }
        });
    }
    
    // Apply and reset filters
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            const publicMarketId = document.getElementById('publicMarketInput').value;
            const privateMarketId = document.getElementById('privateMarketInput').value;
            compareMarkets(publicMarketId, privateMarketId);
        });
    }
    
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', () => {
            resetFilters();
        });
    }
}

// Load categories from API
async function loadCategories() {
    try {
        const categories = await window.marketAPI.getCategories();
        const categorySelect = document.getElementById('categorySelect');
        
        if (categorySelect && categories) {
            // Sort categories by name
            categories.sort((a, b) => a.name.localeCompare(b.name));
            
            // Add options
            let options = '<option value="">Select Category...</option>';
            categories.forEach(category => {
                options += `<option value="${category.category_id}">${category.name}</option>`;
            });
            
            categorySelect.innerHTML = options;
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load groups for a category
async function loadGroups(categoryId) {
    try {
        const groups = await window.marketAPI.getGroupsInCategory(categoryId);
        const groupSelect = document.getElementById('groupSelect');
        
        if (groupSelect && groups) {
            // Sort groups by name
            groups.sort((a, b) => a.name.localeCompare(b.name));
            
            // Add options
            let options = '<option value="">All Groups</option>';
            groups.forEach(group => {
                options += `<option value="${group.group_id}">${group.name}</option>`;
            });
            
            groupSelect.innerHTML = options;
        }
    } catch (error) {
        console.error('Failed to load groups:', error);
    }
}

// Search for items
async function searchItems() {
    const searchInput = document.getElementById('itemSearch');
    const selectedItems = document.getElementById('selectedItems');
    
    if (!searchInput || !selectedItems) return;
    
    const query = searchInput.value.trim();
    if (query.length < 3) {
        alert('Please enter at least 3 characters for search');
        return;
    }
    
    try {
        // Show loading indicator
        selectedItems.innerHTML = '<div class="loading">Searching...</div>';
        
        // Get filter options
        const options = {};
        if (window.marketFilters.categoryId) {
            options.category = window.marketFilters.categoryId;
        }
        if (window.marketFilters.groupId) {
            options.group = window.marketFilters.groupId;
        }
        
        const items = await window.marketAPI.searchItems(query, options);
        
        if (items.length === 0) {
            selectedItems.innerHTML = '<div class="no-results">No items found</div>';
            return;
        }
        
        // Display results
        let html = '<div class="search-results">';
        items.forEach(item => {
            html += `
                <div class="search-item" data-type-id="${item.type_id}">
                    <span class="item-name">${item.name}</span>
                    <button class="add-item-btn">Add</button>
                </div>
            `;
        });
        html += '</div>';
        
        selectedItems.innerHTML = html;
        
        // Add event listeners to "Add" buttons
        const addButtons = selectedItems.querySelectorAll('.add-item-btn');
        addButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const item = e.target.closest('.search-item');
                const typeId = item.dataset.typeId;
                const name = item.querySelector('.item-name').textContent;
                
                addSelectedItem(typeId, name);
            });
        });
    } catch (error) {
        console.error('Item search failed:', error);
        selectedItems.innerHTML = `<div class="error">Search failed: ${error.message}</div>`;
    }
}

// Add an item to the selected items
function addSelectedItem(typeId, name) {
    // Update filter state
    const typeIds = [...window.marketFilters.typeIds];
    if (!typeIds.includes(typeId)) {
        typeIds.push(typeId);
        setFilter('typeIds', typeIds);
        
        // Update UI
        updateSelectedItemsUI();
    }
}

// Remove an item from selected items
function removeSelectedItem(typeId) {
    // Update filter state
    const typeIds = window.marketFilters.typeIds.filter(id => id !== typeId);
    setFilter('typeIds', typeIds);
    
    // Update UI
    updateSelectedItemsUI();
}

// Update the selected items UI
function updateSelectedItemsUI() {
    const selectedItems = document.getElementById('selectedItems');
    if (!selectedItems) return;
    
    const typeIds = window.marketFilters.typeIds;
    
    if (typeIds.length === 0) {
        selectedItems.innerHTML = '<div class="no-selected-items">No items selected</div>';
        return;
    }
    
    // Show loading
    selectedItems.innerHTML = '<div class="loading">Loading selected items...</div>';
    
    // Fetch item details for each type ID
    const promises = typeIds.map(typeId =>
        window.marketAPI.getItemInfo(typeId)
            .catch(() => ({ type_id: typeId, name: `Unknown Item (${typeId})` }))
    );
    
    Promise.all(promises).then(items => {
        let html = '<div class="selected-items-list">';
        items.forEach(item => {
            html += `
                <div class="selected-item" data-type-id="${item.type_id}">
                    <span class="item-name">${item.name}</span>
                    <button class="remove-item-btn">×</button>
                </div>
            `;
        });
        html += '</div>';
        
        selectedItems.innerHTML = html;
        
        // Add event listeners to remove buttons
        const removeButtons = selectedItems.querySelectorAll('.remove-item-btn');
        removeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const item = e.target.closest('.selected-item');
                const typeId = item.dataset.typeId;
                removeSelectedItem(typeId);
            });
        });
    });
}

// Update the saved filters dropdown
function updateSavedFiltersDisplay(filters) {
    const select = document.getElementById('savedFiltersSelect');
    if (!select) return;
    
    // Clear existing options
    select.innerHTML = '<option value="">Select Saved Filter...</option>';
    
    // Add options for each saved filter
    const filterNames = Object.keys(filters);
    if (filterNames.length === 0) {
        select.innerHTML += '<option value="" disabled>No saved filters</option>';
        return;
    }
    
    // Sort by most recent first
    filterNames.sort((a, b) => {
        return filters[b].timestamp - filters[a].timestamp;
    });
    
    filterNames.forEach(name => {
        const filter = filters[name];
        const date = new Date(filter.timestamp).toLocaleDateString();
        select.innerHTML += `<option value="${name}">${name} (${date})</option>`;
    });
    
    // Select current filter if it exists
    if (window.marketFilters.savedFilterName) {
        select.value = window.marketFilters.savedFilterName;
    }
}

// Update the filter UI to reflect current filter state
function updateFilterUIDisplay(filters) {
    // Update category select
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect && filters.categoryId) {
        categorySelect.value = filters.categoryId;
    }
    
    // Update group select (may need to load groups first)
    if (filters.categoryId && filters.groupId) {
        loadGroups(filters.categoryId).then(() => {
            const groupSelect = document.getElementById('groupSelect');
            if (groupSelect) {
                groupSelect.value = filters.groupId;
                groupSelect.disabled = false;
            }
        });
    }
    
    // Update price inputs
    const minPriceInput = document.getElementById('minPriceInput');
    const maxPriceInput = document.getElementById('maxPriceInput');
    const minProfitInput = document.getElementById('minProfitInput');
    const minProfitPercentInput = document.getElementById('minProfitPercentInput');
    
    if (minPriceInput) {
        minPriceInput.value = filters.minPrice || '';
    }
    
    if (maxPriceInput) {
        maxPriceInput.value = filters.maxPrice || '';
    }
    
    if (minProfitInput) {
        minProfitInput.value = filters.minProfit || 100000;
    }
    
    if (minProfitPercentInput) {
        minProfitPercentInput.value = filters.minProfitPercent || 5;
    }
    
    // Update selected items
    updateSelectedItemsUI();
    
    // Update saved filter name
    const filterNameInput = document.getElementById('filterNameInput');
    if (filterNameInput) {
        filterNameInput.value = filters.savedFilterName || '';
    }
}

// Initialize the results UI
function initializeResultsUI() {
    // Nothing to do here yet, but we might add sorting controls later
}

// Enhanced results display
function displayComparisonResults(opportunities) {
    const resultsDiv = document.getElementById('comparisonResults');
    
    if (!opportunities || opportunities.length === 0) {
        resultsDiv.innerHTML = '<div class="no-results">No profitable opportunities found</div>';
        return;
    }
    
    let html = `
        <div class="results-header">
            <h3>Results (${opportunities.length} items)</h3>
            <div class="results-controls">
                <button id="exportResultsBtn" class="results-btn">Export CSV</button>
            </div>
        </div>
        
        <table class="results-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Public Station Trade</th>
                    <th>Private Station Trade</th>
                    <th>Buy Public, Sell Private</th>
                    <th>Buy Private, Sell Public</th>
                    <th>Volume</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    opportunities.forEach(opp => {
        const formatPrice = (price) => {
            if (price === Infinity) return 'N/A';
            if (price === 0) return 'N/A';
            return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        };
        
        const formatProfit = (profit, percent) => {
            if (profit <= 0) return '-';
            return `+${profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${percent.toFixed(1)}%)`;
        };
        
        html += `
            <tr>
                <td class="item-cell" title="${opp.description || ''}">
                    <div class="item-name">${opp.itemName || opp.typeId}</div>
                    <div class="item-category">${opp.categoryId || ''}</div>
                </td>
                <td class="${opp.stationTradePublicProfit > 0 ? 'profit' : ''}">
                    ${formatProfit(opp.stationTradePublicProfit, opp.stationTradePublicProfitPercent)}
                </td>
                <td class="${opp.stationTradePrivateProfit > 0 ? 'profit' : ''}">
                    ${formatProfit(opp.stationTradePrivateProfit, opp.stationTradePrivateProfitPercent)}
                </td>
                <td class="${opp.buyFromPublicProfit > 0 ? 'profit' : ''}">
                    ${formatProfit(opp.buyFromPublicProfit, opp.buyFromPublicProfitPercent)}
                </td>
                <td class="${opp.buyFromPrivateProfit > 0 ? 'profit' : ''}">
                    ${formatProfit(opp.buyFromPrivateProfit, opp.buyFromPrivateProfitPercent)}
                </td>
                <td>
                    <div>Buy: ${opp.publicBuyVolume.toLocaleString()} / ${opp.privateBuyVolume.toLocaleString()}</div>
                    <div>Sell: ${opp.publicSellVolume.toLocaleString()} / ${opp.privateSellVolume.toLocaleString()}</div>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    resultsDiv.innerHTML = html;
    
    // Add event listener for export button
    const exportBtn = document.getElementById('exportResultsBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            exportResultsToCSV(opportunities);
        });
    }
}

// Export results to CSV
function exportResultsToCSV(opportunities) {
    // Create CSV content
    let csv = 'Item,Public Buy,Public Sell,Private Buy,Private Sell,Buy from Public Profit,Buy from Public %,Buy from Private Profit,Buy from Private %\n';
    
    opportunities.forEach(opp => {
        const row = [
            `"${opp.itemName || opp.typeId}"`,
            opp.publicBuyMax || 0,
            opp.publicSellMin === Infinity ? 0 : opp.publicSellMin,
            opp.privateBuyMax || 0,
            opp.privateSellMin === Infinity ? 0 : opp.privateSellMin,
            opp.buyFromPublicProfit || 0,
            opp.buyFromPublicProfitPercent || 0,
            opp.buyFromPrivateProfit || 0,
            opp.buyFromPrivateProfitPercent || 0
        ];
        
        csv += row.join(',') + '\n';
    });
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `eve-market-comparison-${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Update login status
function updateUIForLoggedInUser() {
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.textContent = 'Logged In ✓';
        loginBtn.style.backgroundColor = '#4CAF50';
        
        // Add logout functionality
        loginBtn.onclick = () => {
            if (confirm('Do you want to logout?')) {
                localStorage.removeItem('eveAccessToken');
                window.location.reload();
            }
        };
    }
}

// Make functions available globally
window.displayComparisonResults = displayComparisonResults;
window.updateFilterUIDisplay = updateFilterUIDisplay;
window.updateSavedFiltersDisplay = updateSavedFiltersDisplay;