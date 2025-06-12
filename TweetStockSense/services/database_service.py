from app import db
from models import Stock, StockPrice, Tweet, Prediction, UserWatchlist, MarketSentiment
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

class DatabaseService:
    def __init__(self):
        pass
    
    def get_or_create_stock(self, symbol, name=None, **kwargs):
        """Get existing stock or create new one"""
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        if not stock:
            stock = Stock(
                symbol=symbol,
                name=name or symbol,
                **kwargs
            )
            db.session.add(stock)
            db.session.commit()
        else:
            # Update existing stock data
            if name:
                stock.name = name
            for key, value in kwargs.items():
                if hasattr(stock, key):
                    setattr(stock, key, value)
            stock.last_updated = datetime.utcnow()
            db.session.commit()
        
        return stock
    
    def save_stock_price(self, stock, price_data):
        """Save historical stock price data"""
        try:
            # Check if this price already exists (avoid duplicates)
            existing = StockPrice.query.filter_by(
                stock_id=stock.id,
                timestamp=price_data.get('timestamp', datetime.utcnow())
            ).first()
            
            if not existing:
                stock_price = StockPrice(
                    stock_id=stock.id,
                    open_price=price_data.get('open'),
                    high_price=price_data.get('high'),
                    low_price=price_data.get('low'),
                    close_price=price_data.get('close'),
                    volume=price_data.get('volume'),
                    price_change=price_data.get('change'),
                    price_change_percent=price_data.get('change_percent'),
                    timestamp=price_data.get('timestamp', datetime.utcnow())
                )
                db.session.add(stock_price)
                db.session.commit()
                
        except Exception as e:
            logging.error(f"Error saving stock price for {stock.symbol}: {e}")
            db.session.rollback()
    
    def save_tweet(self, tweet_data):
        """Save tweet data to database"""
        try:
            # Check if tweet already exists
            existing = Tweet.query.filter_by(tweet_id=tweet_data['id']).first()
            
            if not existing:
                tweet = Tweet(
                    tweet_id=tweet_data['id'],
                    text=tweet_data['text'],
                    username=tweet_data['username'],
                    name=tweet_data.get('name'),
                    verified=tweet_data.get('verified', False),
                    sentiment_score=tweet_data['sentiment']['score'],
                    sentiment_label=tweet_data['sentiment']['label'],
                    sentiment_polarity=tweet_data['sentiment']['polarity'],
                    retweet_count=tweet_data.get('retweet_count', 0),
                    like_count=tweet_data.get('like_count', 0),
                    reply_count=tweet_data.get('reply_count', 0),
                    tweet_created_at=datetime.fromisoformat(tweet_data['created_at'].replace('Z', '+00:00')),
                    created_at=datetime.utcnow()
                )
                db.session.add(tweet)
                db.session.commit()
                return tweet
        except Exception as e:
            logging.error(f"Error saving tweet: {e}")
            db.session.rollback()
        
        return existing
    
    def save_prediction(self, stock, prediction_data):
        """Save prediction data to database"""
        try:
            prediction = Prediction(
                stock_id=stock.id,
                symbol=stock.symbol,
                predicted_price=prediction_data['predicted_price'],
                current_price=prediction_data.get('current_price', 0.0),
                price_change_percent=prediction_data.get('price_change_percent', 0.0),
                sentiment_score=prediction_data.get('sentiment_score', 50.0),
                confidence=prediction_data['confidence'],
                recommendation=prediction_data['recommendation'],
                
                # Technical indicators
                ma_5=prediction_data['technical_indicators'].get('ma_5'),
                ma_10=prediction_data['technical_indicators'].get('ma_10'),
                ma_20=prediction_data['technical_indicators'].get('ma_20'),
                ema_12=prediction_data['technical_indicators'].get('ema_12'),
                ema_26=prediction_data['technical_indicators'].get('ema_26'),
                rsi=prediction_data['technical_indicators'].get('rsi'),
                macd=prediction_data['technical_indicators'].get('macd'),
                macd_signal=prediction_data['technical_indicators'].get('macd_signal'),
                bollinger_upper=prediction_data['technical_indicators'].get('bollinger_upper'),
                bollinger_lower=prediction_data['technical_indicators'].get('bollinger_lower'),
                support_level=prediction_data['technical_indicators'].get('support'),
                resistance_level=prediction_data['technical_indicators'].get('resistance'),
                volatility=prediction_data['technical_indicators'].get('volatility'),
                volume_ratio=prediction_data['technical_indicators'].get('volume_ratio'),
                
                # Signals
                buy_signals=prediction_data.get('signals', {}).get('buy_signals'),
                sell_signals=prediction_data.get('signals', {}).get('sell_signals'),
                net_signal=prediction_data.get('signals', {}).get('net_signal'),
                
                prediction_date=datetime.utcnow()
            )
            
            db.session.add(prediction)
            db.session.commit()
            return prediction
            
        except Exception as e:
            logging.error(f"Error saving prediction for {stock.symbol}: {e}")
            db.session.rollback()
        
        return None
    
    def get_recent_tweets(self, limit=20):
        """Get recent tweets from database"""
        return Tweet.query.order_by(Tweet.created_at.desc()).limit(limit).all()
    
    def get_stock_predictions(self, symbol, limit=10):
        """Get recent predictions for a stock"""
        stock = Stock.query.filter_by(symbol=symbol).first()
        if stock:
            return Prediction.query.filter_by(stock_id=stock.id)\
                .order_by(Prediction.prediction_date.desc())\
                .limit(limit).all()
        return []
    
    def get_prediction_accuracy(self, symbol, days=30):
        """Calculate prediction accuracy for a stock"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        if not stock:
            return None
        
        predictions = Prediction.query.filter(
            Prediction.stock_id == stock.id,
            Prediction.prediction_date >= cutoff_date
        ).all()
        
        if not predictions:
            return None
        
        accurate_predictions = 0
        total_predictions = len(predictions)
        
        for prediction in predictions:
            # Simple accuracy check: if price moved in predicted direction
            predicted_change = prediction.predicted_price - prediction.current_price
            
            # Get actual price after prediction (simplified)
            actual_prices = StockPrice.query.filter(
                StockPrice.stock_id == stock.id,
                StockPrice.timestamp > prediction.prediction_date
            ).first()
            
            if actual_prices:
                actual_change = actual_prices.close_price - prediction.current_price
                
                # Check if prediction direction was correct
                if (predicted_change > 0 and actual_change > 0) or \
                   (predicted_change < 0 and actual_change < 0) or \
                   (abs(predicted_change) < 0.01 and abs(actual_change) < 0.01):
                    accurate_predictions += 1
        
        accuracy = (accurate_predictions / total_predictions) * 100 if total_predictions > 0 else 0
        
        return {
            'accuracy_percent': round(accuracy, 2),
            'total_predictions': total_predictions,
            'accurate_predictions': accurate_predictions,
            'period_days': days
        }
    
    def save_market_sentiment(self, sentiment_data):
        """Save overall market sentiment"""
        try:
            market_sentiment = MarketSentiment(
                overall_score=sentiment_data['score'],
                trend_label=sentiment_data['label'],
                tweet_count=sentiment_data.get('sample_count', 0),
                timestamp=datetime.utcnow()
            )
            
            db.session.add(market_sentiment)
            db.session.commit()
            return market_sentiment
            
        except Exception as e:
            logging.error(f"Error saving market sentiment: {e}")
            db.session.rollback()
        
        return None
    
    def get_market_sentiment_history(self, hours=24):
        """Get market sentiment history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return MarketSentiment.query.filter(
            MarketSentiment.timestamp >= cutoff_time
        ).order_by(MarketSentiment.timestamp.desc()).all()
    
    def get_top_stocks(self, limit=10):
        """Get top performing stocks from database"""
        return Stock.query.order_by(Stock.last_updated.desc()).limit(limit).all()
    
    def cleanup_old_data(self, days=90):
        """Clean up old data to keep database size manageable"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean old stock prices (keep more recent data)
            old_prices = StockPrice.query.filter(
                StockPrice.timestamp < cutoff_date
            ).delete()
            
            # Clean old tweets
            old_tweets = Tweet.query.filter(
                Tweet.created_at < cutoff_date
            ).delete()
            
            # Clean old market sentiment data
            old_sentiment = MarketSentiment.query.filter(
                MarketSentiment.timestamp < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logging.info(f"Cleaned up old data: {old_prices} prices, {old_tweets} tweets, {old_sentiment} sentiment records")
            
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")
            db.session.rollback()