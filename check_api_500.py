
import sys
import os

# Add local directory to path
sys.path.append(os.getcwd())

try:
    from app.api import api_trading_performance
    print("Import Successful")
    
    # Mocking dependencies if needed, or just running it
    # We need to see if it runs
    res = api_trading_performance(stock_code="005930")
    print("Result:", res)
    
except Exception as e:
    import traceback
    traceback.print_exc()
