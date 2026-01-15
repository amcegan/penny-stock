from typing import Dict, Any, List
import json
from stock_scanner.state import GraphState
from stock_scanner.utils.api_client import FMPClient
from stock_scanner.utils.llm_client import get_llm
from stock_scanner.prompts import SENTIMENT_PROMPT
from stock_scanner.models import SentimentAnalysis, NewsItem
from stock_scanner.utils.logger import get_logger
from langchain_core.output_parsers import JsonOutputParser

logger = get_logger(__name__)

def news_node(state: GraphState) -> Dict[str, Any]:
    """
    Step 4: Check News Sentiment (3 business days).
    """
    client = FMPClient()
    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=SentimentAnalysis)
    chain = SENTIMENT_PROMPT | llm | parser
    
    analyst_picks = state.get("analyst_picks", [])
    analyzed_stocks = []
    
    logger.info(f"Analyzing news for {len(analyst_picks)} picks...")
    
    for item in analyst_picks:
        candidate = item['candidate']
        symbol = candidate.get('symbol')
        company_name = candidate.get('companyName')
        
        try:
            # Get News (last 3-5 days is roughly covered by limit=10 most recent usually)
            # A more robust impl would filter by date.
            news_data = client.get_stock_news(symbol, limit=8)
            
            if not news_data:
                # No news is generally "no bad news"
                sentiment = SentimentAnalysis(is_negative=False, reasoning="No recent news found.", summary="No news.")
            else:
                # Format for LLM
                news_text = ""
                news_items = []
                for n in news_data:
                    news_text += f"- {n.get('title')} ({n.get('publishedDate')})\n  {n.get('text')}\n\n"
                    news_items.append(NewsItem(
                        title=n.get('title'),
                        date=n.get('publishedDate'),
                        text=n.get('text'),
                        url=n.get('url'),
                        source=n.get('site')
                    ))
                
                # Call LLM
                try:
                    res = chain.invoke({
                        "company_name": company_name,
                        "symbol": symbol,
                        "news_context": news_text
                    })
                    # res should be a dict matching SentimentAnalysis
                    sentiment = SentimentAnalysis(**res)
                except Exception as e:
                    logger.error(f"LLM Sentiment Analysis failed for {symbol}: {e}")
                    # Fail safe: assume verify manually? Or assume neutral?
                    # Let's assume neutral but log it.
                    sentiment = SentimentAnalysis(is_negative=False, reasoning=f"LLM Error: {e}", summary="Error analysing news.")

            item['news_sentiment'] = sentiment.model_dump()
            analyzed_stocks.append(item)
            
        except Exception as e:
            logger.error(f"Error processing news for {symbol}: {e}")
            continue
            
    return {"news_analyzed_stocks": analyzed_stocks}
