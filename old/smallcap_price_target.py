import requests
import pandas as pd
from typing import List, Dict
import time

# Configuration
API_KEY = "ey51zC1guCkrc7I9VbZ3QK4cm6CmeH0V"  # Get your key from https://financialmodelingprep.com/developer/docs/
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Small cap definition (market cap in dollars)
SMALL_CAP_MIN = 300_000_000      # $300M
SMALL_CAP_MAX = 2_000_000_000    # $2B

# IMPORTANT NOTES:
# 1. This script uses individual API calls for each symbol (can be slow)
# 2. For faster processing, Professional/Enterprise users can use the bulk endpoint:
#    https://financialmodelingprep.com/api/v4/price-target-summary-bulk?apikey=YOUR_KEY
# 3. Free tier may have limited access to price target data
# 4. The script limits to 200 symbols by default to avoid excessive API calls

def get_small_cap_stocks() -> List[str]:
    """
    Fetch list of small cap stocks based on market cap criteria
    """
    print("Fetching stock screener data...")
    
    # Get stock screener data with market cap filter
    url = f"{BASE_URL}/stock-screener"
    params = {
        "marketCapMoreThan": SMALL_CAP_MIN,
        "marketCapLowerThan": SMALL_CAP_MAX,
        "limit": 1000,
        "apikey": API_KEY
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching screener data: {response.status_code}")
        return []
    
    data = response.json()
    symbols = [stock['symbol'] for stock in data if stock.get('symbol')]
    
    print(f"Found {len(symbols)} small cap stocks")
    return symbols

def get_price_target_summary(symbols: List[str]) -> Dict:
    """
    Fetch price target summary for multiple symbols
    Returns dict with symbol as key and price target data as value
    Note: This endpoint requires individual calls per symbol
    """
    print("Fetching price target summary data...")
    print("Note: This may take a while as each symbol requires a separate API call")
    
    all_data = {}
    failed_symbols = []
    
    for i, symbol in enumerate(symbols):
        # Use v4 API with price-target-summary endpoint
        url = f"{BASE_URL.replace('v3', 'v4')}/price-target-summary"
        params = {
            "symbol": symbol,
            "apikey": API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # API returns a list with one item
                if data and len(data) > 0:
                    all_data[symbol] = data[0]
            else:
                failed_symbols.append(symbol)
        except Exception as e:
            failed_symbols.append(symbol)
            if len(failed_symbols) <= 5:  # Only print first few errors
                print(f"Error fetching {symbol}: {str(e)}")
        
        # Rate limiting - be respectful to the API
        time.sleep(0.3)
        
        # Progress update every 50 symbols
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1} / {len(symbols)} symbols ({len(all_data)} with targets)")
    
    print(f"\nRetrieved price targets for {len(all_data)} stocks")
    if failed_symbols:
        print(f"Failed to fetch {len(failed_symbols)} symbols")
    
    return all_data

def get_current_quotes(symbols: List[str]) -> Dict:
    """
    Fetch current stock quotes for multiple symbols
    """
    print("Fetching current stock prices...")
    
    batch_size = 100
    all_quotes = {}
    
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        symbol_string = ",".join(batch)
        
        url = f"{BASE_URL}/quote/{symbol_string}"
        params = {"apikey": API_KEY}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            for quote in data:
                if quote.get('symbol'):
                    all_quotes[quote['symbol']] = quote
        
        time.sleep(0.5)
    
    print(f"Retrieved quotes for {len(all_quotes)} stocks")
    return all_quotes

def calculate_upside(current_price: float, target_price: float) -> float:
    """
    Calculate percentage upside from current price to target
    """
    if current_price <= 0:
        return 0
    return ((target_price - current_price) / current_price) * 100

def analyze_small_cap_targets(min_analysts: int = 2, top_n: int = 50):
    """
    Main function to analyze small cap stocks with highest price target upside
    
    Args:
        min_analysts: Minimum number of analysts required (default 2)
        top_n: Number of top stocks to return (default 50)
    """
    # Step 1: Get small cap stocks
    small_cap_symbols = get_small_cap_stocks()
    
    if not small_cap_symbols:
        print("No small cap stocks found")
        return None
    
    # Step 2: Get price targets (limit to first 200 for testing/free tier)
    # Remove this limit if you have a paid plan and want all data
    symbols_to_check = small_cap_symbols #[:200]
    print(f"\nAnalyzing {len(symbols_to_check)} symbols (adjust limit in code for more)")
    
    price_targets = get_price_target_summary(symbols_to_check)
    
    # Filter symbols that have price targets
    symbols_with_targets = list(price_targets.keys())
    
    # Step 3: Get current quotes
    current_quotes = get_current_quotes(symbols_with_targets)
    
    # Step 4: Combine data and calculate upside
    results = []
    
    for symbol in symbols_with_targets:
        target_data = price_targets.get(symbol, {})
        quote_data = current_quotes.get(symbol, {})
        
        # Get relevant data - adjust field names based on actual API response
        target_consensus = target_data.get('targetConsensus') or target_data.get('lastMonthAvgPriceTarget')
        target_high = target_data.get('targetHigh') or target_data.get('lastMonthHighPriceTarget')
        target_low = target_data.get('targetLow') or target_data.get('lastMonthLowPriceTarget')
        
        current_price = quote_data.get('price')
        company_name = quote_data.get('name', 'N/A')
        market_cap = quote_data.get('marketCap', 0)
        
        # Skip if missing critical data
        if not target_consensus or not current_price or current_price <= 0:
            continue
        
        # Calculate upside
        upside_pct = calculate_upside(current_price, target_consensus)
        upside_high_pct = calculate_upside(current_price, target_high) if target_high else None
        
        results.append({
            'Symbol': symbol,
            'Company': company_name,
            'Current Price': round(current_price, 2),
            'Target Price': round(target_consensus, 2),
            'Target High': round(target_high, 2) if target_high else None,
            'Target Low': round(target_low, 2) if target_low else None,
            'Upside %': round(upside_pct, 2),
            'Upside to High %': round(upside_high_pct, 2) if upside_high_pct else None,
            'Market Cap ($M)': round(market_cap / 1_000_000, 1),
        })
    
    # Check if we have any results
    if not results:
        print("\n" + "="*100)
        print("NO RESULTS FOUND")
        print("="*100)
        print("Possible reasons:")
        print("1. Your API key may not have access to price target data")
        print("2. The free tier may have limited access to this endpoint")
        print("3. These stocks may not have analyst price targets")
        print("\nTry:")
        print("- Checking a few symbols manually in the FMP API viewer")
        print("- Upgrading to a paid plan for full access")
        print("- Using different stock symbols")
        return None
    
    # Convert to DataFrame and sort by upside
    df = pd.DataFrame(results)
    df = df.sort_values('Upside %', ascending=False)
    
    # Get top N
    df_top = df.head(top_n)
    
    # Display results
    print("\n" + "="*100)
    print(f"TOP {top_n} SMALL CAP STOCKS BY PRICE TARGET UPSIDE")
    print("="*100)
    print(df_top.to_string(index=False))
    
    # Summary statistics
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    print(f"Total small cap stocks analyzed: {len(small_cap_symbols)}")
    print(f"Stocks with price targets: {len(results)}")
    print(f"Average upside: {df['Upside %'].mean():.2f}%")
    print(f"Median upside: {df['Upside %'].median():.2f}%")
    print(f"Max upside: {df['Upside %'].max():.2f}%")
    
    # Save to CSV files
    print("\n" + "="*100)
    print("EXPORTING RESULTS")
    print("="*100)
    
    # Save full results
    full_output_file = "small_cap_price_targets_full.csv"
    df.to_csv(full_output_file, index=False)
    print(f"✓ Full results ({len(df)} stocks) saved to: {full_output_file}")
    
    # Save top N results
    top_output_file = f"small_cap_price_targets_top{top_n}.csv"
    df_top.to_csv(top_output_file, index=False)
    print(f"✓ Top {top_n} results saved to: {top_output_file}")
    
    print("\nFiles are saved in the current directory and ready to open in Excel or any spreadsheet app.")
    
    return df_top

if __name__ == "__main__":
    # Run the analysis
    print("Starting Small Cap Price Target Analysis")
    print("-" * 100)
    
    # Configure analysis parameters
    MIN_ANALYSTS = 1  # Minimum number of analysts (currently not filtered)
    TOP_N = 50        # Number of top stocks to display
    
    print("\nIMPORTANT NOTES:")
    print("- The script analyzes up to 200 symbols by default (see line ~155 to adjust)")
    print("- Each symbol requires a separate API call (rate-limited to 0.3s per call)")
    print("- Free tier may have limited access to price target data")
    print("- Professional/Enterprise users can modify code to use bulk endpoint for faster processing")
    print("-" * 100)
    
    results = analyze_small_cap_targets(min_analysts=MIN_ANALYSTS, top_n=TOP_N)