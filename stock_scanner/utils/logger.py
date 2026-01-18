import logging
import sys
from stock_scanner.config import config

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name. 
    Configures the base 'stock_scanner' logger if it hasn't been configured yet.
    """
    # We configure the 'stock_scanner' base logger so all sub-loggers inherit its handlers.
    base_logger = logging.getLogger("stock_scanner")
    
    if not base_logger.handlers:
        base_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        base_logger.addHandler(ch)
        
        # File Handler
        try:
            fh = logging.FileHandler(config.LOG_FILE)
            fh.setFormatter(formatter)
            base_logger.addHandler(fh)
        except Exception as e:
            # Fallback to console if file handler fails, but still log the error
            print(f"CRITICAL: Failed to initialize FileHandler at {config.LOG_FILE}: {e}")
            
    return logging.getLogger(name)
