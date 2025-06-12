import logging
import numpy as np
from datetime import datetime, timedelta
from services.stock_service import StockService

class PredictionService:
    def __init__(self):
        self.stock_service = StockService()
        self.min_data_points = 30  # Minimum data points needed for reliable predictions
        self.default_prediction_window = 7  # Default prediction window in days
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def _is_cached(self, key):
        """Check if data is in cache and not expired"""
        if key not in self.cache:
            return False
            
        if 'timestamp' not in self.cache[key]:
            return False
            
        elapsed = (datetime.now() - self.cache[key]['timestamp']).total_seconds()
        return elapsed < self.cache_timeout
    
    def _get_cached(self, key, default=None):
        """Get cached data if available"""
        if self._is_cached(key):
            return self.cache[key]['data']
        return default
    
    def _cache_result(self, key, data):
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def validate_stock_data(self, data):
        """Validate stock data before prediction"""
        if not data or not isinstance(data, dict):
            return {'error': 'Invalid stock data format'}
            
        required_fields = ['price', 'volume', 'change_percent']
        if not all(field in data for field in required_fields):
            return {'error': f'Missing required fields: {required_fields}'}
            
        return True
    
    def get_historical_prices(self, symbol, period='1mo'):
        """Get historical prices with caching"""
        try:
            cache_key = f'prices_{symbol}_{period}'
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached
                
            # Get historical data
            hist = self.stock_service.get_historical_data(symbol, period=period)
            
            if not hist:
                return {'error': f'No historical data available for {symbol}'}
                
            prices = [float(item['close']) for item in hist]
            self._cache_result(cache_key, prices)
            return prices
            
        except Exception as e:
            logging.error(f"Error getting historical prices: {str(e)}")
            return {'error': str(e)}
    
    def calculate_moving_average(self, prices, window=5):
        """Calculate simple moving average with error handling"""
        if not isinstance(prices, (list, tuple)) or len(prices) < window:
            return 0
            
        try:
            return sum(prices[-window:]) / window
        except Exception as e:
            logging.error(f"Error calculating MA: {str(e)}")
            return 0
    
    def calculate_exponential_moving_average(self, prices, window=12):
        """Calculate exponential moving average with error handling"""
        if not isinstance(prices, (list, tuple)) or len(prices) < window:
            return self.calculate_moving_average(prices, len(prices))
        
        try:
            multiplier = 2 / (window + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
        except Exception as e:
            logging.error(f"Error calculating EMA: {str(e)}")
            return 0
    
    def calculate_rsi(self, prices, window=14):
        """Calculate Relative Strength Index with error handling"""
        if not isinstance(prices, (list, tuple)) or len(prices) < window + 1:
            return 50
        
        try:
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [delta if delta > 0 else 0 for delta in deltas]
            losses = [-delta if delta < 0 else 0 for delta in deltas]
            
            avg_gain = sum(gains[-window:]) / window
            avg_loss = sum(losses[-window:]) / window
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logging.error(f"Error calculating RSI: {str(e)}")
            return 50
    
    def calculate_macd(self, prices):
        """Calculate MACD with error handling"""
        if not isinstance(prices, (list, tuple)) or len(prices) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        try:
            ema_12 = self.calculate_exponential_moving_average(prices, 12)
            ema_26 = self.calculate_exponential_moving_average(prices, 26)
            
            macd_line = ema_12 - ema_26
            
            # Simple approximation for signal line (9-period EMA of MACD)
            signal_line = macd_line * 0.2  # Simplified calculation
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except Exception as e:
            logging.error(f"Error calculating MACD: {str(e)}")
            return {'macd': 0, 'signal': 0, 'histogram': 0}
    
    def calculate_bollinger_bands(self, prices, window=20, num_std=2):
        """Calculate Bollinger Bands with error handling"""
        if not isinstance(prices, (list, tuple)) or len(prices) < window:
            return {'upper': 0, 'middle': 0, 'lower': 0}
        
        try:
            ma = self.calculate_moving_average(prices, window)
            std = np.std(prices[-window:])
            
            upper = ma + (std * num_std)
            lower = ma - (std * num_std)
            
            return {
                'upper': upper,
                'middle': ma,
                'lower': lower
            }
        except Exception as e:
            logging.error(f"Error calculating Bollinger Bands: {str(e)}")
            return {'upper': 0, 'middle': 0, 'lower': 0}
    
    def calculate_volatility(self, prices):
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        return np.std(returns) if returns else 0
    
    def calculate_support_resistance(self, prices):
        """Calculate support and resistance levels"""
        if len(prices) < 10:
            return {'support': min(prices) if prices else 0, 'resistance': max(prices) if prices else 0}
        
        # Simple approach: use recent highs and lows
        recent_prices = prices[-20:] if len(prices) >= 20 else prices
        
        # Find local maxima and minima
        highs = []
        lows = []
        
        for i in range(1, len(recent_prices) - 1):
            if recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]:
                highs.append(recent_prices[i])
            elif recent_prices[i] < recent_prices[i-1] and recent_prices[i] < recent_prices[i+1]:
                lows.append(recent_prices[i])
        
        resistance = max(highs) if highs else max(recent_prices)
        support = min(lows) if lows else min(recent_prices)
        
        return {'support': support, 'resistance': resistance}
    
    def predict_price(self, symbol, current_data, sentiment_score):
        """Enhanced stock price prediction using advanced technical analysis and sentiment"""
        try:
            # Validate inputs
            if not symbol or not isinstance(symbol, str):
                raise ValueError("Invalid symbol")
            if not current_data or not isinstance(current_data, dict):
                raise ValueError("Invalid current data")
            if not isinstance(sentiment_score, (int, float)):
                raise ValueError("Invalid sentiment score")
                
            # Get historical data
            hist_data = self.get_historical_prices(symbol)
            if not hist_data or len(hist_data) < self.min_data_points:
                raise ValueError(f"Not enough historical data for {symbol}")
                
            prices = [float(d['Close']) for d in hist_data]
            
            # Calculate technical indicators
            ma = self.calculate_moving_average(prices)
            macd = self.calculate_macd(prices)
            rsi = self.calculate_rsi(prices)
            bb = self.calculate_bollinger_bands(prices)
            vol = self.calculate_volatility(prices)
            
            # Calculate prediction factors
            trend_factor = (ma - prices[-1]) / prices[-1] * 100
            momentum_factor = macd['histogram']
            volatility_factor = vol * 100
            sentiment_factor = sentiment_score
            
            # Weighted prediction
            prediction = current_data['price'] * (1 + 
                (trend_factor * 0.3) +
                (momentum_factor * 0.2) +
                (volatility_factor * 0.1) +
                (sentiment_factor * 0.4)
            )
            
            confidence_factors = {
                'volatility': max(0, 40 - (volatility * 2000)),  # Lower volatility = higher confidence
                'data_quality': min(len(historical_data) / 30, 1) * 30,
                'rsi_confidence': 20 - abs(rsi - 50) / 2.5,  # RSI near 50 = more confidence
                'volume_confidence': min(volume_ratio * 10, 20),
                'sentiment_strength': abs(sentiment_factor) * 10
            }
            
            confidence = min(95, max(20, sum(confidence_factors.values())))
            
            # Generate enhanced recommendation
            price_change_percent = ((predicted_price - current_price) / current_price) * 100
            
            # Multi-factor recommendation system
            buy_signals = 0
            sell_signals = 0
            
            # Trend signals
            if short_trend > 0.02: buy_signals += 2
            elif short_trend < -0.02: sell_signals += 2
            
            # Technical indicator signals
            if rsi < 30: buy_signals += 1
            elif rsi > 70: sell_signals += 1
            
            if current_price < bollinger['lower']: buy_signals += 1
            elif current_price > bollinger['upper']: sell_signals += 1
            
            if ma_5 > ma_10 > ma_20: buy_signals += 1
            elif ma_5 < ma_10 < ma_20: sell_signals += 1
            
            # Sentiment signals
            if sentiment_score > 65: buy_signals += 1
            elif sentiment_score < 35: sell_signals += 1
            
            # Final recommendation
            signal_difference = buy_signals - sell_signals
            if signal_difference >= 3:
                recommendation = "Strong Buy"
            elif signal_difference >= 1:
                recommendation = "Buy"
            elif signal_difference <= -3:
                recommendation = "Strong Sell"
            elif signal_difference <= -1:
                recommendation = "Sell"
            else:
                recommendation = "Hold"
            
            return {
                'predicted_price': float(round(predicted_price, 2)),
                'current_price': float(round(current_price, 2)),
                'confidence': float(round(confidence, 1)),
                'recommendation': recommendation,
                'price_change_percent': float(round(price_change_percent, 2)),
                'sentiment_score': float(sentiment_score),
                'technical_indicators': {
                    'ma_5': float(round(ma_5, 2)),
                    'ma_10': float(round(ma_10, 2)),
                    'ma_20': float(round(ma_20, 2)),
                    'ema_12': float(round(ema_12, 2)),
                    'ema_26': float(round(ema_26, 2)),
                    'rsi': float(round(rsi, 2)),
                    'macd': float(round(macd['macd'], 4)),
                    'macd_signal': float(round(macd['signal'], 4)),
                    'bollinger_upper': float(round(bollinger['upper'], 2)),
                    'bollinger_lower': float(round(bollinger['lower'], 2)),
                    'support': float(round(support_resistance['support'], 2)),
                    'resistance': float(round(support_resistance['resistance'], 2)),
                    'volatility': float(round(volatility * 100, 2)),
                    'trend_short': float(round(short_trend * 100, 2)),
                    'trend_medium': float(round(medium_trend * 100, 2)),
                    'volume_ratio': float(round(volume_ratio, 2))
                },
                'signals': {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'net_signal': signal_difference
                }
            }
            
        except Exception as e:
            logging.error(f"Error predicting price for {symbol}: {e}")
            raise
    
    def batch_predict(self, symbols):
        """Generate predictions for multiple stocks"""
        predictions = []
        
        for symbol in symbols:
            try:
                current_data = self.stock_service.get_stock_data(symbol)
                # For batch predictions, use neutral sentiment if not specified
                prediction = self.predict_price(symbol, current_data, 50)
                prediction['symbol'] = symbol
                prediction['current_price'] = current_data['price']
                predictions.append(prediction)
            except Exception as e:
                logging.warning(f"Failed to generate prediction for {symbol}: {e}")
                continue
        
        return predictions
