from flask import render_template, jsonify, request
from app import app, db
from models import Stock, StockPrice, Tweet, Prediction
from services.stock_service import StockService
from services.prediction_service import PredictionService
from services.database_service import DatabaseService
import logging
import time

# Initialize services once at the top
stock_service = StockService()
prediction_service = PredictionService()
database_service = DatabaseService()

# Initialize Twitter service with error handling
twitter_service = None
try:
    from services.twitter_service import TwitterService
    twitter_service = TwitterService()
except Exception as e:
    logging.error(f"Error initializing Twitter service: {str(e)}")
    # Create a dummy Twitter service as fallback
    class DummyTwitterService:
        def __init__(self):
            self.client = None
            logging.warning("Using dummy Twitter service")
        
        def get_overall_sentiment(self):
            return 50.0  # Return neutral sentiment
            
        def get_stock_sentiment(self, symbol, max_retries=3):
            return 50.0  # Return neutral sentiment
            
    twitter_service = DummyTwitterService()

# Define routes with decorators
@app.route('/')
def index():
    """Root route that redirects to dashboard"""
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard with overview of market and key indicators"""
    return render_template('dashboard.html')

@app.route('/market-data')
def market_data():
    """Market data page showing real-time stock prices"""
    return render_template('market_data.html')

@app.route('/trending-tweets')
def trending_tweets():
    """Trending tweets page with sentiment analysis"""
    return render_template('trending_tweets.html')

@app.route('/predictions')
def predictions():
    """Stock price predictions page"""
    return render_template('predictions.html')

# API Endpoints
@app.route('/api/dashboard-data')
def get_dashboard_data():
    try:
        # Get market indices
        market_indices = []
        try:
            indices = stock_service.get_market_indices()
            if indices:
                market_indices = [{
                    'symbol': i['symbol'],
                    'name': i['name'],
                    'price': float(i['price']),
                    'change': float(i['change']),
                    'change_percent': float(i['change_percent'])
                } for i in indices]
        except Exception as e:
            logging.error(f"Error fetching market indices: {str(e)}")
            market_indices = []

        # Get top stocks
        top_stocks = []
        try:
            stocks = stock_service.get_top_stocks()
            if stocks:
                top_stocks = [{
                    'symbol': s['symbol'],
                    'name': s['name'],
                    'price': float(s['price']),
                    'change': float(s['change']),
                    'change_percent': float(s['change_percent']),
                    'volume': int(s['volume'])
                } for s in stocks]
        except Exception as e:
            logging.error(f"Error fetching top stocks: {str(e)}")
            top_stocks = []

        # Get market sentiment
        market_sentiment = 50.0  # Default neutral sentiment
        try:
            if twitter_service:
                market_sentiment = float(twitter_service.get_overall_sentiment())
        except Exception as e:
            logging.error(f"Error fetching market sentiment: {str(e)}")
            market_sentiment = 50.0

        # Get trending stocks
        trending_stocks = []
        try:
            if twitter_service:
                trending = twitter_service.get_trending_stocks()
                if trending:
                    trending_stocks = [{'symbol': t['symbol'], 'score': float(t['score'])} for t in trending]
        except Exception as e:
            logging.error(f"Error fetching trending stocks: {str(e)}")
            trending_stocks = []

        return jsonify({
            'success': True,
            'data': {
                'market_indices': market_indices,
                'top_stocks': top_stocks,
                'market_sentiment': market_sentiment,
                'trending_stocks': trending_stocks
            }
        })
    except Exception as e:
        logging.error(f"Error in get_dashboard_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/stock-data/<symbol>')
def get_stock_data(symbol):
    """Get detailed stock data for a specific symbol"""
    try:
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Invalid symbol")
            
        # Get current and historical data
        current_data = stock_service.get_stock_data(symbol)
        historical_data = []
        
        if current_data:
            try:
                historical_data = stock_service.get_historical_data(symbol, period='1mo')
                if not isinstance(historical_data, list):
                    raise ValueError("Invalid historical data format")
            except Exception as e:
                logging.error(f"Error fetching historical data for {symbol}: {str(e)}", exc_info=True)
                historical_data = []
                
        # If we have no data at all, return an error
        if not current_data and not historical_data:
            raise ValueError(f"No data available for {symbol}")
            
        # Return response with proper data structure
        return jsonify({
            'current': current_data or {
                'symbol': symbol,
                'name': symbol,
                'price': 0,
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'market_cap': 0,
                'pe_ratio': 0,
                'day_high': 0,
                'day_low': 0,
                'timestamp': datetime.now().isoformat()
            },
            'historical': historical_data
        })
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {str(e)}", exc_info=True)
        # Return a structured error response
        return jsonify({
            'error': 'Failed to fetch stock data',
            'details': str(e),
            'symbol': symbol
        }), 500

@app.route('/api/trending-tweets-data')
def get_trending_tweets_data():
    """Get trending tweets with sentiment analysis"""
    try:
        # Try to get fresh tweets from Twitter API
        tweets = twitter_service.get_financial_tweets()
        
        # Save tweets to database for future reference
        for tweet_data in tweets:
            database_service.save_tweet(tweet_data)
        
        # If no fresh tweets (due to rate limits), get recent ones from database
        if not tweets:
            recent_tweets = database_service.get_recent_tweets(20)
            tweets = []
            for tweet in recent_tweets:
                tweets.append({
                    'id': tweet.tweet_id,
                    'text': tweet.text,
                    'username': tweet.username,
                    'name': tweet.name,
                    'verified': tweet.verified,
                    'created_at': tweet.tweet_created_at.isoformat() if tweet.tweet_created_at else tweet.created_at.isoformat(),
                    'sentiment': {
                        'score': tweet.sentiment_score,
                        'label': tweet.sentiment_label,
                        'polarity': tweet.sentiment_polarity
                    },
                    'retweet_count': tweet.retweet_count,
                    'like_count': tweet.like_count,
                    'reply_count': tweet.reply_count
                })
        
        return jsonify({'tweets': tweets})
    except Exception as e:
        logging.error(f"Error fetching tweets: {e}")
        return jsonify({'error': 'Failed to fetch tweets'}), 500

@app.route('/api/predictions-data/<symbol>')
def get_predictions_data(symbol):
    """Get price predictions for a stock"""
    try:
        # Validate input
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Invalid symbol")
            
        # Get current stock data
        current_data = stock_service.get_stock_data(symbol)
        if not current_data:
            raise ValueError(f"No data available for {symbol}")
            
        # Validate stock data
        if not isinstance(current_data, dict) or 'price' not in current_data:
            raise ValueError("Invalid stock data format")
            
        # Get or create stock in database
        try:
            stock = database_service.get_or_create_stock(
                symbol=symbol,
                name=current_data.get('name', symbol),
                current_price=current_data.get('price', 0),
                day_high=current_data.get('day_high', 0),
                day_low=current_data.get('day_low', 0),
                pe_ratio=current_data.get('pe_ratio', 0),
                market_cap=current_data.get('market_cap', 0)
            )
        except Exception as e:
            logging.error(f"Error creating stock record for {symbol}: {str(e)}", exc_info=True)
            stock = None
            
        # Get sentiment score with retry
        sentiment_score = 0
        try:
            sentiment_score = twitter_service.get_stock_sentiment(symbol)
            if not isinstance(sentiment_score, (int, float)):
                raise ValueError("Invalid sentiment score")
        except Exception as e:
            logging.error(f"Error getting sentiment for {symbol}: {str(e)}", exc_info=True)
            
        # Generate prediction
        prediction = None
        try:
            prediction = prediction_service.predict_price(symbol, current_data, sentiment_score)
            if not prediction:
                raise ValueError("Prediction generation failed")
                
            # Validate prediction
            if not isinstance(prediction, dict) or 'predicted_price' not in prediction:
                raise ValueError("Invalid prediction format")
                
            # Save prediction to database if we have a stock record
            if stock:
                try:
                    database_service.save_prediction(stock, prediction)
                except Exception as e:
                    logging.error(f"Error saving prediction for {symbol}: {str(e)}", exc_info=True)
                    
            # Prepare response
            response = {
                'symbol': symbol,
                'current_price': current_data.get('price', 0),
                'sentiment_score': sentiment_score,
                'prediction': prediction
            }
            
            return jsonify(response)
            
        except Exception as e:
            logging.error(f"Error generating prediction for {symbol}: {str(e)}", exc_info=True)
            raise
            
    except Exception as e:
        logging.error(f"Error processing prediction request for {symbol}: {str(e)}", exc_info=True)
        # Return a structured error response
        return jsonify({
            'error': 'Failed to generate prediction',
            'details': str(e),
            'symbol': symbol
        }), 500

@app.route('/api/search-stocks')
def search_stocks():
    """Search for Indian stocks"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'stocks': []})
    
    try:
        results = stock_service.search_indian_stocks(query)
        return jsonify({'stocks': results})
    except Exception as e:
        logging.error(f"Error searching stocks: {e}")
        return jsonify({'error': 'Failed to search stocks'}), 500

# New database-powered endpoints

@app.route('/api/prediction-history/<symbol>')
def get_prediction_history(symbol):
    try:
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400

        predictions = database_service.get_prediction_history(symbol)
        if not predictions:
            return jsonify({
                'success': False,
                'error': 'No prediction history found'
            }), 404

        return jsonify({
            'success': True,
            'data': predictions
        })
    except Exception as e:
        logging.error(f"Error in get_prediction_history: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/prediction-accuracy/<symbol>')
def get_prediction_accuracy(symbol):
    try:
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400

        accuracy = database_service.get_prediction_accuracy(symbol)
        if not accuracy:
            return jsonify({
                'success': False,
                'error': 'No accuracy data available'
            }), 404

        return jsonify({
            'success': True,
            'data': accuracy
        })
    except Exception as e:
        logging.error(f"Error in get_prediction_accuracy: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/market-sentiment-history')
def get_market_sentiment_history():
    try:
        history = database_service.get_market_sentiment_history()
        if not history:
            return jsonify({
                'success': False,
                'error': 'No market sentiment history found'
            }), 404

        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        logging.error(f"Error in get_market_sentiment_history: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
