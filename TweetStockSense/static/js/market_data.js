// Market data page functionality

let priceChart;
let currentSymbol = '';
let currentTimeframe = '1mo';

// Load market data on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if symbol is provided in URL
    const urlParams = new URLSearchParams(window.location.search);
    const symbol = urlParams.get('symbol');
    
    if (symbol) {
        document.getElementById('stock-search').value = symbol;
        loadStockData(symbol);
    }
    
    // Add search functionality
    const searchInput = document.getElementById('stock-search');
    const debouncedSearch = utils.debounce(performSearch, 300);
    
    searchInput.addEventListener('input', debouncedSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchStocks();
        }
    });
});

async function searchStocks() {
    const searchTerm = document.getElementById('stock-search').value.trim();
    if (!searchTerm) return;
    
    // If it looks like a symbol, load it directly
    if (searchTerm.includes('.NS') || searchTerm.includes('.BO')) {
        loadStockData(searchTerm);
        return;
    }
    
    // Otherwise, search for matches
    performSearch();
}

async function performSearch() {
    const searchTerm = document.getElementById('stock-search').value.trim();
    const resultsContainer = document.getElementById('search-results');
    
    if (!searchTerm) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    try {
        const data = await utils.apiCall(`${API_ENDPOINTS.searchStocks}?q=${encodeURIComponent(searchTerm)}`);
        displaySearchResults(data.stocks);
    } catch (error) {
        console.error('Search failed:', error);
        resultsContainer.innerHTML = '<div class="alert alert-warning">Search failed. Please try again.</div>';
    }
}

function displaySearchResults(stocks) {
    const resultsContainer = document.getElementById('search-results');
    
    if (!stocks || stocks.length === 0) {
        resultsContainer.innerHTML = '<div class="text-muted">No stocks found</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    stocks.forEach(stock => {
        html += `
            <a href="#" class="list-group-item list-group-item-action" onclick="loadStockData('${stock.symbol}')">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${stock.symbol.replace('.NS', '')} - ${stock.name}</h6>
                    <small class="${utils.getChangeColorClass(stock.change_percent)}">
                        ${utils.formatPercentage(stock.change_percent)}
                    </small>
                </div>
                <p class="mb-1">${utils.formatCurrency(stock.price)}</p>
            </a>
        `;
    });
    html += '</div>';
    
    resultsContainer.innerHTML = html;
}

async function loadStockData(symbol) {
    currentSymbol = symbol;
    
    // Clear search results
    document.getElementById('search-results').innerHTML = '';
    
    // Update search input
    document.getElementById('stock-search').value = symbol;
    
    utils.showLoading('loading');
    utils.hideError('error-state');
    
    try {
        const data = await utils.apiCall(`${API_ENDPOINTS.stockData}/${symbol}`);
        
        // Update stock details
        updateStockDetails(data.current);
        
        // Create price chart
        createPriceChart(data.historical, symbol);
        
        // Show content sections
        utils.showContent('stock-details');
        utils.showContent('chart-section');
        
    } catch (error) {
        console.error('Failed to load stock data:', error);
        utils.showError('error-state', `Failed to load data for ${symbol}. Please check the symbol and try again.`);
    } finally {
        utils.hideLoading('loading');
    }
}

function updateStockDetails(stock) {
    if (!stock) return;
    
    // Update title
    document.getElementById('stock-title').textContent = `${stock.symbol.replace('.NS', '')} - ${stock.name}`;
    document.getElementById('last-updated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    
    // Update price information
    document.getElementById('current-price').textContent = utils.formatCurrency(stock.price);
    
    const priceChange = document.getElementById('price-change');
    const changeText = `${utils.formatCurrency(stock.change)} (${utils.formatPercentage(stock.change_percent)})`;
    priceChange.textContent = changeText;
    priceChange.className = utils.getChangeColorClass(stock.change);
    
    // Update other details
    document.getElementById('day-low').textContent = utils.formatCurrency(stock.day_low);
    document.getElementById('day-high').textContent = utils.formatCurrency(stock.day_high);
    document.getElementById('volume').textContent = utils.formatLargeNumber(stock.volume);
    document.getElementById('pe-ratio').textContent = stock.pe_ratio ? stock.pe_ratio.toFixed(2) : 'N/A';
}

function createPriceChart(historicalData, symbol) {
    const ctx = document.getElementById('priceChart');
    if (!ctx || !historicalData) return;
    
    // Destroy existing chart
    if (priceChart) {
        priceChart.destroy();
    }
    
    // Prepare chart data
    const labels = historicalData.map(item => new Date(item.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
    const prices = historicalData.map(item => item.close);
    const volumes = historicalData.map(item => item.volume);
    
    // Determine color based on price trend
    const firstPrice = prices[0];
    const lastPrice = prices[prices.length - 1];
    const trendColor = lastPrice >= firstPrice ? '#198754' : '#dc3545';
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Close Price',
                    data: prices,
                    borderColor: trendColor,
                    backgroundColor: trendColor + '20',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Volume',
                    data: volumes,
                    type: 'bar',
                    backgroundColor: 'rgba(108, 117, 125, 0.3)',
                    borderColor: 'rgba(108, 117, 125, 0.5)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            ...chartDefaults,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    ...chartDefaults.scales.x,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Price (₹)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Volume'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                ...chartDefaults.plugins,
                title: {
                    display: true,
                    text: `${symbol.replace('.NS', '')} - Price & Volume Chart`
                }
            }
        }
    });
}

async function changeTimeframe(timeframe) {
    if (!currentSymbol || currentTimeframe === timeframe) return;
    
    currentTimeframe = timeframe;
    
    // Update active button
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Reload data with new timeframe
    try {
        const data = await utils.apiCall(`${API_ENDPOINTS.stockData}/${currentSymbol}?period=${timeframe}`);
        createPriceChart(data.historical, currentSymbol);
    } catch (error) {
        console.error('Failed to load data for timeframe:', error);
    }
}

function retryLastRequest() {
    if (currentSymbol) {
        loadStockData(currentSymbol);
    }
}
