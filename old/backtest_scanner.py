import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import sys

# Configuration
API_KEY = "ey51zC1guCkrc7I9VbZ3QK4cm6CmeH0V"
BASE_URL = "https://financialmodelingprep.com/api/v3"
V4_BASE_URL = "https://financialmodelingprep.com/api/v4"

# Strategy Parameters
VOLUME_SPIKE_THRESHOLD = 1.5  # Current Vol > 1.5x Avg Vol
UPSIDE_THRESHOLD_PCT = 20.0   # Target > Current Price * 1.2
HOLDING_PERIOD_DAYS = 15      # Check max gain within 3 weeks (15 trading days)
LOOKBACK_DAYS = 180           # Backtest over last 6 months
MIN_AVG_VOLUME = 50000        # Minimum liquidity

def get_symbols_from_csv(filename):
    """Load symbols from the existing CSV file"""
    try:
        df = pd.read_csv(filename)
        return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

def get_historical_prices(symbol):
    """Get daily OHLCV data"""
    url = f"{BASE_URL}/historical-price-full/{symbol}"
    params = {
        'timeseries': LOOKBACK_DAYS + 100, # Extra buffer for rolling avgs
        'apikey': API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data.get('historical', [])
    except Exception as e:
        print(f"Error fetching prices for {symbol}: {e}")
        return []

def get_historical_targets(symbol):
    """Get historical analyst price targets"""
    url = f"{V4_BASE_URL}/price-target"
    params = {
        'symbol': symbol,
        'apikey': API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching targets for {symbol}: {e}")
        return []

def backtest_symbol(symbol, prices, targets):
    """Run backtest for a single symbol"""
    if not prices:
        return []
    
    # improved: create DataFrame strictly
    df = pd.DataFrame(prices)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate Volume Moving Average (30d)
    # We use a shift() because the "spike" detection compares Today's Volume vs Prev 30 days Avg
    # But usually 'rolling' includes current row.
    # To compare Current vs Previous Average: shift the rolling window or exclude current.
    # Approach: Calculate 30d MA, then shift it by 1 so 'vol_ma' at index i is avg of i-30 to i-1.
    df['vol_ma_30'] = df['volume'].rolling(window=30).mean().shift(1)
    
    # Prepare Targets DataFrame
    if targets:
        df_targets = pd.DataFrame(targets)
        # Fix: Convert to datetime, remove timezone, and normalize to midnight
        df_targets['publishedDate'] = pd.to_datetime(df_targets['publishedDate']).dt.tz_localize(None).dt.normalize()
        df_targets = df_targets.sort_values('publishedDate')
    else:
        df_targets = pd.DataFrame()

    signals = []
    
    # Iterate through days (skipping first 30 for MA)
    # We only care about the last LOOKBACK_DAYS
    start_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    df_test = df[df['date'] >= start_date]

    for idx, row in df_test.iterrows():
        # 0. Data Validity Check
        if pd.isna(row['vol_ma_30']) or row['vol_ma_30'] < MIN_AVG_VOLUME:
            continue
            
        # 1. Check Volume Spike
        vol_ratio = row['volume'] / row['vol_ma_30']
        if vol_ratio < VOLUME_SPIKE_THRESHOLD:
            continue
            
        # 2. Check Price Target Upside
        # Find latest target ON or BEFORE this date
        current_target = None
        if not df_targets.empty:
            # unique sorted dates
            past_targets = df_targets[df_targets['publishedDate'] <= row['date']]
            if not past_targets.empty:
                # Get the most recent one
                latest_entry = past_targets.iloc[-1]
                current_target = latest_entry['priceTarget']
        
        if not current_target:
            continue
            
        upside = (current_target - row['close']) / row['close'] * 100
        if upside < UPSIDE_THRESHOLD_PCT:
            continue
            
        # SIGNAL TRIGGERED
        signal_date = row['date']
        entry_price = row['close']
        
        # 3. Simulate Outcome (Next 15 Traidng Days)
        # Look ahead in the dataframe
        future_data = df[df['date'] > signal_date].head(HOLDING_PERIOD_DAYS)
        
        if future_data.empty:
            continue # Can't verify outcome yet
            
        max_price = future_data['high'].max()
        max_gain_pct = (max_price - entry_price) / entry_price * 100
        
        # Also get exit price (close after N days or last available)
        exit_price = future_data.iloc[-1]['close']
        final_return_pct = (exit_price - entry_price) / entry_price * 100
        
        days_held = len(future_data)
        
        signals.append({
            'Symbol': symbol,
            'Date': signal_date.strftime('%Y-%m-%d'),
            'Entry Price': entry_price,
            'Vol Ratio': round(vol_ratio, 2),
            'Target': current_target,
            'Max Price': max_price,
            'Max Gain %': round(max_gain_pct, 2),
            'Final Return %': round(final_return_pct, 2),
            'Days Observed': days_held
        })
        
    return signals

def main():
    print("🚀 Starting Historic Backtest Strategy...")
    print(f"Strategy: Vol Spike > {VOLUME_SPIKE_THRESHOLD}x AND Target Upside > {UPSIDE_THRESHOLD_PCT}%")
    print(f"Holding Period: {HOLDING_PERIOD_DAYS} Trading Days")
    
    symbols = get_symbols_from_csv('small_cap_price_targets_top50.csv')
    if not symbols:
        print("No symbols found in CSV.")
        return

    # Limit for testing/rate-limits
    # FMP Free/Starter tier has rate limits per day/sec
    # We process in small batches
    symbols = symbols[:20] 
    print(f"Testing {len(symbols)} symbols...")
    
    all_signals = []
    
    for i, symbol in enumerate(symbols):
        print(f"Analyzing {symbol} ({i+1}/{len(symbols)})...")
        prices = get_historical_prices(symbol)
        targets = get_historical_targets(symbol)
        
        results = backtest_symbol(symbol, prices, targets)
        if results:
            print(f"  -> Found {len(results)} signals!")
            all_signals.extend(results)
        
        # Rate limit
        time.sleep(0.5)

    if not all_signals:
        print("No signals found in the backtest period.")
        return

    # Analysis
    df_res = pd.DataFrame(all_signals)
    
    # Sort by date
    df_res = df_res.sort_values('Date')
    
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80)
    print(df_res.to_string(index=False))
    
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    
    avg_max_gain = df_res['Max Gain %'].mean()
    avg_final = df_res['Final Return %'].mean()
    win_rate = (df_res['Max Gain %'] > 5.0).mean() * 100 # Stocks that eventually popped > 5%
    
    print(f"Total Signals: {len(df_res)}")
    print(f"Average Max Gain (within 3 weeks): {avg_max_gain:.2f}%")
    print(f"Average Final Return (hold 3 weeks): {avg_final:.2f}%")
    print(f"Win Rate (>5% gain at any point): {win_rate:.0f}%")
    
    # Save to CSV
    df_res.to_csv("backtest_results.csv", index=False)
    print("\nSaved detailed results to backtest_results.csv")

if __name__ == "__main__":
    main()
