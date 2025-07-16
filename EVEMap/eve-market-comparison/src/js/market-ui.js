// Enhanced UI display functions with advanced filtering

// Initialize UI components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for all required functions to be available before initializing UI
    waitForDependencies().then(() => {
        initializeUI();
    });
});

// Function to wait for all required dependencies
async function waitForDependencies() {
    let attempts = 0;
    const maxAttempts = 200; // Wait up to 20 seconds
    
    while (attempts < maxAttempts) {
        // Check if all required dependencies are available
        const hasMarketFilters = !!window.marketFilters;
        const hasSetFilter = typeof window.setFilter === 'function';
        const hasCompareMarkets = typeof window.compareMarkets === 'function';
        const hasInitializeMarketFilters = typeof window.initializeMarketFilters === 'function';
        const hasCompareCategoryMarkets = typeof window.compareCategoryMarkets === 'function';
        
        if (hasMarketFilters && hasSetFilter && hasCompareMarkets && hasInitializeMarketFilters && hasCompareCategoryMarkets) {
            console.log('✅ All dependencies available for market-ui.js initialization');
            // Initialize market filters if not already done
            if (window.initializeMarketFilters && typeof window.marketFilters === 'object') {
                window.initializeMarketFilters();
            }
            return true;
        }
        
        if (attempts % 10 === 0) { // Log every second
            console.log(`⏳ market-ui.js waiting for dependencies (attempt ${attempts + 1}/${maxAttempts}):`, {
                marketFilters: hasMarketFilters,
                setFilter: hasSetFilter,
                compareMarkets: hasCompareMarkets,
                initializeMarketFilters: hasInitializeMarketFilters,
                compareCategoryMarkets: hasCompareCategoryMarkets
            });
        }
        
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }
    
    console.error('❌ Timeout waiting for dependencies in market-ui.js');
    return false;
}

