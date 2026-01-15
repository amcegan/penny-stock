import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

class PennyStockVolumeScanner:
    def __init__(self, fmp_api_key):
        self.api_key = fmp_api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    def get_low_market_cap_stocks(self, max_market_cap=1000000000, min_volume=50000):
        """Get stocks with market cap under $1B and minimum volume"""
        url = f"{self.base_url}/stock-screener"
        params = {
            'marketCapLowerThan': max_market_cap,
            'volumeMoreThan': min_volume,
            'priceMoreThan': 0.01,  # Penny stocks above $0.01
            'priceLowerThan': 10,   # Under $10
            'limit': 1000,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching screener data: {e}")
            return []
    
    def get_average_volume(self, symbol, days=30):
        """Get average volume for a symbol over specified days"""
        url = f"{self.base_url}/historical-price-full/{symbol}"
        params = {
            'serietype': 'line',
            'timeseries': days,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            historical = data.get("historical", [])
            
            if not historical:
                print(f"No volume data returned for symbol: {symbol}")
                return None
            
            volumes = [day["volume"] for day in historical if "volume" in day and day["volume"] > 0]
            
            if len(volumes) < days:
                print(f"Only {len(volumes)} days of data available for {symbol}")
            
            if not volumes:
                return None
                
            average_volume = sum(volumes) / len(volumes)
            return average_volume
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching average volume for {symbol}: {e}")
            return None
    def get_historical_volume_data(self, symbol, days=90):
        """Get historical volume data for a symbol"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{self.base_url}/historical-price-full/{symbol}"
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('historical', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    def analyze_volume_spike(self, historical_data, spike_multiplier=2.0, recent_days=30):
        """Analyze volume data to identify recent spikes"""
        if len(historical_data) < 60:  # Need enough data for analysis
            return None
            
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Calculate rolling averages
        df['volume_ma_30'] = df['volume'].rolling(window=30, min_periods=20).mean()
        df['volume_ma_60'] = df['volume'].rolling(window=60, min_periods=40).mean()
        
        # Calculate volume percentiles
        df['volume_percentile'] = df['volume'].rolling(window=60, min_periods=40).apply(
            lambda x: (x.iloc[-1] - x.mean()) / x.std() if x.std() > 0 else 0
        )
        
        # Focus on recent data
        recent_data = df.tail(recent_days).copy()
        
        # Identify spikes: volume > spike_multiplier * 60-day average
        recent_data['volume_spike'] = recent_data['volume'] > (recent_data['volume_ma_60'] * spike_multiplier)
        recent_data['spike_ratio'] = recent_data['volume'] / recent_data['volume_ma_60']
        
        # Check if there are any spikes in recent period
        spike_days = recent_data[recent_data['volume_spike']]
        
        if len(spike_days) > 0:
            max_spike = spike_days['spike_ratio'].max()
            max_spike_date = spike_days.loc[spike_days['spike_ratio'].idxmax(), 'date']
            recent_avg_spike = spike_days['spike_ratio'].mean()
            
            return {
                'has_spike': True,
                'max_spike_ratio': max_spike,
                'max_spike_date': max_spike_date.strftime('%Y-%m-%d'),
                'spike_days_count': len(spike_days),
                'avg_spike_ratio': recent_avg_spike,
                'recent_volume_trend': recent_data['volume'].tail(5).mean() / recent_data['volume_ma_60'].iloc[-1]
            }
        
        return {'has_spike': False}
    
    def generate_tradingview_url(self, symbol):
        """Generate TradingView chart URL for a symbol"""
        # Clean symbol for TradingView format
        clean_symbol = symbol.replace('.', '-')
        
        # For OTC stocks, you might need different exchange prefixes
        if any(suffix in symbol.upper() for suffix in ['.OB', '.PK', '.QB']):
            return f"https://www.tradingview.com/chart/?symbol=OTC:{clean_symbol}"
        else:
            return f"https://www.tradingview.com/chart/?symbol={clean_symbol}"
    
    def scan_for_volume_spikes(self, max_market_cap=1000000000, spike_multiplier=2.0, max_stocks=50, 
                              volume_spike_threshold=1.5, min_absolute_volume=100000):
        """Main function to scan for volume spikes"""
        print("🔍 Scanning for penny stocks with volume spikes...")
        
        # Step 1: Get low market cap stocks
        stocks = self.get_low_market_cap_stocks(max_market_cap)
        print(f"📊 Found {len(stocks)} stocks under ${max_market_cap/1000000:.0f}M market cap")
        
        if not stocks:
            print("❌ No stocks found matching criteria")
            return []
        
        # Filter out stocks with very low absolute volume (likely illiquid)
        active_stocks = [stock for stock in stocks if stock.get('volume', 0) >= min_absolute_volume]
        print(f"🎯 Found {len(active_stocks)} stocks with volume >= {min_absolute_volume:,}")
        
        # Sort by current volume (highest first) to prioritize most active stocks
        active_stocks.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
        # Limit the number of stocks to analyze (API rate limiting)
        stocks_to_analyze = active_stocks[:max_stocks]
        print(f"📈 Analyzing top {len(stocks_to_analyze)} most active stocks...")
        
        results = []
        
        for i, stock in enumerate(stocks_to_analyze):
            symbol = stock['symbol']
            current_volume = stock.get('volume', 0)
            
            print(f"📊 Analyzing {symbol} ({i+1}/{len(stocks_to_analyze)}) - Current volume: {current_volume:,}")
            
            # Get 30-day average volume for comparison
            avg_volume = self.get_average_volume(symbol, days=30)
            
            if avg_volume is None or avg_volume == 0:
                print(f"⚠️  Skipping {symbol} - No historical volume data available")
                continue
            
            # Check if current volume is a spike compared to 30-day average
            volume_ratio = current_volume / avg_volume
            
            if volume_ratio >= volume_spike_threshold:
                print(f"🚀 POTENTIAL SPIKE: {symbol} - Current: {current_volume:,} vs 30-day avg: {avg_volume:,.0f} (ratio: {volume_ratio:.2f}x)")
                
                # Get detailed historical data for deeper analysis
                historical_data = self.get_historical_volume_data(symbol)
                
                if historical_data:
                    # Analyze for volume spikes over time
                    spike_analysis = self.analyze_volume_spike(historical_data, spike_multiplier)
                    
                    if spike_analysis and spike_analysis.get('has_spike'):
                        result = {
                            'symbol': symbol,
                            'company_name': stock.get('companyName', 'N/A'),
                            'market_cap': stock.get('marketCap', 0),
                            'price': stock.get('price', 0),
                            'volume': current_volume,
                            'avg_volume_30d': avg_volume,
                            'volume_ratio': volume_ratio,
                            'spike_analysis': spike_analysis,
                            'tradingview_url': self.generate_tradingview_url(symbol)
                        }
                        results.append(result)
                        print(f"✅ CONFIRMED SPIKE: {symbol} - Added to results")
                    else:
                        print(f"❌ {symbol} - Current volume spike but no historical pattern")
                else:
                    print(f"❌ {symbol} - Could not get historical data")
            else:
                print(f"📉 {symbol} - Volume ratio {volume_ratio:.2f}x below threshold")
            
            # Rate limiting - be respectful to the API
            time.sleep(0.2)
        
        return results
    
    def format_results(self, results):
        """Format results in a readable way"""
        if not results:
            print("❌ No volume spikes detected in the analyzed stocks")
            return
        
        print(f"\n🎯 FOUND {len(results)} STOCKS WITH VOLUME SPIKES:\n")
        print("=" * 100)
        
        # Sort by spike ratio
        results.sort(key=lambda x: x['spike_analysis']['max_spike_ratio'], reverse=True)
        
        for i, result in enumerate(results, 1):
            spike = result['spike_analysis']
            print(f"{i}. {result['symbol']} - {result['company_name']}")
            print(f"   💰 Market Cap: ${result['market_cap']:,.0f}")
            print(f"   💵 Price: ${result['price']:.2f}")
            print(f"   📊 Current Volume: {result['volume']:,}")
            print(f"   📈 30-day Avg Volume: {result['avg_volume_30d']:,.0f}")
            print(f"   🔥 Volume Ratio: {result['volume_ratio']:.2f}x")
            print(f"   🚀 Max Historical Spike: {spike['max_spike_ratio']:.2f}x (on {spike['max_spike_date']})")
            print(f"   📊 Spike Days: {spike['spike_days_count']} in last 30 days")
            print(f"   🔗 Chart: {result['tradingview_url']}")
            print("-" * 100)

# Example usage
def main():
    # Replace with your FMP API key
    API_KEY = "YOUR_FMP_API_KEY_HERE"
    
    scanner = PennyStockVolumeScanner(API_KEY)
    
    # Scan for volume spikes
    results = scanner.scan_for_volume_spikes(
        max_market_cap=1000000000,     # $1B max market cap
        spike_multiplier=2.0,          # 2x historical volume spike threshold
        max_stocks=20,                 # Analyze top 20 most active stocks
        volume_spike_threshold=1.5,    # Current volume must be 1.5x+ 30-day average
        min_absolute_volume=100000     # Minimum absolute volume to avoid illiquid stocks
    )
    
    # Format and display results
    scanner.format_results(results)
    
    return results

if __name__ == "__main__":
    main()