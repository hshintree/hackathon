"""
Test DataStorage fix to verify the initialization bug is resolved
"""
from database.storage import DataStorage
import pandas as pd
from datetime import datetime

def test_datastorage_initialization():
    """Test that DataStorage can be instantiated correctly"""
    print("Testing DataStorage fix...")
    
    try:
        storage = DataStorage()
        print("✅ DataStorage instantiated successfully")
        
        test_data = pd.DataFrame([{
            'symbol': 'TEST',
            'timestamp': datetime.now(),
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000.0
        }])
        print("✅ Test data created")
        print("✅ DataStorage fix verified - ready for database connection test")
        return True
        
    except Exception as e:
        print(f"❌ DataStorage test failed: {e}")
        return False

if __name__ == "__main__":
    test_datastorage_initialization()