function initializeUI() {
    console.log('🎨 Initializing UI components...');
    
    // Check if marketFilters is available
    if (!window.marketFilters) {
        console.warn('⚠️ window.marketFilters not available during UI initialization');
        // Create a minimal marketFilters object to prevent errors
        window.marketFilters = {
            groupIds: [],
            excludedGroupIds: [],
            typeIds: [],
            minPrice: null,
            maxPrice: null,
            minProfit: 100000,
            minProfitPercent: 5,
            searchQuery: '',
            savedFilterName: '',
            showMissingItems: true,
            firstLocationOrderType: 'sell',
            secondLocationOrderType: 'sell'
        };
    }
    
    // Initialize market filters if the function exists
    if (window.initializeMarketFilters) {
        window.initializeMarketFilters();
    }
    
    // Only initialize the old filter UI if we're in compatibility mode
    // For group-based filtering, the group-filter-ui.js will handle the UI
    if (!document.getElementById('filterPanel')) {
        console.log('🎨 Creating traditional filter UI...');
        initializeFilterUI();
    } else {
        console.log('🎨 Group filter UI already present, skipping traditional UI');
    }
    
    initializeResultsUI();
    initializeLocationDropdowns();
    
    // Check login status
    const token = localStorage.getItem('eveAccessToken');
    if (token) {
        updateUIForLoggedInUser();
    }
    
    console.log('✅ UI initialization complete');
}

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
                    <button id="fullCategoryBtn" class="filter-btn primary-btn" title="Compare all items in the selected category" style="margin-left: 10px;" disabled>Full Category Compare</button>
                    <button id="downloadCategoryBtn" class="filter-btn" title="Download all items in the selected category from the buy location" style="margin-left: 10px;" disabled>Download Category</button>
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
                <h4>Excluded Categories</h4>
                <div class="filter-row">
                    <select id="excludeCategorySelect" class="filter-select">
                        <option value="">Select Category to Exclude...</option>
                        <!-- Categories will be loaded dynamically -->
                    </select>
                    <button id="addExcludedCategoryBtn" class="filter-btn">Add</button>
                </div>
                <div id="excludedCategoriesList" class="excluded-categories-list">
                    <!-- Excluded categories will appear here -->
                    <p class="info-text">No categories excluded. Items from all categories will be included in searches.</p>
                </div>
                <div class="filter-info">
                    <div class="tooltip">
                        <span class="tooltip-icon">?</span>
                        <span class="tooltip-text">Excluded categories will be skipped during searches and comparisons. This can save bandwidth and processing time by ignoring categories you're not interested in.</span>
                    </div>
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
                
                <div class="filter-row">
                    <div class="checkbox-container">
                        <input type="checkbox" id="showMissingItemsCheckbox" class="filter-checkbox" checked>
                        <label for="showMissingItemsCheckbox">Show items available only in buy location</label>
                        <div class="tooltip">
                            <span class="tooltip-icon">?</span>
                            <span class="tooltip-text">Show items that are available for purchase in the first location but have no buy orders in the second location. These could be potential opportunities to be the first seller in that market.</span>
                        </div>
                    </div>
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

    // Market ID input listeners are now handled in initializeLocationDropdowns()
    
    // Category selection
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect) {
        categorySelect.addEventListener('change', async () => {
            const categoryId = categorySelect.value;
            if (categoryId) {
                await loadGroups(categoryId);
                
                // Wait for dependencies if not available
                if (!window.setFilter || !window.marketFilters) {
                    console.log('⏳ Category handler waiting for dependencies...');
                    await waitForDependencies();
                }
                
                // Safely set the category filter
                if (window.setFilter) {
                    console.log(`🎯 Setting categoryId filter: ${categoryId}`);
                    window.setFilter('categoryId', categoryId);
                } else if (window.marketFilters) {
                    // Ensure categoryId property exists
                    if (!window.marketFilters.hasOwnProperty('categoryId')) {
                        window.marketFilters.categoryId = null;
                    }
                    console.log(`🎯 Setting categoryId in marketFilters: ${categoryId}`);
                    window.marketFilters.categoryId = categoryId;
                } else {
                    console.error('❌ Cannot set categoryId - marketFilters and setFilter still not available after waiting');
                }
                
                // Enable group select and category buttons
                const groupSelect = document.getElementById('groupSelect');
                const fullCategoryBtn = document.getElementById('fullCategoryBtn');
                const downloadCategoryBtn = document.getElementById('downloadCategoryBtn');

                if (groupSelect) groupSelect.disabled = false;
                if (fullCategoryBtn) fullCategoryBtn.disabled = false;
                if (downloadCategoryBtn) downloadCategoryBtn.disabled = false;

                // Recalculate results if data exists
                const buyLocationInput = document.getElementById('buyLocationInput');
                const sellLocationInput = document.getElementById('sellLocationInput');
                if (buyLocationInput && sellLocationInput && buyLocationInput.value && sellLocationInput.value && window.recalculateMarketComparison) {
                    window.recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
                }

            } else {
                if (window.setFilter) {
                    window.setFilter('categoryId', null);
                } else if (window.marketFilters) {
                    window.marketFilters.categoryId = null;
                }
                
                // Disable and reset group select and category buttons
                const groupSelect = document.getElementById('groupSelect');
                const fullCategoryBtn = document.getElementById('fullCategoryBtn');
                const downloadCategoryBtn = document.getElementById('downloadCategoryBtn');

                if (groupSelect) {
                    groupSelect.disabled = true;
                    groupSelect.innerHTML = '<option value="">Select Group...</option>';
                }
                if (fullCategoryBtn) fullCategoryBtn.disabled = true;
                if (downloadCategoryBtn) downloadCategoryBtn.disabled = true;

                // Recalculate results if data exists (show all categories)
                const buyLocationInput = document.getElementById('buyLocationInput');
                const sellLocationInput = document.getElementById('sellLocationInput');
                if (buyLocationInput && sellLocationInput && buyLocationInput.value && sellLocationInput.value && window.recalculateMarketComparison) {
                    window.recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
                }
            }
        });
    }
    
    // Group selection
    const groupSelect = document.getElementById('groupSelect');
    if (groupSelect) {
        groupSelect.addEventListener('change', () => {
            const groupId = groupSelect.value;
            if (window.setFilter) {
                window.setFilter('groupId', groupId ? groupId : null);
            } else {
                window.marketFilters.groupId = groupId ? groupId : null;
            }
            
            // Recalculate results if data exists
            const buyLocationInput = document.getElementById('buyLocationInput');
            const sellLocationInput = document.getElementById('sellLocationInput');
            if (buyLocationInput && sellLocationInput && buyLocationInput.value && sellLocationInput.value && window.recalculateMarketComparison) {
                window.recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
            }
        });
    }
    
    const fullCategoryBtn = document.getElementById('fullCategoryBtn');
    if (fullCategoryBtn) {
        fullCategoryBtn.addEventListener('click', async () => {
            const categoryId = document.getElementById('categorySelect').value;
            const buyLocationId = document.getElementById('buyLocationInput').value;
            const sellLocationId = document.getElementById('sellLocationInput').value;
            
            if (categoryId && buyLocationId && sellLocationId) {
                // Wait for dependencies if not available
                if (!window.compareCategoryMarkets) {
                    console.log('⏳ Full category handler waiting for dependencies...');
                    await waitForDependencies();
                }
                
                if (window.compareCategoryMarkets) {
                    console.log(`🚀 Starting full category comparison for category ${categoryId}`);
                    window.compareCategoryMarkets(buyLocationId, sellLocationId, categoryId);
                } else {
                    console.error('❌ compareCategoryMarkets still not available after waiting');
                    alert('Error: Category comparison function is not available. Please refresh the page.');
                }
            } else {
                alert('Please select a category and enter both market locations');
            }
        });
    }

    const downloadCategoryBtn = document.getElementById('downloadCategoryBtn');
    if (downloadCategoryBtn) {
        downloadCategoryBtn.addEventListener('click', () => {
            const categoryId = document.getElementById('categorySelect').value;
            const buyLocationId = document.getElementById('buyLocationInput').value;
            
            if (categoryId && buyLocationId) {
                downloadCategoryData(buyLocationId, categoryId);
            } else {
                alert('Please select a category and enter a buy market location');
            }
        });
    }
    
    // Excluded categories handling
    const excludeCategorySelect = document.getElementById('excludeCategorySelect');
    const addExcludedCategoryBtn = document.getElementById('addExcludedCategoryBtn');
    
    if (excludeCategorySelect && addExcludedCategoryBtn) {
        // Load the same categories as in the main category select
        loadCategories(excludeCategorySelect);
        
        // Add event listener for the add button
        addExcludedCategoryBtn.addEventListener('click', () => {
            const categoryId = excludeCategorySelect.value;
            const categoryName = excludeCategorySelect.options[excludeCategorySelect.selectedIndex].text;
            
            if (categoryId) {
                addExcludedCategory(categoryId, categoryName);
                excludeCategorySelect.value = ''; // Reset selection
            } else {
                alert('Please select a category to exclude');
            }
        });
        
        // Update the display of excluded categories
        updateExcludedCategoriesUI();
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
    
    // Missing items checkbox
    const showMissingItemsCheckbox = document.getElementById('showMissingItemsCheckbox');
    if (showMissingItemsCheckbox) {
        showMissingItemsCheckbox.addEventListener('change', () => {
            setFilter('showMissingItems', showMissingItemsCheckbox.checked);
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
            const buyLocationId = document.querySelector('#marketComparison .input-group #buyLocationInput').value;
            const sellLocationId = document.querySelector('#marketComparison .input-group #sellLocationInput').value;
            compareMarkets(buyLocationId, sellLocationId);
        });
    }
    
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', () => {
            resetFilters();
        });
    }
}

