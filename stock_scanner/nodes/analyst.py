from typing import Dict, Any, List
from stock_scanner.state import GraphState
from stock_scanner.utils.api_client import FMPClient
from stock_scanner.models import AnalystRating
from stock_scanner.config import config
from stock_scanner.utils.logger import get_logger

logger = get_logger(__name__)

def analyst_node(state: GraphState) -> Dict[str, Any]:
    """
    Step 3: Check Analyst Ratings and Upside.
    """
    client = FMPClient()
    spiked_stocks = state.get("spiked_stocks", [])
    valid_picks = []
    
    logger.info(f"Checking analyst ratings for {len(spiked_stocks)} volume spikes...")
    
    for item in spiked_stocks:
        candidate = item['candidate']
        symbol = candidate.get('symbol')
        price = candidate.get('price', 0)
        
        try:
            pt_data_list = client.get_price_target(symbol)
            if not pt_data_list:
                continue
            
            pt_data = pt_data_list[0]
            target_price = pt_data.get('targetConsensus') or pt_data.get('lastMonthAvgPriceTarget') or 0
            
            if price > 0 and target_price > 0:
                upside = ((target_price - price) / price) * 100
                
                if upside >= config.DEFAULT_UPSIDE_THRESHOLD:
                    logger.info(f"High Potential: {symbol} (+{upside:.1f}%)")
                    
                    rating = AnalystRating(
                        symbol=symbol,
                        target_consensus=target_price,
                        upside_percent=upside
                    )
                    
                    # Carry forward previous data
                    new_item = item.copy()
                    new_item['analyst_rating'] = rating.model_dump()
                    valid_picks.append(new_item)
                    
        except Exception as e:
            logger.error(f"Error checking analyst rating for {symbol}: {e}")
            continue
            
    return {"analyst_picks": valid_picks}
