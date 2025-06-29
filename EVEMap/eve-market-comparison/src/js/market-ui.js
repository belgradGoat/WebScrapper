// UI display functions - clean version

function displayComparisonResults(opportunities) {
    const resultsDiv = document.getElementById('comparisonResults');
    
    if (!opportunities || opportunities.length === 0) {
        resultsDiv.innerHTML = '<div class="no-results">No profitable opportunities found</div>';
        return;
    }
    
    let html = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Public Buy</th>
                    <th>Public Sell</th>
                    <th>Private Buy</th>
                    <th>Private Sell</th>
                    <th>Buy from Public</th>
                    <th>Buy from Private</th>
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
        
        const formatProfit = (profit) => {
            if (profit <= 0) return '-';
            return `+${profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        };
        
        html += `
            <tr>
                <td>${opp.itemName || opp.typeId}</td>
                <td>${formatPrice(opp.publicBuyMax)}</td>
                <td>${formatPrice(opp.publicSellMin)}</td>
                <td>${formatPrice(opp.privateBuyMax)}</td>
                <td>${formatPrice(opp.privateSellMin)}</td>
                <td class="${opp.buyFromPublicProfit > 0 ? 'profit' : ''}">${formatProfit(opp.buyFromPublicProfit)}</td>
                <td class="${opp.buyFromPrivateProfit > 0 ? 'profit' : ''}">${formatProfit(opp.buyFromPrivateProfit)}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    resultsDiv.innerHTML = html;
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

// Check login status on page load
const token = localStorage.getItem('eveAccessToken');
if (token) {
    updateUIForLoggedInUser();
}

// Make displayComparisonResults available globally
window.displayComparisonResults = displayComparisonResults;