// Add this to your market-ui.js file

// Add after the initializeFilterUI() function
function initializeLocationDropdowns() {
    console.log('initializeLocationDropdowns called');
    const marketInputs = [
        {inputId: 'buyLocationInput', dropdownId: 'buyLocationDropdown', labelId: 'buyLocationTypeDisplay'},
        {inputId: 'sellLocationInput', dropdownId: 'sellLocationDropdown', labelId: 'sellLocationTypeDisplay'}
    ];
    
    marketInputs.forEach(({inputId, dropdownId, labelId}) => {
        console.log(`Processing input: ${inputId}`);
        // Get or create the input wrapper
        const input = document.getElementById(inputId);
        if (!input) {
            console.warn(`Input element ${inputId} not found`);
            return;
        }
        
        const wrapper = input.parentElement;
        if (!wrapper || !wrapper.classList.contains('market-input-wrapper')) {
            console.warn(`Wrapper for ${inputId} not found or incorrect class`);
            return;
        }
        
        // Check if dropdown already exists
        if (document.getElementById(dropdownId)) {
            console.log(`Dropdown ${dropdownId} already exists`);
            return;
        }
        
        // Create dropdown structure
        const dropdownHtml = `
            <div class="location-dropdown-container">
                <select id="${dropdownId}" class="location-dropdown">
                    <option value="">Saved locations...</option>
                </select>
                <button id="${dropdownId}-save" class="location-save-btn" title="Save current location">+</button>
            </div>
        `;
        
        // Insert dropdown after input
        wrapper.insertAdjacentHTML('beforeend', dropdownHtml);
        console.log(`Dropdown ${dropdownId} created successfully`);
        
        // Load saved locations (using shared storage)
        loadSavedLocations(dropdownId);
        
        // Add event listeners
        const dropdown = document.getElementById(dropdownId);
        const saveBtn = document.getElementById(`${dropdownId}-save`);
        
        if (dropdown) {
            dropdown.addEventListener('change', () => {
                if (dropdown.value) {
                    const [locationId, locationType] = dropdown.value.split('|');
                    if (locationId && locationType) {
                        input.value = locationId;
                        
                        // Update the type display
                        const typeDisplay = document.getElementById(labelId);
                        if (typeDisplay) {
                            typeDisplay.textContent = `Type: ${locationType}`;
                            typeDisplay.className = 'market-type-display detected';
                        }
                        
                        // Update placeholder
                        updateMarketInputPlaceholder(locationType, input);
                        
                        // Trigger input event to update any other UI
                        const event = new Event('input', { bubbles: true });
                        input.dispatchEvent(event);
                    }
                }
            });
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                const locationId = input.value.trim();
                if (!locationId) {
                    alert('Please enter a location ID first');
                    return;
                }
                
                try {
                    const marketInfo = window.getMarketIdInfo ? window.getMarketIdInfo(locationId) : getMarketIdInfo(locationId);
                    const locationName = prompt('Enter a name for this location:', '');
                    if (locationName) {
                        // Use shared storage (dropdownId no longer matters)
                        saveLocation(locationId, locationName, marketInfo.type);
                        
                        // Update all dropdowns to show the new location
                        marketInputs.forEach(item => {
                            loadSavedLocations(item.dropdownId);
                        });
                    }
                } catch (error) {
                    alert('Invalid location ID format');
                }
            });
        }
        
        // Add structure type detection to input
        input.addEventListener('input', () => {
            const marketId = input.value.trim();
            const typeDisplay = document.getElementById(labelId);
            if (typeDisplay && marketId) {
                try {
                    const marketInfo = window.getMarketIdInfo ? window.getMarketIdInfo(marketId) : getMarketIdInfo(marketId);
                    typeDisplay.textContent = `Type: ${marketInfo.type}`;
                    typeDisplay.className = 'market-type-display detected';
                    updateMarketInputPlaceholder(marketInfo.type, input);
                } catch (error) {
                    typeDisplay.textContent = 'Unknown Type';
                    typeDisplay.className = 'market-type-display error';
                }
            }
        });
    });
}

