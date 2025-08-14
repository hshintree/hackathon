"""
Test all data source clients on main branch
"""
import os
import sys
from datetime import datetime, timedelta

def test_alpaca_client():
    """Test Alpaca client"""
    print("📈 Testing Alpaca Client...")
    try:
        from data_sources.alpaca_client import AlpacaClient
        client = AlpacaClient()
        data = client.get_market_data_for_symbol("AAPL", "1d")
        print(f"✅ Alpaca: Retrieved {len(data)} records for AAPL")
        return True
    except Exception as e:
        print(f"❌ Alpaca failed: {e}")
        return False

def test_sec_edgar_client():
    """Test SEC EDGAR client"""
    print("📋 Testing SEC EDGAR Client...")
    try:
        from data_sources.sec_edgar_client import SECEdgarClient
        client = SECEdgarClient()
        filings = client.get_company_filings(forms=["10-K"], limit=5)
        print(f"✅ SEC EDGAR: Retrieved {len(filings)} recent 10-K filings")
        return True
    except Exception as e:
        print(f"❌ SEC EDGAR failed: {e}")
        return False

def test_fred_client():
    """Test FRED client"""
    print("📊 Testing FRED Client...")
    try:
        from data_sources.fred_client import FREDClient
        client = FREDClient()
        data = client.get_series_data(["GDP"])
        print(f"✅ FRED: Retrieved {len(data)} GDP data points")
        return True
    except Exception as e:
        print(f"❌ FRED failed: {e}")
        return False

def test_binance_client():
    """Test Binance client"""
    print("₿ Testing Binance Client...")
    try:
        from data_sources.binance_client import BinanceClient
        client = BinanceClient()
        import asyncio
        data = asyncio.run(client.get_historical_klines("BTCUSDT", "1d", 10))
        print(f"✅ Binance: Retrieved {len(data)} BTCUSDT klines")
        return True
    except Exception as e:
        print(f"❌ Binance failed: {e}")
        return False

def test_modal_integration():
    """Test Modal integration"""
    print("🚀 Testing Modal Integration...")
    try:
        import modal
        print(f"✅ Modal available (version {modal.__version__})")
        
        from modal_app import app
        print("✅ Modal app configuration loaded")
        return True
    except Exception as e:
        print(f"❌ Modal integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 GIGACONTEXT DATA SOURCES TEST")
    print("=" * 50)
    
    results = []
    results.append(test_alpaca_client())
    results.append(test_sec_edgar_client())
    results.append(test_fred_client())
    results.append(test_binance_client())
    results.append(test_modal_integration())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"🎯 Data sources test complete: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All data sources ready for gigacontext collection!")
    else:
        print("⚠️ Some data sources need attention")
