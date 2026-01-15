class StockScannerException(Exception):
    """Base exception for the stock scanner application."""
    pass

class APIError(StockScannerException):
    """Raised when an external API fails."""
    pass

class ConfigurationError(StockScannerException):
    """Raised when configuration is invalid."""
    pass

class ValidationError(StockScannerException):
    """Raised when data validation fails."""
    pass

class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass
