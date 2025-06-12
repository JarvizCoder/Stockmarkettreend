// Predictions page functionality

let currentPrediction = null;

// Load predictions functionality on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add enter key support for stock input
    document.getElementById('stock-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            generatePrediction();
        }
    });
});

async function generatePrediction() {
    const stockInput = document.getElementById('stock-input');
    const symbol = stockInput.value.trim().toUpperCase();
    
    if (!symbol) {
        alert('Please enter a stock symbol');
        return;
    }
    
    // Add .NS suffix if not present
    const fullSymbol = symbol.includes('.') ? symbol : symbol + '.NS';
    
    utils.showLoading('loading');
    utils.hideError('error-state');
    
    try {
        const data = await utils.apiCall(`${API_ENDPOINTS.predictions}/${fullSymbol}`);
        
        currentPrediction = data;
        displayPredictionResults(data);
        
        // Show results section
        utils.showContent('prediction-results');
        
    } catch (error) {
        console.error('Failed to generate prediction:', error);
        utils.showError('error-state', error.message);
    } finally {
        utils.hideLoading('loading');
    }
}

function displayPredictionResults(prediction) {
    if (!prediction) return;
    
    // Update price comparison
    document.getElementById('current-price-display').textContent = utils.formatCurrency(prediction.current_price);
    document.getElementById('predicted-price-display').textContent = utils.formatCurrency(prediction.predicted_price);
    
    // Update price change
    const priceChangeElement = document.getElementById('price-change-display');
    const changePercent = ((prediction.predicted_price - prediction.current_price) / prediction.current_price) * 100;
    priceChangeElement.textContent = utils.formatPercentage(changePercent);
    priceChangeElement.className = utils.getChangeColorClass(changePercent);
    
    // Update recommendation
    const recommendationBadge = document.getElementById('recommendation-badge');
    recommendationBadge.textContent = prediction.recommendation;
    recommendationBadge.className = getRecommendationBadgeClass(prediction.recommendation);
    
    // Update confidence
    const confidenceBar = document.getElementById('confidence-bar');
    const confidenceText = document.getElementById('confidence-text');
    confidenceBar.style.width = prediction.confidence + '%';
    confidenceBar.className = 'progress-bar ' + getConfidenceColorClass(prediction.confidence);
    confidenceText.textContent = prediction.confidence.toFixed(1) + '%';
    
    // Update sentiment
    document.getElementById('sentiment-score-display').textContent = prediction.sentiment_score.toFixed(1) + '/100';
    const sentimentLabel = document.getElementById('sentiment-label-display');
    sentimentLabel.textContent = getSentimentLabel(prediction.sentiment_score);
    sentimentLabel.className = utils.getSentimentColorClass(prediction.sentiment_score);
    
    // Update technical analysis
    if (prediction.technical_indicators) {
        const indicators = prediction.technical_indicators;
        
        // Moving Averages
        document.getElementById('ma-5').textContent = utils.formatCurrency(indicators.ma_5);
        document.getElementById('ma-10').textContent = utils.formatCurrency(indicators.ma_10);
        document.getElementById('ma-20').textContent = utils.formatCurrency(indicators.ma_20);
        document.getElementById('ema-12').textContent = utils.formatCurrency(indicators.ema_12);
        document.getElementById('ema-26').textContent = utils.formatCurrency(indicators.ema_26);
        
        // Oscillators & Momentum
        const rsiElement = document.getElementById('rsi');
        const rsiSignalElement = document.getElementById('rsi-signal');
        rsiElement.textContent = indicators.rsi.toFixed(1);
        
        // RSI Signal
        if (indicators.rsi < 30) {
            rsiSignalElement.textContent = 'Oversold';
            rsiSignalElement.className = 'badge bg-success';
        } else if (indicators.rsi > 70) {
            rsiSignalElement.textContent = 'Overbought';
            rsiSignalElement.className = 'badge bg-danger';
        } else {
            rsiSignalElement.textContent = 'Neutral';
            rsiSignalElement.className = 'badge bg-secondary';
        }
        
        // MACD
        document.getElementById('macd').textContent = indicators.macd.toFixed(4);
        document.getElementById('macd-signal').textContent = `Signal: ${indicators.macd_signal.toFixed(4)}`;
        
        // Volatility and Volume
        document.getElementById('volatility').textContent = indicators.volatility.toFixed(2) + '%';
        document.getElementById('volume-ratio').textContent = indicators.volume_ratio.toFixed(2) + 'x';
        
        // Support & Resistance
        document.getElementById('support').textContent = utils.formatCurrency(indicators.support);
        document.getElementById('resistance').textContent = utils.formatCurrency(indicators.resistance);
        document.getElementById('bollinger-upper').textContent = utils.formatCurrency(indicators.bollinger_upper);
        document.getElementById('bollinger-lower').textContent = utils.formatCurrency(indicators.bollinger_lower);
        
        // Trend Analysis
        const shortTrendElement = document.getElementById('trend-short');
        const mediumTrendElement = document.getElementById('trend-medium');
        
        shortTrendElement.textContent = utils.formatPercentage(indicators.trend_short);
        shortTrendElement.className = 'mb-0 fw-bold ' + utils.getChangeColorClass(indicators.trend_short);
        
        mediumTrendElement.textContent = utils.formatPercentage(indicators.trend_medium);
        mediumTrendElement.className = 'mb-0 fw-bold ' + utils.getChangeColorClass(indicators.trend_medium);
    }
    
    // Update signal strength
    if (prediction.signals) {
        document.getElementById('buy-signals').textContent = `${prediction.signals.buy_signals} Buy`;
        document.getElementById('sell-signals').textContent = `${prediction.signals.sell_signals} Sell`;
    }
}

function getRecommendationBadgeClass(recommendation) {
    const baseClass = 'badge fs-4 ';
    
    switch (recommendation.toLowerCase()) {
        case 'strong buy':
            return baseClass + 'bg-success';
        case 'buy':
            return baseClass + 'bg-success';
        case 'hold':
            return baseClass + 'bg-warning';
        case 'sell':
            return baseClass + 'bg-danger';
        case 'strong sell':
            return baseClass + 'bg-danger';
        default:
            return baseClass + 'bg-secondary';
    }
}

function getConfidenceColorClass(confidence) {
    if (confidence >= 80) return 'bg-success';
    if (confidence >= 60) return 'bg-info';
    if (confidence >= 40) return 'bg-warning';
    return 'bg-danger';
}

function getSentimentLabel(score) {
    if (score > 60) return 'Positive';
    if (score < 40) return 'Negative';
    return 'Neutral';
}

// Popular stocks suggestions
const popularStocks = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
    'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS', 'LT.NS',
    'ASIANPAINT.NS', 'MARUTI.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'WIPRO.NS'
];

// Add auto-complete functionality
document.getElementById('stock-input').addEventListener('input', function(e) {
    const value = e.target.value.toUpperCase();
    const datalist = document.getElementById('stock-suggestions');
    
    if (value.length > 0) {
        const matches = popularStocks.filter(stock => 
            stock.startsWith(value) || stock.replace('.NS', '').startsWith(value)
        );
        
        datalist.innerHTML = '';
        matches.forEach(stock => {
            const option = document.createElement('option');
            option.value = stock;
            datalist.appendChild(option);
        });
    }
});
