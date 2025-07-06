from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_order_blocks(df, depth=5):
    order_blocks = []
    for i in range(depth, len(df) - 3):
        candle = df.iloc[i]
        next_candles = df.iloc[i+1:i+4]
        if candle['Close'] < candle['Open']:
            if next_candles['Close'].mean() > candle['Close'] * 1.01:
                ob = {
                    'timestamp': candle.name.isoformat(),
                    'low': candle['Low'],
                    'high': candle['High']
                }
                order_blocks.append(ob)
    return order_blocks

def scan_stocks(strategy: str):
    tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD']
    results = []
    for ticker in tickers:
        df = yf.download(ticker, period="30d", interval="1h")
        if df.empty:
            continue
        df.dropna(inplace=True)
        if strategy == 'order_block':
            obs = detect_order_blocks(df)
            current_price = df.iloc[-1]['Close']
            for ob in obs:
                if ob['low'] <= current_price <= ob['high']:
                    results.append({
                        'ticker': ticker,
                        'price': round(current_price, 2),
                        'ob_low': round(ob['low'], 2),
                        'ob_high': round(ob['high'], 2),
                        'timestamp': ob['timestamp']
                    })
                    break
    return results

@app.get("/scan")
def scan(strategy: str = Query(default="order_block")):
    return {"strategy": strategy, "results": scan_stocks(strategy)}
