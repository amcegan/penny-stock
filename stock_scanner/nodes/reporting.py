from typing import Dict, Any, List
from stock_scanner.state import GraphState
from stock_scanner.utils.llm_client import get_llm
from stock_scanner.prompts import COMPANY_REPORT_PROMPT, CEO_REPORT_PROMPT
from stock_scanner.models import ReportContent, StockResult, StockCandidate, VolumeAnalysis, AnalystRating, SentimentAnalysis
from stock_scanner.utils.logger import get_logger
from langchain_core.output_parsers import StrOutputParser

logger = get_logger(__name__)

def reporting_node(state: GraphState) -> Dict[str, Any]:
    """
    Step 5: Generate Company & CEO Reports if news is not negative.
    """
    llm = get_llm()
    str_parser = StrOutputParser()
    
    company_chain = COMPANY_REPORT_PROMPT | llm | str_parser
    ceo_chain = CEO_REPORT_PROMPT | llm | str_parser
    
    analyzed_stocks = state.get("news_analyzed_stocks", [])
    final_results = []
    
    logger.info(f"Generating reports for clean stocks...")
    
    for item in analyzed_stocks:
        candidate_data = item['candidate']
        sentiment_data = item.get('news_sentiment', {})
        
        # Parse back to objects for easier access if needed, or use dicts
        is_negative = sentiment_data.get('is_negative', False)
        
        if is_negative:
            logger.info(f"Skipping report for {candidate_data['symbol']} due to negative news.")
            continue
            
        try:
            symbol = candidate_data['symbol']
            company_name = candidate_data.get('companyName')
            
            # 1. Company Report
            logger.info(f"Generating Company Report for {symbol}...")
            # Prepare context
            vol_info = f"Ratio: {item['volume_analysis']['ratio']:.2f}x, AvgVol: {item['volume_analysis']['avg_volume']}"
            upside_info = f"Upside: {item['analyst_rating']['upside_percent']:.1f}%, Target: ${item['analyst_rating']['target_consensus']}"
            
            company_report = company_chain.invoke({
                "company_name": company_name,
                "symbol": symbol,
                "industry": candidate_data.get('industry'),
                "sector": candidate_data.get('sector'),
                "volume_info": vol_info,
                "upside_info": upside_info
            })
            
            # 2. CEO Report
            logger.info(f"Generating CEO Report for {symbol}...")
            ceo_report = ceo_chain.invoke({
                "company_name": company_name,
                "symbol": symbol
            })
            
            report_content = ReportContent(
                company_report=company_report,
                ceo_report=ceo_report
            )
            
            # Assemble Final Result
            result = StockResult(
                candidate=StockCandidate(**candidate_data),
                volume_analysis=VolumeAnalysis(**item['volume_analysis']),
                analyst_rating=AnalystRating(**item['analyst_rating']),
                news_sentiment=SentimentAnalysis(**sentiment_data),
                reports=report_content
            )
            
            final_results.append(result)
            
        except Exception as e:
            logger.error(f"Error generating report for {symbol}: {e}")
            continue
            
    return {"results": final_results}
