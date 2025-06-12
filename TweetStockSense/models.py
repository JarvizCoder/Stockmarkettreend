from app import db
from datetime import datetime

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(100))
    market_cap = db.Column(db.Float)
    current_price = db.Column(db.Float)
    day_high = db.Column(db.Float)
    day_low = db.Column(db.Float)
    pe_ratio = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StockPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger)
    price_change = db.Column(db.Float)
    price_change_percent = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref=db.backref('prices', lazy=True, order_by='StockPrice.timestamp.desc()'))

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.String(50), unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(200))
    verified = db.Column(db.Boolean, default=False)
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(20))
    sentiment_polarity = db.Column(db.Float)
    retweet_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    tweet_created_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    price_change_percent = db.Column(db.Float)
    sentiment_score = db.Column(db.Float)
    confidence = db.Column(db.Float)
    recommendation = db.Column(db.String(20))
    
    # Technical indicators
    ma_5 = db.Column(db.Float)
    ma_10 = db.Column(db.Float)
    ma_20 = db.Column(db.Float)
    ema_12 = db.Column(db.Float)
    ema_26 = db.Column(db.Float)
    rsi = db.Column(db.Float)
    macd = db.Column(db.Float)
    macd_signal = db.Column(db.Float)
    bollinger_upper = db.Column(db.Float)
    bollinger_lower = db.Column(db.Float)
    support_level = db.Column(db.Float)
    resistance_level = db.Column(db.Float)
    volatility = db.Column(db.Float)
    volume_ratio = db.Column(db.Float)
    
    # Signal counts
    buy_signals = db.Column(db.Integer)
    sell_signals = db.Column(db.Integer)
    net_signal = db.Column(db.Integer)
    
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref=db.backref('predictions', lazy=True, order_by='Prediction.prediction_date.desc()'))

class UserWatchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_session = db.Column(db.String(100), nullable=False)  # Simple session-based tracking
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref=db.backref('watchers', lazy=True))

class MarketSentiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    overall_score = db.Column(db.Float, nullable=False)
    trend_label = db.Column(db.String(20))
    tweet_count = db.Column(db.Integer)
    positive_tweets = db.Column(db.Integer)
    negative_tweets = db.Column(db.Integer)
    neutral_tweets = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
