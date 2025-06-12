import logging
from datetime import datetime, timedelta
import yfinance as yf
from functools import lru_cache
import time

class StockService:
    def __init__(self):
        # Popular Indian stocks with .NS suffix for NSE
        self.indian_stocks = {
            'RELIANCE.NS': 'Reliance Industries',
            'TCS.NS': 'Tata Consultancy Services',
            'HDFCBANK.NS': 'HDFC Bank',
            'INFY.NS': 'Infosys',
            'HINDUNILVR.NS': 'Hindustan Unilever',
            'ITC.NS': 'ITC Limited',
            'SBIN.NS': 'State Bank of India',
            'BHARTIARTL.NS': 'Bharti Airtel',
            'KOTAKBANK.NS': 'Kotak Mahindra Bank',
            'LT.NS': 'Larsen & Toubro',
            'ASIANPAINT.NS': 'Asian Paints',
            'MARUTI.NS': 'Maruti Suzuki',
            'BAJFINANCE.NS': 'Bajaj Finance',
            'HCLTECH.NS': 'HCL Technologies',
            'WIPRO.NS': 'Wipro',
        }
        # Cache settings
        self.cache_timeout = 300  # 5 minutes
        self.last_fetch = {}
        
        # Rate limiting settings
        self.last_request_time = time.time()  # Initialize with current time
        self.request_interval = 1.5  # Minimum 1.5 seconds between requests
        self.rate_limit_reset = None
    
    def _is_cached(self, symbol):
        """Check if data is in cache and not expired"""
        if symbol in self.last_fetch:
            timestamp = self.last_fetch[symbol].get('timestamp', 0)
            if time.time() - timestamp < self.cache_timeout:
                return True
        return False

    def get_market_indices(self):
        """Get market indices data"""
        try:
            indices = {}
            # Use proper Yahoo Finance ticker symbols for Indian indices
            index_symbols = {
                'NIFTY50': '^NSEI',  # NIFTY 50
                'SENSEX': '^BSESN',  # BSE SENSEX
                'NIFTYBANK': '^NSEBANK'  # NIFTY BANK
            }
            
            for index, symbol in index_symbols.items():
                try:
                    data = self.get_stock_data(symbol, retries=5, delay=5)  # Increased retries and delay
                    if data:
                        indices[index] = data
                    else:
                        logging.warning(f"No data fetched for {index}")
                except Exception as e:
                    logging.warning(f"Error fetching {index} data: {str(e)}")
                    continue
            
            return indices if indices else None
        except Exception as e:
            logging.error(f"Error fetching market indices: {str(e)}", exc_info=True)
            return None
            return None

    def get_top_stocks(self):
        """Get data for top Indian stocks"""
        try:
            top_stocks = []
            for symbol, name in self.indian_stocks.items():
                try:
                    data = self.get_stock_data(symbol)
                    if data:
                        top_stocks.append(data)
                except Exception as e:
                    logging.warning(f"Error fetching data for {symbol}: {str(e)}")
            return top_stocks
        except Exception as e:
            logging.error(f"Error fetching top stocks: {str(e)}")
            return []

    def _get_stock_info(self, stock):
        """Safely get stock info with fallbacks"""
        try:
            info = stock.info
            return {
                'name': info.get('longName', ''),
                'marketCap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'trailingPE': info.get('trailingPE', 0)
            }
        except Exception as e:
            logging.warning(f"Error getting stock info: {str(e)}")
            return {}

    def _get_stock_data(self, symbol, hist):
        """Process stock data from historical data"""
        try:
            if hist.empty:
                logging.warning(f"No historical data available for {symbol}")
                return None
                
            # Get the latest data point
            latest = hist.iloc[-1]
            
            # Get today's data
            current_price = latest.get('Close')
            day_high = latest.get('High')
            day_low = latest.get('Low')
            
            # Validate data exists
            if current_price is None or day_high is None or day_low is None:
                logging.warning(f"Missing required data for {symbol}: {latest}")
                return None
                
            # Get previous day's close for change calculation
            prev_close = None
            if len(hist) > 1:
                prev_row = hist.iloc[-2]
                prev_close = prev_row.get('Close')
            
            # Calculate change and percentage change
            change = 0
            change_percent = 0
            if prev_close is not None and isinstance(prev_close, (float, int)):
                try:
                    change = float(current_price) - float(prev_close)
                    change_percent = (change / float(prev_close)) * 100
                except (TypeError, ValueError) as e:
                    logging.warning(f"Error calculating change for {symbol}: {str(e)}")
                    change = 0
                    change_percent = 0
            
            # Get stock info
            stock = yf.Ticker(symbol)
            info = self._get_stock_info(stock)
            
            # Validate info
            if not info:
                info = {}
            
            return {
                'symbol': symbol,
                'name': info.get('name', symbol),
                'price': float(round(current_price, 2)),
                'change': float(round(change, 2)),
                'change_percent': float(round(change_percent, 2)),
                'volume': int(info.get('volume', 0)),
                'market_cap': int(info.get('marketCap', 0)),
                'pe_ratio': float(info.get('trailingPE', 0)),
                'day_high': float(round(day_high, 2)),
                'day_low': float(round(day_low, 2)),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error processing stock data for {symbol}: {str(e)}", exc_info=True)
            return None

    
    @lru_cache(maxsize=128)
    def _get_stock_data(self, symbol, hist):
        """Helper method to process stock data"""
        # Get current price and change
        current_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - previous_price
        change_percent = (change / previous_price * 100) if previous_price != 0 else 0
        
        # Get day high and low
        day_high = hist['High'].iloc[-1]
        day_low = hist['Low'].iloc[-1]
        
        # Get additional info with error handling
        info = self._get_stock_info(hist)
        
        # Validate data
        if pd.isna(current_price) or pd.isna(day_high) or pd.isna(day_low):
            raise ValueError(f"Invalid data for {symbol}")
            
        return {
            'symbol': symbol,
            'name': info['name'],
            'current_price': float(current_price),
            'previous_price': float(previous_price),
            'change': float(change),
            'change_percent': float(change_percent),
            'market_cap': info['marketCap'],
            'volume': info['volume'],
            'trailing_pe': info['trailingPE'],
            'day_high': float(day_high),
            'day_low': float(day_low),
            'timestamp': datetime.now().isoformat()
        }

    def get_stock_data(self, symbol, retries=5, delay=5):
        """Get current stock data with improved error handling and caching"""
        try:
            # Validate input
            if not symbol or not isinstance(symbol, str):
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # Check cache
            if self._is_cached(symbol):
                cached_data = self.last_fetch[symbol]
                if 'data' in cached_data:
                    return cached_data['data']
            
            # Implement rate limiting with longer interval
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.request_interval:  # Minimum 3 seconds between requests
                time.sleep(self.request_interval - time_since_last)
            self.last_request_time = time.time()
            
            # Initialize variables
            current_price = 0.0
            day_high = 0.0
            day_low = 0.0
            info = {}
            change = 0.0
            change_percent = 0.0
            
            # Fetch data with retries
            for attempt in range(retries):
                try:
                    logging.info(f"Attempting to fetch data for {symbol}, attempt {attempt + 1} of {retries}")
                    
                    stock = yf.Ticker(symbol)
                    
                    # Get historical data
                    hist = stock.history(period='2d')
                    if hist.empty:
                        logging.warning(f"No historical data available for {symbol}")
                        raise ValueError(f"No historical data available for {symbol}")
                        
                    # Get latest data point
                    latest = hist.iloc[-1]
                    
                    # Get today's data
                    current_price = float(latest.get('Close', 0.0))
                    day_high = float(latest.get('High', 0.0))
                    day_low = float(latest.get('Low', 0.0))
                    
                    # Get previous day's close for change calculation
                    prev_close = None
                    if len(hist) > 1:
                        prev_row = hist.iloc[-2]
                        prev_close = float(prev_row.get('Close', 0.0))
                    
                    # Calculate change and percentage change
                    if prev_close is not None and prev_close > 0:
                        try:
                            change = current_price - prev_close
                            change_percent = (change / prev_close) * 100
                        except (TypeError, ValueError) as e:
                            logging.warning(f"Error calculating change for {symbol}: {str(e)}")
                            change = 0.0
                            change_percent = 0.0
                    
                    # Get stock info
                    info = self._get_stock_info(stock)
                    
                    # Cache the data
                    self.last_fetch[symbol] = {
                        'data': {
                            'symbol': symbol,
                            'name': info.get('name', symbol),
                            'price': float(round(current_price, 2)),
                            'change': float(round(change, 2)),
                            'change_percent': float(round(change_percent, 2)),
                            'volume': int(info.get('volume', 0)),
                            'market_cap': int(info.get('marketCap', 0)),
                            'pe_ratio': float(info.get('trailingPE', 0)),
                            'day_high': float(round(day_high, 2)),
                            'day_low': float(round(day_low, 2)),
                            'timestamp': datetime.now().isoformat()
                        },
                        'timestamp': time.time()
                    }
                    
                    return self.last_fetch[symbol]['data']
                    
                except Exception as e:
                    if attempt == retries - 1:
                        logging.error(f"Error fetching data for {symbol} after {retries} attempts: {str(e)}", exc_info=True)
                        return None
                    logging.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying...")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    
        except Exception as e:
            logging.error(f"Critical error in get_stock_data for {symbol}: {str(e)}", exc_info=True)
            return None
            
            # Implement rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.request_interval:  # Minimum 1.5 seconds between requests
                time.sleep(self.request_interval - time_since_last)
            self.last_request_time = time.time()

            # Initialize variables
            current_price = 0.0
            day_high = 0.0
            day_low = 0.0
            info = {}
            change = 0.0
            change_percent = 0.0
            
            # Fetch data with retries
            for attempt in range(retries):
                try:
                    logging.info(f"Attempting to fetch data for {symbol}, attempt {attempt + 1} of {retries}")
                    
                    stock = yf.Ticker(symbol)
                    
                    # Get historical data
                    hist = stock.history(period='2d')
                    if hist.empty:
                        logging.warning(f"No historical data available for {symbol}")
                        raise ValueError(f"No historical data available for {symbol}")
                        
                    # Get latest data point
                    latest = hist.iloc[-1]
                    
                    # Get today's data
                    current_price = float(latest.get('Close', 0.0))
                    day_high = float(latest.get('High', 0.0))
                    day_low = float(latest.get('Low', 0.0))
                    
                    # Get previous day's close for change calculation
                    prev_close = None
                    if len(hist) > 1:
                        prev_row = hist.iloc[-2]
                        prev_close = float(prev_row.get('Close', 0.0))
                    
                    # Calculate change and percentage change
                    if prev_close is not None and prev_close > 0:
                        try:
                            change = current_price - prev_close
                            change_percent = (change / prev_close) * 100
                        except (TypeError, ValueError) as e:
                            logging.warning(f"Error calculating change for {symbol}: {str(e)}")
                            change = 0.0
                            change_percent = 0.0
                    
                    # Get stock info
                    info = self._get_stock_info(stock)
                    
                    # Cache the data
                    self.last_fetch[symbol] = {
                        'data': {
                            'symbol': symbol,
                            'name': info.get('name', symbol),
                            'price': float(round(current_price, 2)),
                            'change': float(round(change, 2)),
                            'change_percent': float(round(change_percent, 2)),
                            'volume': int(info.get('volume', 0)),
                            'market_cap': int(info.get('marketCap', 0)),
                            'pe_ratio': float(info.get('trailingPE', 0)),
                            'day_high': float(round(day_high, 2)),
                            'day_low': float(round(day_low, 2)),
                            'timestamp': datetime.now().isoformat()
                        },
                        'timestamp': time.time()
                    }
                    
                    return self.last_fetch[symbol]['data']
                    
                except Exception as e:
                    if attempt == retries - 1:
                        logging.error(f"Error fetching data for {symbol} after {retries} attempts: {str(e)}", exc_info=True)
                        return None
                    logging.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying...")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    
        except Exception as e:
            logging.error(f"Critical error in get_stock_data for {symbol}: {str(e)}", exc_info=True)
            return None

            # Fetch data with retries
            for attempt in range(retries):
                try:
                    yf.set_timeout(timeout)
                    
                    logging.info(f"Attempting to fetch data for {symbol}, attempt {attempt + 1} of {retries}")
                    
                    stock = yf.Ticker(symbol)
                    
                    # Get historical data with timeout
                    hist = stock.history(period='2d', timeout=timeout)
                    if hist.empty:
                        logging.warning(f"No historical data available for {symbol}")
                        raise ValueError(f"No historical data available for {symbol}")
                        
                    data = self._get_stock_data(symbol, hist)
                    
                    # Cache the data
                    self.last_fetch[symbol] = {
                        'data': data,
                        'timestamp': time.time()
                    }
                    
                    return data
                    
                except Exception as e:
                    if attempt == retries - 1:  # Last attempt
                        logging.error(f"Failed to fetch data for {symbol} after {retries} attempts: {str(e)}")
                        raise
                    else:
                        logging.warning(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}, retrying...")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff

            # If we reach here, all retries failed
            raise Exception(f"Failed to fetch data for {symbol} after {retries} attempts")

        except Exception as e:
            # Handle any other unexpected errors
            logging.error(f"Critical error in get_stock_data for {symbol}: {str(e)}")
            raise

    def get_historical_data(self, symbol, period='1mo', retries=3):
        """Get historical stock data with retry mechanism"""
        for attempt in range(retries):
            try:
                yf = get_yf()
                stock = yf.Ticker(symbol)
                hist = stock.history(period=period)
                
                if hist.empty:
                    if attempt == retries - 1:
                        raise ValueError(f"No historical data available for {symbol}")
                    continue
                
                data = []
                for date, row in hist.iterrows():
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': round(row['Open'], 2),
                        'high': round(row['High'], 2),
                        'low': round(row['Low'], 2),
                        'close': round(row['Close'], 2),
                        'volume': int(row['Volume'])
                    })
                
                return data
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Error fetching historical data for {symbol} after {retries} attempts: {e}")
                    raise
                logging.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def get_top_indian_stocks(self):
        """Get data for top Indian stocks"""
        top_stocks = []
        
        for symbol, name in list(self.indian_stocks.items())[:10]:  # Get top 10
            try:
                data = self.get_stock_data(symbol)
                top_stocks.append(data)
            except Exception as e:
                logging.warning(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        return top_stocks
    
    def search_indian_stocks(self, query):
        """Search for Indian stocks by name or symbol"""
        results = []
        query_lower = query.lower()
        
        for symbol, name in self.indian_stocks.items():
            if (query_lower in symbol.lower() or 
                query_lower in name.lower()):
                try:
                    data = self.get_stock_data(symbol)
                    results.append(data)
                except Exception as e:
                    logging.warning(f"Failed to fetch data for {symbol}: {e}")
                    continue
                
                if len(results) >= 10:  # Limit results
                    break
        
        return results
