import argparse
import sys
import pandas as pd
from datetime import datetime
from stock_scanner.graph import app
from stock_scanner.config import config
from stock_scanner.utils.logger import get_logger

logger = get_logger("stock_scanner.main")

def main():
    parser = argparse.ArgumentParser(description='High Potential Stock Scanner (LangGraph)')
    parser.add_argument('--full', action='store_true', help='Run full scan (default limits apply)')
    # Add other args if needed to override config, but config is env based mainly.
    
    args = parser.parse_args()
    
    logger.info("Starting Stock Scanner Workflow...")
    
    try:
        # Initial State
        initial_state = {
            "candidates": [],
            "spiked_stocks": [],
            "analyst_picks": [],
            "news_analyzed_stocks": [],
            "results": [],
            "errors": []
        }
        
        # Invoke Graph
        final_state = app.invoke(initial_state)
        
        results = final_state.get("results", [])
        
        if not results:
            logger.info("No high potential candidates found.")
            return
            
        logger.info(f"Scan Complete. Found {len(results)} candidates.")
        
        # Save Results
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        
        # 1. CSV Summary (Basic data)
        csv_data = []
        for r in results:
            csv_data.append({
                "Symbol": r.candidate.symbol,
                "Company": r.candidate.company_name,
                "Price": r.candidate.price,
                "Vol Ratio": f"{r.volume_analysis.ratio:.2f}x",
                "Avg Vol": r.volume_analysis.avg_volume,
                "Upside %": f"{r.analyst_rating.upside_percent:.1f}%",
                "Sentiment": "Negative" if r.news_sentiment.is_negative else "Neutral/Positive"
            })
            
        df = pd.DataFrame(csv_data)
        csv_filename = f"scan_results_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        logger.info(f"Saved CSV summary to {csv_filename}")
        
        # 2. Detailed Markdown Report
        md_filename = f"scan_report_{timestamp}.md"
        with open(md_filename, 'w') as f:
            f.write(f"# High Potential Stock Scan Report - {timestamp}\n\n")
            for r in results:
                f.write(f"## {r.candidate.company_name} ({r.candidate.symbol})\n")
                f.write(f"**Price:** ${r.candidate.price} | **Market Cap:** ${r.candidate.market_cap:,.0f}\n")
                f.write(f"**Volume Spike:** {r.volume_analysis.ratio:.2f}x (Avg: {r.volume_analysis.avg_volume:,})\n")
                f.write(f"**Analyst Upside:** {r.analyst_rating.upside_percent:.1f}% (Target: ${r.analyst_rating.target_consensus})\n\n")
                
                f.write("### News Sentiment\n")
                f.write(f"**Summary:** {r.news_sentiment.summary}\n")
                f.write(f"**Reasoning:** {r.news_sentiment.reasoning}\n\n")
                
                if r.reports:
                    if r.reports.company_report:
                        f.write("### Company Analysis\n")
                        f.write(r.reports.company_report + "\n\n")
                    if r.reports.ceo_report:
                        f.write("### CEO Report\n")
                        f.write(r.reports.ceo_report + "\n\n")
                
                f.write("---\n\n")
                
        logger.info(f"Saved detailed report to {md_filename}")
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
