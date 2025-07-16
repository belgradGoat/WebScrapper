/**
 * Group-based Filter UI Management
 * Creates and manages the group filtering interface
 */

function createGroupFilterUI() {
    console.log('🎨 Creating group filter UI...');
    
    // Find the container where we want to insert the filter UI
    let insertionContainer = document.getElementById('filterContainer');
    
    // If filterContainer doesn't exist, create it and insert before comparison results
    if (!insertionContainer) {
        const comparisonSection = document.getElementById('marketComparison');
        const resultsDiv = document.getElementById('comparisonResults');
        
        if (comparisonSection && resultsDiv) {
            insertionContainer = document.createElement('div');
            insertionContainer.id = 'filterContainer';
            comparisonSection.insertBefore(insertionContainer, resultsDiv);
            console.log('   📦 Created filter container');
        } else {
            console.error('   ❌ Could not find insertion point for filter UI');
            return false;
        }
    }
    
    const filterHTML = `
        <div id="filterPanel" class="filter-panel">
            <h3>🔧 Market Filters</h3>
            
            <!-- Group Filters Section -->
            <div class="filter-section">
                <h4>📦 Group Filters</h4>
                <div class="filter-row">
                    <label for="includeGroups">Include Groups (comma-separated IDs):</label>
                    <input type="text" id="includeGroups" placeholder="e.g., 25,26,27 (leave empty for all)" />
                    <button onclick="setIncludeGroups()">Set Include</button>
                </div>
                <div class="filter-row">
                    <label for="excludeGroups">Exclude Groups (comma-separated IDs):</label>
                    <input type="text" id="excludeGroups" placeholder="e.g., 60,40 (modules)" />
                    <button onclick="setExcludeGroups()">Set Exclude</button>
                </div>
                <div class="filter-row">
                    <button onclick="clearGroupFilters()">Clear All Group Filters</button>
                    <button onclick="showGroupInfo()">Show Common Groups</button>
                </div>
            </div>
            
            <!-- Quick Group Presets -->
            <div class="filter-section">
                <h4>🚀 Quick Presets</h4>
                <div class="preset-buttons">
                    <button onclick="setPreset('frigates')" class="preset-btn">Frigates Only</button>
                    <button onclick="setPreset('cruisers')" class="preset-btn">Cruisers Only</button>
                    <button onclick="setPreset('battleships')" class="preset-btn">Battleships Only</button>
                    <button onclick="setPreset('minerals')" class="preset-btn">Minerals Only</button>
                    <button onclick="setPreset('exclude-ships')" class="preset-btn">Exclude All Ships</button>
                </div>
            </div>
            
            <!-- Traditional Filters -->
            <div class="filter-section">
                <h4>💰 Price & Profit Filters</h4>
                <div class="filter-row">
                    <label for="minProfit">Min Profit (ISK):</label>
                    <input type="number" id="minProfit" value="100000" />
                </div>
                <div class="filter-row">
                    <label for="minProfitPercent">Min Profit (%):</label>
                    <input type="number" id="minProfitPercent" value="5" step="0.1" />
                </div>
                <div class="filter-row">
                    <label for="searchQuery">Search Items:</label>
                    <input type="text" id="searchQuery" placeholder="Item name contains..." />
                </div>
            </div>
            
            <!-- Filter Status -->
            <div class="filter-section">
                <h4>📊 Current Filters</h4>
                <div id="filterStatus" class="filter-status">
                    <p>No filters active</p>
                </div>
            </div>
        </div>
    `;
    
    // Insert the HTML into the container
    insertionContainer.innerHTML = filterHTML;
    console.log('   ✅ Group filter UI HTML inserted');
    
    // Initialize the filter status display
    updateFilterStatus();
    
    return true;
}

function setIncludeGroups() {
    const input = document.getElementById('includeGroups');
    const value = input.value.trim();
    
    if (value === '') {
        window.setFilter('groupIds', []);
        console.log('✅ Cleared include groups - showing all groups');
    } else {
        const groupIds = value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        if (groupIds.length > 0) {
            window.setFilter('groupIds', groupIds);
            console.log('✅ Set include groups:', groupIds);
        } else {
            alert('Please enter valid group IDs separated by commas');
            return;
        }
    }
    
    updateFilterStatus();
    triggerRecalculation();
}

function setExcludeGroups() {
    const input = document.getElementById('excludeGroups');
    const value = input.value.trim();
    
    if (value === '') {
        window.setFilter('excludedGroupIds', []);
        console.log('✅ Cleared exclude groups');
    } else {
        const groupIds = value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        if (groupIds.length > 0) {
            window.setFilter('excludedGroupIds', groupIds);
            console.log('✅ Set exclude groups:', groupIds);
        } else {
            alert('Please enter valid group IDs separated by commas');
            return;
        }
    }
    
    updateFilterStatus();
    triggerRecalculation();
}

function clearGroupFilters() {
    window.setFilter('groupIds', []);
    window.setFilter('excludedGroupIds', []);
    
    document.getElementById('includeGroups').value = '';
    document.getElementById('excludeGroups').value = '';
    
    console.log('✅ Cleared all group filters');
    updateFilterStatus();
    triggerRecalculation();
}

