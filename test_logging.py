from stock_scanner.utils.logger import get_logger
import os

logger = get_logger("test_logger")
logger.info("Test log message")

if os.path.exists("daily_scan.log"):
    print("SUCCESS: daily_scan.log created.")
else:
    print("FAILURE: daily_scan.log NOT created.")
