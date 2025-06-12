import yfinance as yf

# Example: Get Apple stock data
apple = yf.Ticker("AAPL")
print(apple.history(period="1mo"))