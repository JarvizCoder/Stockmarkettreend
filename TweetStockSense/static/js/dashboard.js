// Dashboard page functionality

let marketChart;

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

async function loadDashboardData() {
    utils.showLoading('loading');
    utils.hideError('error-state');
    
    try {
        const data = await utils.apiCall(API_ENDPOINTS.dashboard);
        
        // Update market overview cards
        updateMarketOverview(data);
        
        // Update top stocks table
        updateTopStocks(data.top_stocks);
        
        // Create market chart
        createMarketChart(data);
        
        // Show content sections
        utils.showContent('market-overview');
        utils.showContent('top-stocks-section');
        utils.showContent('chart-section');
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        utils.showError('error-state', error.message);
    } finally {
        utils.hideLoading('loading');
    }
}

function updateMarketOverview(data) {
    // Update Nifty data
    if (data.nifty) {
        document.getElementById('nifty-price').textContent = utils.formatCurrency(data.nifty.price, 0);
        
        const niftyChange = document.getElementById('nifty-change');
        const changeText = utils.formatPercentage(data.nifty.change_percent);
        niftyChange.textContent = changeText;
        niftyChange.className = utils.getChangeColorClass(data.nifty.change);
    }
    
    // Update Sensex data
    if (data.sensex) {
        document.getElementById('sensex-price').textContent = utils.formatCurrency(data.sensex.price, 0);
        
        const sensexChange = document.getElementById('sensex-change');
        const changeText = utils.formatPercentage(data.sensex.change_percent);
        sensexChange.textContent = changeText;
        sensexChange.className = utils.getChangeColorClass(data.sensex.change);
    }
    
    // Update sentiment data
    if (data.sentiment) {
        document.getElementById('sentiment-score').textContent = data.sentiment.score + '/100';
        document.getElementById('sentiment-label').textContent = data.sentiment.label;
        document.getElementById('sentiment-label').className = 'badge ' + utils.getSentimentColorClass(data.sentiment.score);
    }
    
    // Update active stocks count
    document.getElementById('active-stocks').textContent = data.top_stocks ? data.top_stocks.length : 0;
}

function updateTopStocks(stocks) {
    const tableBody = document.getElementById('top-stocks-table');
    tableBody.innerHTML = '';
    
    if (!stocks || stocks.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No stock data available</td></tr>';
        return;
    }
    
    stocks.forEach(stock => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <strong>${stock.symbol.replace('.NS', '')}</strong>
            </td>
            <td class="text-truncate" style="max-width: 200px;">
                ${stock.name}
            </td>
            <td>
                <strong>${utils.formatCurrency(stock.price)}</strong>
            </td>
            <td>
                <span class="${utils.getChangeColorClass(stock.change)}">
                    ${utils.formatCurrency(stock.change)}
                </span>
            </td>
            <td>
                <span class="${utils.getChangeColorClass(stock.change_percent)}">
                    ${utils.formatPercentage(stock.change_percent)}
                </span>
            </td>
            <td>
                ${utils.formatLargeNumber(stock.volume)}
            </td>
        `;
        
        // Add click handler to navigate to market data page
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => {
            window.location.href = `/market-data?symbol=${stock.symbol}`;
        });
        
        tableBody.appendChild(row);
    });
}

function createMarketChart(data) {
    const ctx = document.getElementById('marketChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (marketChart) {
        marketChart.destroy();
    }
    
    // Prepare chart data
    const chartData = prepareChartData(data);
    
    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'NIFTY 50',
                    data: chartData.niftyData,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'SENSEX',
                    data: chartData.sensexData,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            ...chartDefaults,
            scales: {
                x: {
                    ...chartDefaults.scales.x,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    ...chartDefaults.scales.y,
                    title: {
                        display: true,
                        text: 'Price (₹)'
                    }
                }
            },
            plugins: {
                ...chartDefaults.plugins,
                title: {
                    display: true,
                    text: 'Market Index Comparison'
                }
            }
        }
    });
}

function prepareChartData(data) {
    // This is a simplified version - in a real implementation,
    // you would fetch historical data for both indices
    const now = new Date();
    const labels = [];
    const niftyData = [];
    const sensexData = [];
    
    // Generate last 7 days of mock trend data based on current values
    for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
        
        // Mock data with slight variations
        const niftyBase = data.nifty ? data.nifty.price : 18000;
        const sensexBase = data.sensex ? data.sensex.price : 60000;
        
        const variation = (Math.random() - 0.5) * 0.02; // ±1% variation
        niftyData.push(niftyBase * (1 + variation));
        sensexData.push(sensexBase * (1 + variation));
    }
    
    return { labels, niftyData, sensexData };
}

// Auto-refresh data every 5 minutes
setInterval(loadDashboardData, 5 * 60 * 1000);
