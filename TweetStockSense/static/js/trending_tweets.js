// Trending tweets page functionality

// Load trending tweets on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTrendingTweets();
});

async function loadTrendingTweets() {
    utils.showLoading('loading');
    utils.hideError('error-state');
    
    try {
        const data = await utils.apiCall(API_ENDPOINTS.trendingTweets);
        
        if (!data.tweets || data.tweets.length === 0) {
            showEmptyState();
            return;
        }
        
        // Update sentiment overview
        updateSentimentOverview(data.tweets);
        
        // Display tweets
        displayTweets(data.tweets);
        
        // Show content sections
        utils.showContent('sentiment-overview');
        utils.showContent('tweets-container');
        
        // Update last updated time
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
        
    } catch (error) {
        console.error('Failed to load tweets:', error);
        utils.showError('error-state');
    } finally {
        utils.hideLoading('loading');
    }
}

function updateSentimentOverview(tweets) {
    if (!tweets || tweets.length === 0) return;
    
    // Calculate overall sentiment
    const totalSentiment = tweets.reduce((sum, tweet) => sum + tweet.sentiment.score, 0);
    const averageSentiment = totalSentiment / tweets.length;
    
    // Determine trend
    let trend = 'Stable';
    let trendClass = 'text-muted';
    
    if (averageSentiment > 60) {
        trend = 'Bullish';
        trendClass = 'text-success';
    } else if (averageSentiment < 40) {
        trend = 'Bearish';
        trendClass = 'text-danger';
    }
    
    // Update UI
    document.getElementById('overall-sentiment-score').textContent = averageSentiment.toFixed(1);
    
    const sentimentLabel = document.getElementById('overall-sentiment-label');
    sentimentLabel.textContent = averageSentiment > 50 ? 'Positive' : averageSentiment < 50 ? 'Negative' : 'Neutral';
    sentimentLabel.className = 'badge ' + utils.getSentimentColorClass(averageSentiment);
    
    const marketTrend = document.getElementById('market-trend');
    marketTrend.textContent = trend;
    marketTrend.className = 'card-text ' + trendClass;
    
    document.getElementById('tweet-count').textContent = tweets.length;
}

function displayTweets(tweets) {
    const container = document.getElementById('tweets-list');
    container.innerHTML = '';
    
    tweets.forEach((tweet, index) => {
        const tweetElement = createTweetElement(tweet, index);
        container.appendChild(tweetElement);
    });
}

function createTweetElement(tweet, index) {
    const tweetDiv = document.createElement('div');
    tweetDiv.className = 'tweet-card p-3 mb-3 border rounded';
    
    // Add border color based on sentiment
    if (tweet.sentiment.score > 60) {
        tweetDiv.classList.add('border-start-success');
    } else if (tweet.sentiment.score < 40) {
        tweetDiv.classList.add('border-start-danger');
    } else {
        tweetDiv.classList.add('border-start-warning');
    }
    
    tweetDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <div class="d-flex align-items-center">
                <i class="fab fa-twitter text-primary me-2"></i>
                <div>
                    <div class="d-flex align-items-center">
                        <strong class="text-small">${escapeHtml(tweet.name || tweet.username)}</strong>
                        ${tweet.verified ? '<i class="fas fa-check-circle text-primary ms-1" title="Verified Account"></i>' : ''}
                        ${tweet.reliability_score >= 80 ? '<i class="fas fa-star text-warning ms-1" title="High Reliability"></i>' : ''}
                    </div>
                    <small class="text-muted">
                        @${escapeHtml(tweet.username)}
                        ${tweet.follower_count ? ` • ${utils.formatLargeNumber(tweet.follower_count)} followers` : ''}
                        ${tweet.reliability_score ? ` • ${tweet.reliability_score}% reliable` : ''}
                    </small>
                </div>
            </div>
            <div class="d-flex align-items-center gap-2">
                <span class="badge tweet-sentiment ${utils.getSentimentColorClass(tweet.sentiment.score)}">
                    ${tweet.sentiment.label} (${tweet.sentiment.score.toFixed(1)})
                </span>
                <small class="text-muted">${utils.formatDate(tweet.created_at)}</small>
            </div>
        </div>
        
        <p class="mb-2">${escapeHtml(tweet.text)}</p>
        
        <div class="d-flex justify-content-between align-items-center text-muted small">
            <div class="d-flex gap-3">
                <span>
                    <i class="fas fa-retweet me-1"></i>
                    ${utils.formatLargeNumber(tweet.retweet_count || 0)}
                </span>
                <span>
                    <i class="fas fa-heart me-1"></i>
                    ${utils.formatLargeNumber(tweet.like_count || 0)}
                </span>
                <span>
                    <i class="fas fa-reply me-1"></i>
                    ${utils.formatLargeNumber(tweet.reply_count || 0)}
                </span>
            </div>
            <div>
                Impact Score: ${tweet.sentiment.polarity > 0 ? 'Positive' : tweet.sentiment.polarity < 0 ? 'Negative' : 'Neutral'}
            </div>
        </div>
    `;
    
    // Add animation delay
    tweetDiv.style.animationDelay = `${index * 0.1}s`;
    tweetDiv.classList.add('slide-up');
    
    return tweetDiv;
}

function showEmptyState() {
    utils.hideLoading('loading');
    utils.hideError('error-state');
    
    const emptyState = document.getElementById('empty-state');
    if (emptyState) {
        emptyState.classList.remove('d-none');
    }
    
    // Hide other sections
    document.getElementById('sentiment-overview').classList.add('d-none');
    document.getElementById('tweets-container').classList.add('d-none');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-refresh tweets every 10 minutes
setInterval(loadTrendingTweets, 10 * 60 * 1000);