function setPreset(presetName) {
    console.log('🎯 Setting preset:', presetName);
    
    // Clear existing group filters first
    window.setFilter('groupIds', []);
    window.setFilter('excludedGroupIds', []);
    
    switch (presetName) {
        case 'frigates':
            window.setFilter('groupIds', [25]); // Frigate group
            document.getElementById('includeGroups').value = '25';
            break;
        case 'cruisers':
            window.setFilter('groupIds', [26]); // Cruiser group
            document.getElementById('includeGroups').value = '26';
            break;
        case 'battleships':
            window.setFilter('groupIds', [27]); // Battleship group
            document.getElementById('includeGroups').value = '27';
            break;
        case 'minerals':
            window.setFilter('groupIds', [18]); // Mineral group
            document.getElementById('includeGroups').value = '18';
            break;
        case 'exclude-ships':
            window.setFilter('excludedGroupIds', [25, 26, 27, 28, 29, 30, 31]); // Common ship groups
            document.getElementById('excludeGroups').value = '25,26,27,28,29,30,31';
            break;
        default:
            console.warn('Unknown preset:', presetName);
            return;
    }
    
    updateFilterStatus();
    triggerRecalculation();
}

function showGroupInfo() {
    const commonGroups = [
        { id: 25, name: 'Frigate', description: 'Small, fast ships' },
        { id: 26, name: 'Cruiser', description: 'Medium-sized versatile ships' },
        { id: 27, name: 'Battleship', description: 'Large, powerful ships' },
        { id: 18, name: 'Mineral', description: 'Raw materials for manufacturing' },
        { id: 60, name: 'Armor Module', description: 'Armor tanking modules' },
        { id: 40, name: 'Shield Module', description: 'Shield tanking modules' }
    ];
    
    const infoHtml = commonGroups.map(group => 
        `<li><strong>${group.id}</strong>: ${group.name} - ${group.description}</li>`
    ).join('');
    
    const popup = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: white; border: 2px solid #007bff; border-radius: 8px; 
                    padding: 20px; max-width: 500px; z-index: 10000; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
            <h3>📦 Common EVE Market Groups</h3>
            <ul style="text-align: left;">${infoHtml}</ul>
            <button onclick="this.parentElement.remove()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Close</button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', popup);
}

function updateFilterStatus() {
    const statusDiv = document.getElementById('filterStatus');
    if (!statusDiv || !window.marketFilters) return;
    
    const includeGroups = window.marketFilters.groupIds || [];
    const excludeGroups = window.marketFilters.excludedGroupIds || [];
    const minProfit = window.marketFilters.minProfit || 0;
    const minProfitPercent = window.marketFilters.minProfitPercent || 0;
    
    let status = [];
    
    if (includeGroups.length > 0) {
        status.push(`✅ Include groups: ${includeGroups.join(', ')}`);
    }
    
    if (excludeGroups.length > 0) {
        status.push(`🚫 Exclude groups: ${excludeGroups.join(', ')}`);
    }
    
    if (minProfit > 0) {
        status.push(`💰 Min profit: ${minProfit.toLocaleString()} ISK`);
    }
    
    if (minProfitPercent > 0) {
        status.push(`📈 Min profit %: ${minProfitPercent}%`);
    }
    
    statusDiv.innerHTML = status.length > 0 
        ? `<ul style="margin: 0; padding-left: 20px;">${status.map(s => `<li>${s}</li>`).join('')}</ul>`
        : '<p>No filters active</p>';
}

function triggerRecalculation() {
    // If we have market data loaded, recalculate with new filters
    const buyInput = document.getElementById('buyLocationInput');
    const sellInput = document.getElementById('sellLocationInput');
    
    if (buyInput && sellInput && buyInput.value && sellInput.value && window.recalculateMarketComparison) {
        console.log('🔄 Triggering market comparison recalculation...');
        window.recalculateMarketComparison(buyInput.value, sellInput.value);
    }
}

// Initialize the filter UI when DOM is ready
function initializeGroupFilterUI() {
    console.log('🎨 Initializing group filter UI...');
    
    // Find the comparison results div and insert filter panel before it
    const resultsDiv = document.getElementById('comparisonResults');
    if (resultsDiv) {
        const filterPanel = createGroupFilterUI();
        resultsDiv.insertAdjacentHTML('beforebegin', filterPanel);
        
        // Update status display
        setTimeout(() => {
            updateFilterStatus();
        }, 500);
        
        console.log('✅ Group filter UI initialized');
        return true;
    } else {
        console.warn('⚠️ Could not find comparisonResults div');
        return false;
    }
}

// Export functions to global scope
window.initializeGroupFilterUI = initializeGroupFilterUI;
window.setIncludeGroups = setIncludeGroups;
window.setExcludeGroups = setExcludeGroups;
window.clearGroupFilters = clearGroupFilters;
window.setPreset = setPreset;
window.showGroupInfo = showGroupInfo;
window.updateFilterStatus = updateFilterStatus;
