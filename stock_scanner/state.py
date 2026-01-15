from typing import TypedDict, List, Annotated, Dict, Any
from stock_scanner.models import StockResult
import operator

class GraphState(TypedDict):
    """State for the LangGraph workflow."""
    
    # Raw candidates from screener
    candidates: List[dict] 
    
    # Candidates that passed volume check (list of dicts with 'candidate' and 'volume_analysis')
    spiked_stocks: List[Dict[str, Any]]
    
    # Candidates that passed analyst check
    analyst_picks: List[Dict[str, Any]]
    
    # Candidates analyzed for news
    news_analyzed_stocks: List[Dict[str, Any]]
    
    # Final fully processed results
    results: List[StockResult]
    
    # Errors encountered
    errors: List[str]
