from typing import Dict, Any
from stock_scanner.state import GraphState
from stock_scanner.utils.api_client import FMPClient
from stock_scanner.models import VolumeAnalysis, StockCandidate
from stock_scanner.config import config
from stock_scanner.utils.logger import get_logger

logger = get_logger(__name__)

def volume_node(state: GraphState) -> Dict[str, Any]:
    """
    Step 2: Check Volume Spikes.
    """
    client = FMPClient()
    candidates = state.get("candidates", [])
    valid_results = []
    
    logger.info(f"Checking volume for {len(candidates)} candidates...")
    
    for i, item in enumerate(candidates):
        symbol = item.get('symbol')
        current_volume = item.get('volume', 0)
        
        # Simple logging for progress
        if i > 0 and i % 20 == 0:
            logger.info(f"Processed {i}/{len(candidates)} stocks...")
            
        try:
            # Reusing logic: Check Volume Spike
            # Note: In a real "LangGraph" map-reduce, this would be per-node. 
            # Given the constraints and requested structure, iterating in a node is fine for batch processing.
            
            hist_data = client.get_historical_price(symbol)
            if not hist_data or 'historical' not in hist_data:
                continue
                
            history = hist_data['historical']
            if len(history) < 20:
                continue
            
            volumes = [d['volume'] for d in history if d['volume'] > 0]
            
            # Use provided current volume or fallback
            if current_volume == 0 and len(history) > 0:
                current_volume = history[0]['volume']
                
            # Calc 30d avg (excluding today/most recent)
            # Similar logic to original script
            avg_vol = sum(volumes[1:31]) / len(volumes[1:31]) if len(volumes) > 30 else sum(volumes[1:]) / len(volumes[1:])
            
            if avg_vol == 0:
                continue
                
            ratio = current_volume / avg_vol
            
            if ratio >= config.DEFAULT_VOLUME_SPIKE_THRESHOLD:
                logger.info(f"Spike found: {symbol} ({ratio:.2f}x)")
                
                # Construct partial result
                candidate_model = StockCandidate(**item) # Partial validation
                vol_analysis = VolumeAnalysis(
                    symbol=symbol,
                    current_volume=current_volume,
                    avg_volume=int(avg_vol),
                    ratio=ratio,
                    is_spike=True,
                    history_snippet=history[:5]
                )
                
                # We store this temporary structure or append to 'results' but we need to pass it to next steps.
                # Since 'results' in state is List[StockResult], we essentially build the StockResult progressively.
                # However, StockResult requires all fields. 
                # Better strategy: Filter down 'candidates' to 'spiked_candidates' OR 
                # Start creating 'results' (StockResult) with partial data?
                # Let's pass 'spiked_stocks' list of dicts to the next node for simplicity.
                # We can't change GraphState easily mid-flight without defining it.
                # Let's add 'spiked_stocks' to GraphState.
                
                valid_results.append({
                    "candidate": item,
                    "volume_analysis": vol_analysis.model_dump()
                })
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            continue
            
    return {"spiked_stocks": valid_results} 
