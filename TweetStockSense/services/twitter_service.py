import os
import logging
from textblob import TextBlob
import re
from datetime import datetime, timedelta
import tweepy
from tweepy.errors import TweepyException, HTTPException, TooManyRequests
import urllib.parse
import time
from functools import lru_cache

class TwitterService:
    def __init__(self):
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.last_request_time = 0
        self.request_interval = 60  # Increased to 60 seconds between requests
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.rate_limit_reset = None
        self.client = None
        self.use_cached_only = False
        
        if not self.bearer_token:
            logging.error("No Twitter bearer token found in environment variables")
            return
            
        try:
            self.bearer_token = urllib.parse.unquote(self.bearer_token)
            self.client = tweepy.Client(bearer_token=self.bearer_token)
            
            # Test the connection
            logging.info("Attempting to connect to Twitter API...")
            try:
                # Test the connection
                user = self.client.get_user(username="TwitterDev")
                if user:
                    logging.info("Successfully connected to Twitter API")
                    logging.info(f"Test user data: {user.data.username}")
                else:
                    logging.warning("Twitter API connection test failed: No user data returned")
                    self.client = None
            except TooManyRequests:
                logging.warning("Rate limit hit. Skipping test connection")
                self.rate_limit_reset = time.time() + 60  # Wait 1 minute
            except Exception as e:
                logging.error(f"Error connecting to Twitter API: {str(e)}")
                logging.error(f"Bearer token length: {len(self.bearer_token)}")
                self.client = None
                
        except Exception as e:
            logging.error(f"Error initializing Twitter client: {str(e)}")
            self.client = None
            
        # If client initialization failed, try to use cached data
        if not self.client:
            logging.warning("Twitter client initialization failed. Using cached data only.")
            self.use_cached_only = True
        else:
            self.use_cached_only = False

    def _wait_for_rate_limit(self):
        """Wait until rate limit is reset"""
        if self.rate_limit_reset and time.time() < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time()
            logging.warning(f"Waiting {wait_time:.1f} seconds for rate limit reset...")
            time.sleep(wait_time + 1)  # Add a small buffer

    def _rate_limit_check(self):
        """Check rate limit and wait if necessary"""
        current_time = time.time()
        if current_time - self.last_request_time < self.request_interval:
            wait_time = self.request_interval - (current_time - self.last_request_time)
            logging.warning(f"Rate limit hit. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        self.last_request_time = current_time

    def get_trending_stocks(self):
        """Get trending stocks from Twitter"""
        if self.use_cached_only:
            logging.warning("Using cached data only - Twitter API not available")
            return []
            
        try:
            # Search for stock-related tweets
            query = "$ OR stock OR market OR trading lang:en"
            self._rate_limit_check()
            
            # Get recent tweets
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics'],
                expansions=['author_id']
            )
            
            if not tweets.data:
                logging.warning("No tweets found in search results")
                return []
                
            # Extract stock symbols from tweets
            stock_symbols = {}
            for tweet in tweets.data:
                # Extract symbols using regex
                symbols = re.findall(r'\$\w+', tweet.text)
                for symbol in symbols:
                    symbol = symbol[1:]  # Remove the $ prefix
                    if symbol not in stock_symbols:
                        stock_symbols[symbol] = 0
                    stock_symbols[symbol] += 1
            
            # Sort by frequency and take top 10
            trending_stocks = sorted(
                stock_symbols.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Cache the results
            self.cache['trending_stocks'] = {
                'data': [{
                    'symbol': symbol,
                    'mentions': count
                } for symbol, count in trending_stocks],
                'timestamp': time.time()
            }
            
            return self.cache['trending_stocks']['data']
            
        except TooManyRequests as e:
            logging.warning("Rate limit hit while fetching trending stocks")
            self._wait_for_rate_limit()
            
            # Return cached data if available
            if 'trending_stocks' in self.cache:
                cached_data = self.cache['trending_stocks']
                if time.time() - cached_data['timestamp'] < self.cache_timeout:
                    return cached_data['data']
            
            return []
        except Exception as e:
            logging.error(f"Error fetching trending stocks: {str(e)}", exc_info=True)
            return []

    def get_tweets(self, query, max_results=20):
        """Get tweets with rate limiting"""
        if self.use_cached_only:
            logging.warning("Using cached data only - Twitter API not available")
            return []
            
        try:
            self._rate_limit_check()
            
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                expansions=['author_id']
            )
            
            if not tweets.data:
                logging.warning(f"No tweets found for query: {query}")
                return []
                
            # Process tweets
            processed_tweets = []
            for tweet in tweets.data:
                processed_tweets.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'like_count': tweet.public_metrics['like_count'],
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'reply_count': tweet.public_metrics['reply_count'],
                    'quote_count': tweet.public_metrics['quote_count']
                })
            
            # Cache the results
            cache_key = f"tweets_{hash(query)}"
            self.cache[cache_key] = {
                'data': processed_tweets,
                'timestamp': time.time()
            }
            
            return processed_tweets
            
        except TooManyRequests as e:
            logging.warning("Rate limit hit while fetching tweets")
            self._wait_for_rate_limit()
            
            # Return cached data if available
            cache_key = f"tweets_{hash(query)}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_timeout:
                    return cached_data['data']
            
            return []
        except Exception as e:
            logging.error(f"Error fetching tweets: {str(e)}", exc_info=True)
            return []
    
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
    
    def _rate_limit(self):
        """Ensure we don't hit rate limits by enforcing minimum interval between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            logging.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = current_time
    
    def get_stock_sentiment(self, symbol, max_retries=3):
        """Get sentiment score for a stock symbol with improved rate limiting"""
        try:
            # Check cache
            if self._is_cached(symbol):
                cached_data = self.cache[symbol]
                if 'sentiment' in cached_data:
                    return cached_data['sentiment']
                return None
            
            # Rate limiting
            current_time = time.time()
            if hasattr(self, 'last_request_time'):
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.request_interval:
                    time.sleep(self.request_interval - time_since_last)
            self.last_request_time = current_time
            
            # Get tweets mentioning the stock
            query = f"${symbol} lang:en"
            tweets = []
            
            for attempt in range(max_retries):
                try:
                    # Get tweets with pagination
                    for response in tweepy.Paginator(
                        self.client.search_recent_tweets,
                        query=query,
                        max_results=100,
                        tweet_fields=['text'],
                        expansions=['author_id']
                    ).flatten(limit=100):
                        tweets.append(response.text)
                    
                    break  # Success
                    
                except TooManyRequests as e:
                    logging.warning(f"Rate limit hit for {symbol} (attempt {attempt + 1}/{max_retries})")
                    wait_time = 900 if attempt == max_retries - 1 else 60  # Wait 15 minutes on last attempt, 1 minute otherwise
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        logging.error(f"Failed to get tweets for {symbol} after {max_retries} attempts")
                        return 50  # Neutral sentiment
                        
                except Exception as e:
                    logging.error(f"Error fetching tweets for {symbol}: {e}")
                    if attempt == max_retries - 1:
                        return 50  # Neutral sentiment
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
            
            # Calculate sentiment
            if not tweets:
                return 50  # Neutral sentiment if no tweets found
                
            total_sentiment = 0
            for tweet in tweets:
                # Clean tweet text
                text = re.sub(r'http\S+|www.\S+', '', tweet, flags=re.MULTILINE)
                text = re.sub(r'\$\w+', '', text)  # Remove stock symbols
                text = re.sub(r'@[\w_]+', '', text)  # Remove mentions
                
                # Get sentiment
                blob = TextBlob(text)
                sentiment = blob.sentiment.polarity
                
                # Convert to 0-100 scale
                sentiment_score = (sentiment + 1) * 50
                total_sentiment += sentiment_score
            
            # Cache result
            self.cache[symbol] = {
                'sentiment': total_sentiment / len(tweets),
                'timestamp': time.time()
            }
            
            return total_sentiment / len(tweets)
            
        except Exception as e:
            logging.error(f"Error calculating sentiment for {symbol}: {e}", exc_info=True)
            return 50  # Neutral sentiment on error
    
    def get_overall_sentiment(self):
        """Get overall market sentiment"""
        if not self.client:
            return 50  # Neutral sentiment
            
        try:
            # Check cache first
            cache_key = 'overall_sentiment'
            cached = self._get_cached(cache_key, None)
            if cached is not None:
                return cached
                
            # Get recent market-related tweets
            query = "(stock OR market OR nifty OR sensex) lang:en"
            tweets = []
            
            try:
                # Get tweets with pagination
                for response in tweepy.Paginator(
                    self.client.search_recent_tweets,
                    query=query,
                    max_results=100,
                    tweet_fields=['text'],
                    expansions=['author_id']
                ).flatten(limit=100):
                    tweets.append(response.text)
            except TooManyRequests as e:
                logging.warning("Rate limit hit for overall sentiment")
                return 50  # Neutral sentiment
            except Exception as e:
                logging.error(f"Error fetching market tweets: {e}")
                return 50  # Neutral sentiment
            
            # Calculate sentiment
            if not tweets:
                return 50  # Neutral sentiment if no tweets found
                
            total_sentiment = 0
            for tweet in tweets:
                # Clean tweet text
                text = self.clean_tweet_text(tweet)
                
                # Get sentiment
                blob = TextBlob(text)
                sentiment = blob.sentiment.polarity
                
                # Convert to 0-100 scale
                sentiment_score = (sentiment + 1) * 50
                total_sentiment += sentiment_score
            
            # Calculate average and cache
            avg_sentiment = total_sentiment / len(tweets)
            self._cache_result(cache_key, avg_sentiment)
            
            # Return as float
            return float(avg_sentiment)
            
        except Exception as e:
            logging.error(f"Error calculating overall sentiment: {e}", exc_info=True)
            return 50.0  # Return neutral sentiment as float on error
    
    def _rate_limit(self):
        """Ensure we don't hit rate limits by enforcing minimum interval between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            logging.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @lru_cache(maxsize=128)
    def get_user_tweets(self, username, limit=10):
        """Get tweets for a specific user with caching and rate limiting"""
        try:
            self._rate_limit()
            tweets = self.client.get_users_tweets(
                username=username,
                max_results=limit,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                expansions=['author_id']
            )
            return tweets
        except TooManyRequests as e:
            logging.error("Rate limit hit! Waiting 15 minutes...")
            time.sleep(900)  # Wait 15 minutes
            return self.get_user_tweets(username, limit)
        except Exception as e:
            logging.error(f"Error fetching tweets: {str(e)}")
            return None
    
    def get_stock_sentiment(self, symbol):
        """Get sentiment for a specific stock with rate limiting"""
        if not self.client:
            return 50  # Neutral sentiment
            
        try:
            self._rate_limit()
            
            # Remove .NS suffix for search
            clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
            query = f'${clean_symbol} OR "{clean_symbol}" (stock OR share OR market) -is:retweet lang:en'
            
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=['created_at', 'public_metrics'],
                expansions=['author_id']
            )
            
            if not tweets.data:
                return 50  # Neutral sentiment if no tweets found
                
            # Calculate sentiment
            total_sentiment = 0
            for tweet in tweets.data:
                text = self.clean_tweet_text(tweet.text)
                sentiment = TextBlob(text).sentiment.polarity
                total_sentiment += sentiment
            
            return int((total_sentiment / len(tweets.data) + 1) * 50)
        except TooManyRequests as e:
            logging.error("Rate limit hit! Waiting 15 minutes...")
            time.sleep(900)  # Wait 15 minutes
            return self.get_stock_sentiment(symbol)
        except Exception as e:
            logging.error(f"Error calculating sentiment: {str(e)}")
            return 50  # Return neutral sentiment on error
    
    def clean_tweet_text(self, text):
        """Clean tweet text for sentiment analysis"""
        # Remove URLs, mentions, hashtags
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob"""
        try:
            cleaned_text = self.clean_tweet_text(text)
            blob = TextBlob(cleaned_text)
            
            # TextBlob polarity ranges from -1 (negative) to 1 (positive)
            polarity = blob.sentiment.polarity
            
            # Convert to a 0-100 scale for easier interpretation
            sentiment_score = (polarity + 1) * 50
            
            return {
                'score': round(sentiment_score, 2),
                'polarity': round(polarity, 3),
                'label': 'Positive' if polarity > 0.1 else 'Negative' if polarity < -0.1 else 'Neutral'
            }
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            return {'score': 50, 'polarity': 0, 'label': 'Neutral'}
    
    def calculate_user_reliability(self, author, tweet):
        """Calculate user reliability score based on multiple factors"""
        if not author:
            return 0
        
        score = 0
        
        # Verified account bonus (high weight)
        if getattr(author, 'verified', False):
            score += 40
        
        # Follower count scoring
        follower_count = getattr(author, 'public_metrics', {}).get('followers_count', 0) if hasattr(author, 'public_metrics') else 0
        if follower_count >= 100000:  # 100K+ followers
            score += 30
        elif follower_count >= 50000:  # 50K+ followers
            score += 25
        elif follower_count >= 10000:  # 10K+ followers
            score += 20
        elif follower_count >= 5000:   # 5K+ followers
            score += 15
        elif follower_count >= 1000:   # 1K+ followers
            score += 10
        elif follower_count >= 500:    # 500+ followers
            score += 5
        
        # Tweet engagement scoring
        if hasattr(tweet, 'public_metrics'):
            metrics = tweet.public_metrics
            retweets = metrics.get('retweet_count', 0)
            likes = metrics.get('like_count', 0)
            
            # High engagement tweets are more reliable
            if retweets >= 100 or likes >= 500:
                score += 15
            elif retweets >= 50 or likes >= 200:
                score += 10
            elif retweets >= 10 or likes >= 50:
                score += 5
        
        # Account age and activity (based on username patterns)
        username = getattr(author, 'username', '')
        if username and not any(char.isdigit() for char in username[-4:]):  # No numbers at end suggests older account
            score += 5
        
        # Financial keywords in name (suggests expertise)
        name = getattr(author, 'name', '').lower()
        financial_keywords = ['analyst', 'trader', 'finance', 'investment', 'market', 'equity', 'portfolio', 'fund']
        if any(keyword in name for keyword in financial_keywords):
            score += 10
        
        return min(100, score)  # Cap at 100
    
    def get_financial_tweets(self, stock_symbol=None, limit=20):
        """Get tweets about a specific stock"""
        if not self.client:
            return []
            
        all_tweets = []
        
        try:
            # Search for tweets containing the stock symbol
            query = f"${stock_symbol} lang:en"
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=limit,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                expansions=['author_id']
            )
            
            if not tweets.data:
                logging.warning(f"No tweets found for symbol {stock_symbol}")
                return []

            # Get user data
            users = {user.id: user for user in tweets.includes['users']}

            for tweet in tweets.data:
                user = users[tweet.author_id]
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'username': user.username,
                    'name': user.name,
                    'verified': user.verified,
                    'created_at': tweet.created_at,
                    'sentiment': self.analyze_sentiment(tweet.text),
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'like_count': tweet.public_metrics['like_count'],
                    'reply_count': tweet.public_metrics['reply_count']
                }
                all_tweets.append(tweet_data)

            # Sort by creation time (newest first) and limit
            all_tweets.sort(key=lambda x: x['created_at'], reverse=True)
            return all_tweets[:limit]

        except Exception as e:
            logging.error(f"Error fetching tweets: {e}")
            return []
    
    def get_stock_sentiment(self, symbol):
        """Get sentiment for a specific stock"""
        if not self.client:
            return 50  # Neutral sentiment
            
        try:
            # Remove .NS suffix for search
            clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
            query = f'${clean_symbol} OR "{clean_symbol}" (stock OR share OR market) -is:retweet lang:en'
            
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=10
            ).flatten(limit=50)
            
            total_sentiment = 0
            count = 0
            
            for tweet in tweets:
                sentiment = self.analyze_sentiment(tweet.text)
                total_sentiment += sentiment['score']
                count += 1
            
            if count > 0:
                average_sentiment = total_sentiment / count
                return round(average_sentiment, 2)
            else:
                return 50  # Neutral if no tweets found
                
        except Exception as e:
            logging.error(f"Error getting sentiment for {symbol}: {e}")
            return 50
    
    def get_overall_sentiment(self):
        """Get overall market sentiment"""
        try:
            tweets = self.get_financial_tweets(50)
            if not tweets:
                return {'score': 50, 'label': 'Neutral', 'trend': 'Stable'}
            
            total_sentiment = sum(tweet['sentiment']['score'] for tweet in tweets)
            average_sentiment = total_sentiment / len(tweets)
            
            if average_sentiment > 60:
                label = 'Positive'
                trend = 'Bullish'
            elif average_sentiment < 40:
                label = 'Negative'
                trend = 'Bearish'
            else:
                label = 'Neutral'
                trend = 'Stable'
            
            return {
                'score': round(average_sentiment, 2),
                'label': label,
                'trend': trend,
                'sample_count': len(tweets)
            }
            
        except Exception as e:
            logging.error(f"Error getting overall sentiment: {e}")
            return {'score': 50, 'label': 'Neutral', 'trend': 'Stable'}