// Save a location to localStorage (shared between dropdowns)
function saveLocation(locationId, name, type) {
    // Use a single storage key for all locations
    const storageKey = 'eve-market-saved-locations';
    
    // Get existing locations
    let savedLocations = JSON.parse(localStorage.getItem(storageKey) || '[]');
    
    // Check if already exists
    const existingIndex = savedLocations.findIndex(loc => loc.id === locationId);
    if (existingIndex >= 0) {
        // Update existing
        savedLocations[existingIndex].name = name;
        savedLocations[existingIndex].timestamp = Date.now(); // Update timestamp
    } else {
        // Add new
        savedLocations.push({
            id: locationId,
            name: name,
            type: type,
            timestamp: Date.now()
        });
    }
    
    // Save back to localStorage
    localStorage.setItem(storageKey, JSON.stringify(savedLocations));
}

// Load saved locations into dropdown
function loadSavedLocations(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    // Use shared storage key
    const storageKey = 'eve-market-saved-locations';
    
    // Get saved locations
    const savedLocations = JSON.parse(localStorage.getItem(storageKey) || '[]');
    
    // Clear existing options (except first)
    while (dropdown.options.length > 1) {
        dropdown.remove(1);
    }
    
    // Add saved locations
    if (savedLocations.length === 0) {
        const option = document.createElement('option');
        option.disabled = true;
        option.text = 'No saved locations';
        dropdown.add(option);
    } else {
        // Sort by most recently used
        savedLocations.sort((a, b) => b.timestamp - a.timestamp);
        
        savedLocations.forEach(location => {
            const option = document.createElement('option');
            option.value = `${location.id}|${location.type}`;
            option.text = `${location.name} (${location.type}: ${location.id})`;
            dropdown.add(option);
        });
    }
}

