import requests
import time
from typing import Optional, Dict, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

from stock_scanner.config import config
from stock_scanner.exceptions import APIError, RateLimitError
from stock_scanner.utils.logger import get_logger

logger = get_logger(__name__)

class FMPClient:
    def __init__(self):
        self.api_key = config.FMP_API_KEY
        self.session = requests.Session()
        
    def _handle_response(self, response: requests.Response) -> Any:
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif response.status_code >= 500:
                raise APIError(f"Server error {response.status_code}: {e}")
            else:
                raise APIError(f"Client error {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def get_json(self, url: str, params: Optional[Dict] = None) -> Any:
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        response = self.session.get(url, params=params, timeout=15)
        return self._handle_response(response)

    def get_stock_screener(self, min_market_cap: int, max_market_cap: int, min_volume: int) -> List[Dict]:
        url = f"{config.FMP_BASE_URL_V3}/stock-screener"
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
        return self.get_json(url, params)

    def get_historical_price(self, symbol: str, days: int = 40) -> Dict:
        url = f"{config.FMP_BASE_URL_V3}/historical-price-full/{symbol}"
        params = {'timeseries': days}
        return self.get_json(url, params)

    def get_price_target(self, symbol: str) -> List[Dict]:
        url = f"{config.FMP_BASE_URL_V4}/price-target-summary"
        params = {'symbol': symbol}
        return self.get_json(url, params)
        
    def get_stock_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        url = f"{config.FMP_BASE_URL_V3}/stock_news"
        params = {'tickers': symbol, 'limit': limit}
        return self.get_json(url, params)
