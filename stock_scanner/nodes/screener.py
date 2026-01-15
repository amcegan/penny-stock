from typing import Dict, Any
from stock_scanner.state import GraphState
from stock_scanner.utils.api_client import FMPClient
from stock_scanner.config import config
from stock_scanner.utils.logger import get_logger

logger = get_logger(__name__)

def screener_node(state: GraphState) -> Dict[str, Any]:
    """
    Step 1: Fetch candidates from FMP Screener.
    """
    client = FMPClient()
    logger.info("Executing Screener Node")
    
    try:
        candidates = client.get_stock_screener(
            min_market_cap=config.DEFAULT_MIN_MARKET_CAP,
            max_market_cap=config.DEFAULT_MAX_MARKET_CAP,
            min_volume=config.DEFAULT_MIN_VOLUME
        )
        logger.info(f"Found {len(candidates)} candidates.")
        return {"candidates": candidates}
    except Exception as e:
        logger.error(f"Screener failed: {e}")
        return {"errors": [f"Screener Error: {str(e)}"]}
