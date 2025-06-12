// Common utility functions and configurations

// API endpoints
const API_ENDPOINTS = {
    dashboard: '/api/dashboard-data',
    stockData: '/api/stock-data',
    trendingTweets: '/api/trending-tweets-data',
    predictions: '/api/predictions-data',
    searchStocks: '/api/search-stocks'
};

// Utility functions
const utils = {
    // Format currency values
    formatCurrency: function(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) {
            return '--';
        }
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    },

    // Format large numbers (for volume, market cap)
    formatLargeNumber: function(value) {
        if (value === null || value === undefined || isNaN(value)) {
            return '--';
        }
        
        if (value >= 1e9) {
            return (value / 1e9).toFixed(2) + 'B';
        } else if (value >= 1e6) {
            return (value / 1e6).toFixed(2) + 'M';
        } else if (value >= 1e3) {
            return (value / 1e3).toFixed(2) + 'K';
        }
        return value.toString();
    },

    // Format percentage values
    formatPercentage: function(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) {
            return '--';
        }
        const sign = value >= 0 ? '+' : '';
        return sign + value.toFixed(decimals) + '%';
    },

    // Get color class based on value (positive/negative)
    getChangeColorClass: function(value) {
        if (value > 0) return 'price-positive';
        if (value < 0) return 'price-negative';
        return 'price-neutral';
    },

    // Get sentiment color class
    getSentimentColorClass: function(score) {
        if (score > 60) return 'sentiment-positive';
        if (score < 40) return 'sentiment-negative';
        return 'sentiment-neutral';
    },

    // Format date
    formatDate: function(dateString) {
        if (!dateString) return '--';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Show loading state
    showLoading: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('d-none');
        }
    },

    // Hide loading state
    hideLoading: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('d-none');
        }
    },

    // Show error state
    showError: function(elementId, message = '') {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('d-none');
            const messageElement = element.querySelector('#error-message');
            if (messageElement && message) {
                messageElement.textContent = message;
            }
        }
    },

    // Hide error state
    hideError: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('d-none');
        }
    },

    // Show content section
    showContent: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('d-none');
            element.classList.add('fade-in');
        }
    },

    // API call wrapper with error handling
    apiCall: async function(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },

    // Debounce function for search
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Chart.js default configuration
Chart.defaults.color = '#6c757d';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.backgroundColor = 'rgba(13, 110, 253, 0.1)';

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            position: 'top'
        },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1
        }
    },
    scales: {
        x: {
            grid: {
                color: 'rgba(255, 255, 255, 0.1)'
            }
        },
        y: {
            grid: {
                color: 'rgba(255, 255, 255, 0.1)'
            }
        }
    }
};

// Global error handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// Initialize tooltips if Bootstrap is available
document.addEventListener('DOMContentLoaded', function() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
