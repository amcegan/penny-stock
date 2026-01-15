from typing import List, Optional
from pydantic import BaseModel, Field

class StockCandidate(BaseModel):
    """Represents a stock candidate from the initial screener."""
    symbol: str
    company_name: Optional[str] = Field(None, alias='companyName')
    market_cap: Optional[float] = Field(None, alias='marketCap')
    sector: Optional[str] = None
    industry: Optional[str] = None
    price: Optional[float] = None
    volume: Optional[int] = None

class VolumeAnalysis(BaseModel):
    """Result of volume spike analysis."""
    symbol: str
    current_volume: int
    avg_volume: int
    ratio: float
    is_spike: bool
    history_snippet: List[dict] = Field(default_factory=list)

class AnalystRating(BaseModel):
    """Analyst rating and price target data."""
    symbol: str
    target_consensus: Optional[float] = None
    upside_percent: Optional[float] = None

class NewsItem(BaseModel):
    """Represents a news item."""
    title: str
    date: str
    text: str
    source: Optional[str] = None
    url: Optional[str] = None
    
class SentimentAnalysis(BaseModel):
    """Sentiment analysis result."""
    is_negative: bool
    reasoning: str
    summary: str

class ReportContent(BaseModel):
    """Content for the final report."""
    company_report: Optional[str] = None
    ceo_report: Optional[str] = None

class StockResult(BaseModel):
    """Final aggregated result for a stock."""
    candidate: StockCandidate
    volume_analysis: Optional[VolumeAnalysis] = None
    analyst_rating: Optional[AnalystRating] = None
    news_sentiment: Optional[SentimentAnalysis] = None
    reports: Optional[ReportContent] = None
