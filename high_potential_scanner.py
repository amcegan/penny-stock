import requests
import pandas as pd
import numpy as np
import time
import argparse
import sys
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
API_KEY = os.environ.get("FMP_API_KEY", "ey51zC1guCkrc7I9VbZ3QK4cm6CmeH0V") # Fallback for local testing if not set
BASE_URL = "https://financialmodelingprep.com/api/v3"
V4_BASE_URL = "https://financialmodelingprep.com/api/v4"

class HighPotentialScanner:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    def _get_json(self, url, params=None):
        """Helper to make API calls with rate limiting"""
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # print(f"Error fetching {url}: {e}")
            return None
        finally:
            time.sleep(0.12) # Rate limit (~8 calls/sec max)

    def get_candidates(self, min_market_cap=10_000_000, max_market_cap=2_000_000_000, min_volume=50_000, preferred_sectors=None):
        """Step 1: Get broad list of candidates from screener"""
        print("🔍 Step 1: Fetching candidates from Screener...")
        url = f"{BASE_URL}/stock-screener"
        params = {
            'marketCapMoreThan': min_market_cap,
            'marketCapLowerThan': max_market_cap,
            'volumeMoreThan': min_volume,
            'priceMoreThan': 1,
            'priceLowerThan': 50,
            'isEtf': 'false',
            'isActivelyTrading': 'true',
            'limit': 2000 
        }
        
        data = self._get_json(url, params)
        if not data:
            return []
            
        print(f"    -> Found {len(data)} total candidates.")
        
        # Filter by sector if specified
        if preferred_sectors:
            user_sectors = [s.lower().strip() for s in preferred_sectors.split(',')]
            filtered = []
            for stock in data:
                stock_sector = (stock.get('sector') or '').lower()
                stock_industry = (stock.get('industry') or '').lower()
                
                # Check if matches any preferred sector OR industry keyword
                match = False
                for s in user_sectors:
                    if s in stock_sector or s in stock_industry:
                        match = True
                        break
                if match:
                    filtered.append(stock)
            
            print(f"    -> Filtered to {len(filtered)} stocks in sectors: {preferred_sectors}")
            return filtered
            
        return data

    def check_volume_spike(self, symbol, current_volume):
        """Step 2: Check if current volume is a spike vs 30d average"""
        # Fetch historical for average
        url = f"{BASE_URL}/historical-price-full/{symbol}"
        params = {'timeseries': 40} # Get last 40 days
        
        data = self._get_json(url, params)
        if not data or 'historical' not in data:
            return None
            
        history = data['historical']
        if len(history) < 20: # Not enough data
            return None
            
        # exclude today (first item) for average calculation if it's the current trading day
        # FMP 'historical' usually includes today if market is open/closed today
        # We want to compare Today (current_volume) vs Previous Days Avg
        
        # Use provided current_volume from screener as "Today" (real-time-ish) 
        # OR use the first item of history if screener is lagged. 
        # Screener volume is usually decent. Let's trust the checking method.
        
        volumes = [d['volume'] for d in history if d['volume'] > 0]
        
        # Calculate 30d avg (excluding the most recent day to verify spike against history)
        avg_vol = sum(volumes[1:31]) / len(volumes[1:31]) if len(volumes) > 30 else sum(volumes[1:]) / len(volumes[1:])
        
        if avg_vol == 0:
            return None
            
        ratio = current_volume / avg_vol
        return {
            'avg_volume': avg_vol,
            'ratio': ratio,
            'history': history[:5] # Keep recent history for trend check
        }

    def get_price_target(self, symbol):
        """Step 3: Get Analyst Consensus"""
        url = f"{V4_BASE_URL}/price-target-summary"
        params = {'symbol': symbol}
        
        data = self._get_json(url, params)
        if not data or len(data) == 0:
            return None
            
        return data[0] # Returns dict with targetConsensus, targetHigh, etc.

    def scan(self, sectors=None, volume_threshold=1.5, upside_threshold=20.0):
        # 1. Get Candidates
        candidates = self.get_candidates(preferred_sectors=sectors)
        
        results = []
        print(f"🔍 Step 2: Analyzing {len(candidates)} candidates for Volume Spikes...")
        print("    (This may take a few minutes due to API rate limits)")
        
        for i, stock in enumerate(candidates):
            symbol = stock['symbol']
            curr_vol = stock.get('volume', 0)
            
            if i > 0 and i % 50 == 0:
                print(f"    ... processed {i}/{len(candidates)} stocks ...")
            
            # Check Volume Spike
            vol_data = self.check_volume_spike(symbol, curr_vol)
            
            if not vol_data or vol_data['ratio'] < volume_threshold:
                continue
                
            # print(f"    🚀 Spike Found: {symbol} (Vol: {curr_vol:,}, Ratio: {vol_data['ratio']:.2f}x)")
            
            # Check Price Target (Only for spikes)
            pt_data = self.get_price_target(symbol)
            
            target_price = 0
            upside = 0
            
            if pt_data:
                target_price = pt_data.get('targetConsensus') or pt_data.get('lastMonthAvgPriceTarget') or 0
                curr_price = stock.get('price', 0)
                if curr_price > 0 and target_price > 0:
                    upside = ((target_price - curr_price) / curr_price) * 100
            
            # Filter by Upside
            if upside < upside_threshold:
                # Optional: keep it if user wants to see all spikes, but for "High Potential" we filter
                continue
                
            print(f"    ✅ MATCH: {symbol} | Vol Ratio: {vol_data['ratio']:.1f}x | Upside: +{upside:.0f}%")
            
            results.append({
                'Symbol': symbol,
                'Name': stock.get('companyName'),
                'Sector': stock.get('sector'),
                'Industry': stock.get('industry'),
                'Price': stock.get('price'),
                'Market Cap ($M)': round(stock.get('marketCap', 0) / 1_000_000, 1),
                'Volume': curr_vol,
                'Avg Volume': int(vol_data['avg_volume']),
                'Vol Ratio': round(vol_data['ratio'], 2),
                'Target Price': target_price,
                'Upside %': round(upside, 2)
            })
            
        return results

    def send_email_report(self, df):
        """Send email with results"""
        sender_email = os.environ.get("EMAIL_ADDRESS")
        sender_password = os.environ.get("EMAIL_PASSWORD")
        recipient_email = os.environ.get("EMAIL_RECIPIENT")

        if not all([sender_email, sender_password, recipient_email]):
            print("⚠️ Email credentials not set. Skipping email report.")
            return

        # Create HTML Table
        html_table = df.to_html(index=False, classes='table table-striped', border=1)
        
        # Email Content
        subject = f"🚀 High Potential Stock Scan - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        <html>
          <head>
            <style>
              table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
              th, td {{ text-align: left; padding: 8px; border: 1px solid #ddd; }}
              th {{ background-color: #4CAF50; color: white; }}
              tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
          </head>
          <body>
            <h2>Daily Stock Scan Results</h2>
            <p>Found {len(df)} candidates with Volume Spike > 1.5x and Upside > 20%.</p>
            {html_table}
            <p><em>Generated by High Potential Scanner</em></p>
          </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            # Connect to Gmail SMTP (using SSL)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print("✅ Email report sent successfully!")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

def main():
    parser = argparse.ArgumentParser(description='High Potential Stock Scanner')
    parser.add_argument('--min-gain', type=float, default=20.0, help='Minimum analyst upside percentage (default: 20.0)')
    parser.add_argument('--spike', type=float, default=1.5, help='Minimum volume spike ratio (default: 1.5)')
    
    args = parser.parse_args()
    
    scanner = HighPotentialScanner(API_KEY)
    
    sectors_to_scan = [
        "Basic Materials",
        "Communication Services",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Energy",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Technology",
        "Utilities"
    ]
    
    print("="*80)
    print(" 🚀 HIGH POTENTIAL STOCK SCANNER")
    print("="*80)
    print(f"Config: Spike > {args.spike}x | Upside > {args.min_gain}%")
    print(f"Scanning {len(sectors_to_scan)} sectors...")
    
    all_results = []
    
    for sector in sectors_to_scan:
        print(f"\n📡 Scanning Sector: {sector}...")
        results = scanner.scan(sectors=sector, volume_threshold=args.spike, upside_threshold=args.min_gain)
        
        if results:
            print(f"    ✅ Found {len(results)} matches in {sector}")
            # Optional: Display mini-table for this sector
            df_sector = pd.DataFrame(results)
            df_sector = df_sector.sort_values('Vol Ratio', ascending=False)
            print(df_sector[['Symbol', 'Vol Ratio', 'Upside %', 'Price']].to_string(index=False))
            all_results.extend(results)
        else:
            print(f"    ❌ No matches in {sector}")
            
    if not all_results:
        print("\n❌ No stocks found in any sector matching criteria.")
        return
        
    # Final Consolidation
    df = pd.DataFrame(all_results)
    df = df.sort_values('Vol Ratio', ascending=False)
    
    print("\n" + "="*80)
    print(f"🎯 TOTAL FOUND: {len(df)} HIGH POTENTIAL CANDIDATES")
    print("="*80)
    
    # Display Columns
    cols = ['Symbol', 'Price', 'Vol Ratio', 'Upside %', 'Sector', 'Industry', 'Market Cap ($M)']
    print(df[cols].to_string(index=False))
    
    # Export with Date-Hour-Minute
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f"high_potential_scan_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"\n📄 Consolidated results saved to {filename}")
    
    # Send Email
    if not df.empty:
        print("\n📧 Sending Email Report...")
        scanner.send_email_report(df)

if __name__ == "__main__":
    main()