// Helper to update all location dropdowns
function updateAllLocationDropdowns() {
    const dropdownIds = ['buyLocationDropdown', 'sellLocationDropdown'];
    dropdownIds.forEach(dropdownId => {
        loadSavedLocations(dropdownId);
    });
}

// Load categories from API
async function loadCategories(excludeSelect) {
    try {
        const categories = await window.marketAPI.getCategories();
        const categorySelect = document.getElementById('categorySelect');
        const excludeCategorySelect = excludeSelect || document.getElementById('excludeCategorySelect');
        
        // Sort categories by name once
        if (categories) {
            categories.sort((a, b) => a.name.localeCompare(b.name));
        }
        
        if (categorySelect && categories) {
            // Add options
            let options = '<option value="">Select Category...</option>';
            categories.forEach(category => {
                options += `<option value="${category.category_id}">${category.name}</option>`;
            });
            
            categorySelect.innerHTML = options;
        }
        
        if (excludeCategorySelect && categories) {
            // Add options for excluded categories
            let excludeOptions = '<option value="">Select Category to Exclude...</option>';
            
            // Filter out already excluded categories for better UX
            const excludedCategoryIds = window.marketFilters?.excludedCategoryIds || [];
            
            categories.forEach(category => {
                // Skip already excluded categories
                if (!excludedCategoryIds.includes(category.category_id.toString())) {
                    excludeOptions += `<option value="${category.category_id}">${category.name}</option>`;
                }
            });
            
            excludeCategorySelect.innerHTML = excludeOptions;
        }
        
        // Update the excluded categories UI to reflect current state
        // Only if we're using the old category system
        if (window.marketFilters && window.marketFilters.hasOwnProperty('excludedCategoryIds')) {
            updateExcludedCategoriesUI();
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
        if (window.setFilter) {
            window.setFilter('typeIds', typeIds);
        } else {
            window.marketFilters.typeIds = typeIds;
        }
        
        // Update UI
        updateSelectedItemsUI();
    }
}

// Remove an item from selected items
function removeSelectedItem(typeId) {
    // Update filter state
    const typeIds = window.marketFilters.typeIds.filter(id => id !== typeId);
    if (window.setFilter) {
        window.setFilter('typeIds', typeIds);
    } else {
        window.marketFilters.typeIds = typeIds;
    }
    
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
    
    // Update excluded categories UI
    if (filters.excludedCategoryIds) {
        updateExcludedCategoriesUI();
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
    
    // Update missing items checkbox
    const showMissingItemsCheckbox = document.getElementById('showMissingItemsCheckbox');
    if (showMissingItemsCheckbox) {
        showMissingItemsCheckbox.checked = filters.showMissingItems !== false; // Default to true if not specified
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

    // Update the live results display to show it's complete
    const notice = document.querySelector('.partial-results-notice');
    if (notice) {
        notice.textContent = 'Analysis complete. Displaying final results.';
        notice.classList.remove('active');
    }
    
    // Filter out items from excluded categories (extra check to ensure nothing is missed)
    const excludedCategoryIds = window.marketFilters?.excludedCategoryIds || [];
    const filteredOpportunities = opportunities.filter(opp => 
        !opp.categoryId || !excludedCategoryIds.includes(opp.categoryId.toString())
    );
    
    // Separate regular opportunities from missing items
    const regularOpportunities = filteredOpportunities.filter(opp => !opp.isMissingInSellLocation);
    const missingItems = filteredOpportunities.filter(opp => opp.isMissingInSellLocation);
    
    // Display missing items if enabled
    if (window.marketFilters.showMissingItems && missingItems.length > 0) {
        window.updateMissingItemsList(missingItems);
    } else {
        // Remove missing items section if not showing
        const missingItemsSection = document.getElementById('missing-items-section');
        if (missingItemsSection) {
            missingItemsSection.remove();
        }
    }

    let html = `
        <div class="results-header">
            <h3>Results (${regularOpportunities.length} items)</h3>
            <div class="results-controls">
                <button id="exportResultsBtn" class="results-btn">Export CSV</button>
            </div>
        </div>
        
        <table class="results-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Buy Price</th>
                    <th>Sell Price</th>
                    <th>Profit</th>
                    <th>Profit %</th>
                    <th>Volume (Buy/Sell)</th>
                </tr>
            </thead>
            <tbody>
    `;

    regularOpportunities.forEach(opp => {
        const formatPrice = (price) => {
            if (price === Infinity || price === null) return 'N/A';
            return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        };

        html += `
            <tr>
                <td class="item-cell" title="${opp.description || ''}">
                    <div class="item-name">${opp.itemName || opp.typeId}</div>
                    <div class="item-category">${opp.categoryId || ''}</div>
                </td>
                <td>${formatPrice(opp.buyPrice)}</td>
                <td>${formatPrice(opp.sellPrice)}</td>
                <td class="profit">+${formatPrice(opp.profit)}</td>
                <td class="profit">${opp.profitPercent ? opp.profitPercent.toFixed(1) + '%' : 'N/A'}</td>
                <td>${opp.buyVolume.toLocaleString()} / ${opp.sellVolume.toLocaleString()}</td>
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
    // Separate regular opportunities from missing items
    const regularOpportunities = opportunities.filter(opp => !opp.isMissingInSellLocation);
    const missingItems = opportunities.filter(opp => opp.isMissingInSellLocation);
    
    // Create CSV content for regular opportunities
    let regularCsv = 'Item,Buy Price,Sell Price,Profit,Profit %,Buy Volume,Sell Volume\n';
    regularOpportunities.forEach(opp => {
        const row = [
            `"${opp.itemName || opp.typeId}"`,
            opp.buyPrice,
            opp.sellPrice,
            opp.profit,
            opp.profitPercent ? opp.profitPercent.toFixed(2) : 'N/A',
            opp.buyVolume,
            opp.sellVolume
        ];
        regularCsv += row.join(',') + '\n';
    });
    
    // Create CSV content for missing items if they exist
    let missingCsv = '';
    if (missingItems.length > 0) {
        missingCsv = '\n\nItems Available Only in Buy Location\n';
        missingCsv += 'Item,Buy Price,Available Volume\n';
        
        missingItems.forEach(opp => {
            const row = [
                `"${opp.itemName || opp.typeId}"`,
                opp.buyPrice,
                opp.buyVolume
            ];
            missingCsv += row.join(',') + '\n';
        });
    }
    
    // Combine the CSVs
    const csv = regularCsv + missingCsv;
    
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

// Update market input placeholder based on structure type
function updateMarketInputPlaceholder(locationType, input) {
    const placeholders = {
        'region': 'Enter Region ID (e.g., 10000002 for The Forge)',
        'station': 'Enter Station ID (e.g., 60003760 for Jita 4-4)',
        'structure': 'Enter Structure ID',
        'constellation': 'Enter Constellation ID (e.g., 20000001)',
        'solar_system': 'Enter Solar System ID (e.g., 30000142)',
        'corporation': 'Enter Corporation ID',
        'alliance': 'Enter Alliance ID'
    };

    input.placeholder = placeholders[locationType] || 'Enter Market ID';
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

// Add a category to the excluded list
function addExcludedCategory(categoryId, categoryName) {
    // Ensure categoryId is a string for consistent comparison
    categoryId = categoryId.toString();
    
    // Get current excluded categories
    const excludedCategories = [...window.marketFilters.excludedCategoryIds];
    
    // Check if already excluded
    if (excludedCategories.includes(categoryId)) {
        alert(`Category "${categoryName}" is already excluded.`);
        return;
    }
    
    // Check if it matches the currently selected category
    const currentCategoryId = window.marketFilters.categoryId?.toString();
    if (currentCategoryId === categoryId) {
        if (!confirm(`Warning: You're about to exclude the currently selected category "${categoryName}". This will prevent any searches or downloads for this category. Continue?`)) {
            return;
        }
    }
    
    // Add to excluded list and persist
    excludedCategories.push(categoryId);
    window.setFilter('excludedCategoryIds', excludedCategories);
    
    // Update UI
    updateExcludedCategoriesUI();
    
    // Recalculate results if data exists
    const buyLocationInput = document.getElementById('buyLocationInput');
    const sellLocationInput = document.getElementById('sellLocationInput');
    if (buyLocationInput && sellLocationInput && buyLocationInput.value && sellLocationInput.value && window.recalculateMarketComparison) {
        window.recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
    }
}

// Remove a category from the excluded list
function removeExcludedCategory(categoryId) {
    // Ensure categoryId is a string for consistent comparison
    categoryId = categoryId.toString();
    
    // Get current excluded categories
    const excludedCategories = window.marketFilters.excludedCategoryIds.filter(id => id !== categoryId);
    
    // Update filter and persist
    window.setFilter('excludedCategoryIds', excludedCategories);
    
    // Update UI
    updateExcludedCategoriesUI();
    
    // Refresh the exclude category select to show the newly available category
    loadCategories();
    
    // Recalculate results if data exists
    const buyLocationInput = document.getElementById('buyLocationInput');
    const sellLocationInput = document.getElementById('sellLocationInput');
    if (buyLocationInput && sellLocationInput && buyLocationInput.value && sellLocationInput.value && window.recalculateMarketComparison) {
        window.recalculateMarketComparison(buyLocationInput.value, sellLocationInput.value);
    }
}

// Update the excluded categories UI display
function updateExcludedCategoriesUI() {
    const container = document.getElementById('excludedCategoriesList');
    if (!container) return;
    
    // Check if we're using the new group-based system
    if (!window.marketFilters || !window.marketFilters.hasOwnProperty('excludedCategoryIds')) {
        // New group-based system - show a message about the new filtering
        container.innerHTML = `
            <p class="info-text">
                🎯 <strong>New Group-Based Filtering Active!</strong><br>
                Category-based filtering has been replaced with more granular group-based filtering. 
                Use the Group Filters section above for better control.
            </p>
        `;
        return;
    }
    
    const excludedCategories = window.marketFilters.excludedCategoryIds;
    
    // If no excluded categories
    if (!excludedCategories || excludedCategories.length === 0) {
        container.innerHTML = '<p class="info-text">No categories excluded. Items from all categories will be included in searches.</p>';
        return;
    }
    
    // Get category names from both select boxes
    const getCategoryName = (categoryId) => {
        const mainSelect = document.getElementById('categorySelect');
        const excludeSelect = document.getElementById('excludeCategorySelect');
        
        // Try to find in main select
        if (mainSelect) {
            for (const option of mainSelect.options) {
                if (option.value === categoryId) {
                    return option.text;
                }
            }
        }
        
        // Try to find in exclude select
        if (excludeSelect) {
            for (const option of excludeSelect.options) {
                if (option.value === categoryId) {
                    return option.text;
                }
            }
        }
        
        // Default if not found
        return `Category ${categoryId}`;
    };
    
    // Build HTML for excluded categories
    let html = '';
    for (const categoryId of excludedCategories) {
        const categoryName = getCategoryName(categoryId);
        html += `
            <div class="excluded-category-item" data-category-id="${categoryId}">
                <span class="excluded-category-name">${categoryName}</span>
                <button class="remove-excluded-btn" title="Remove from exclusion list">×</button>
            </div>
        `;
    }
    
    container.innerHTML = html;
    
    // Add event listeners to remove buttons
    const removeButtons = container.querySelectorAll('.remove-excluded-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const item = e.target.closest('.excluded-category-item');
            const categoryId = item.dataset.categoryId;
            removeExcludedCategory(categoryId);
        });
    });
}

// Function to handle loading categories for different select elements

// Export functions to global scope for testing and external access
window.addExcludedCategory = addExcludedCategory;
window.removeExcludedCategory = removeExcludedCategory;
window.updateExcludedCategoriesUI = updateExcludedCategoriesUI;
window.loadCategories = loadCategories;