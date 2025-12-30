import pandas as pd
import requests
import time
import sys

# Configuration
API_KEY = "ey51zC1guCkrc7I9VbZ3QK4cm6CmeH0V"
BASE_URL = "https://financialmodelingprep.com/api/v3"

def get_symbol_profiles(symbols):
    """Fetch profile data (Sector, Industry) for a list of symbols"""
    profiles = {}
    print(f"Fetching profiles for {len(symbols)} symbols...")
    
    # Process in batches to be safe, though profile endpoint supports multiple
    batch_size = 50
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        symbol_str = ",".join(batch)
        url = f"{BASE_URL}/profile/{symbol_str}?apikey={API_KEY}"
        
        try:
            response = requests.get(url)
            data = response.json()
            for item in data:
                profiles[item['symbol']] = {
                    'sector': item.get('sector', 'Unknown'),
                    'industry': item.get('industry', 'Unknown'),
                    'description': item.get('description', '')
                }
        except Exception as e:
            print(f"Error fetching batch {i}: {e}")
            
    return profiles

def main():
    # 1. Load Backtest Results
    try:
        df = pd.read_csv("backtest_results.csv")
    except FileNotFoundError:
        print("backtest_results.csv not found. Please run backtest first.")
        return

    unique_symbols = df['Symbol'].unique().tolist()
    
    # 2. Get Sector/Industry Data
    profiles = get_symbol_profiles(unique_symbols)
    
    # 3. Enrich Data
    df['Sector'] = df['Symbol'].map(lambda x: profiles.get(x, {}).get('sector', 'Unknown'))
    df['Industry'] = df['Symbol'].map(lambda x: profiles.get(x, {}).get('industry', 'Unknown'))
    
    # 4. Group by Sector
    print("\n" + "="*80)
    print("SECTOR PERFORMANCE")
    print("="*80)
    
    sector_stats = df.groupby('Sector').agg({
        'Symbol': 'count', # Total signals
        'Max Gain %': 'mean',
        'Final Return %': 'mean'
    }).rename(columns={'Symbol': 'Signals'})
    
    # Calculate Win Rate per sector
    sector_win_rate = df.groupby('Sector').apply(lambda x: (x['Max Gain %'] > 5.0).mean() * 100)
    sector_stats['Win Rate %'] = sector_win_rate
    
    print(sector_stats.sort_values('Win Rate %', ascending=False).to_string())
    
    # 5. Group by Industry
    print("\n" + "="*80)
    print("INDUSTRY PERFORMANCE")
    print("="*80)
    
    ind_stats = df.groupby('Industry').agg({
        'Symbol': 'count',
        'Max Gain %': 'mean',
        'Final Return %': 'mean'
    }).rename(columns={'Symbol': 'Signals'})
    
    ind_win_rate = df.groupby('Industry').apply(lambda x: (x['Max Gain %'] > 5.0).mean() * 100)
    ind_stats['Win Rate %'] = ind_win_rate
    
    # Filter for industries with at least 5 signals to be meaningful
    # (Since our sample is small, we might show all but highlight low count)
    print(ind_stats.sort_values('Win Rate %', ascending=False).to_string())

if __name__ == "__main__":
    main()
