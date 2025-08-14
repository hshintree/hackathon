"""
Test the complete data ingestion pipeline with all data sources
"""
import os
import sys
from datetime import datetime, timedelta

def test_data_sources():
    """Test all data source clients"""
    print("🧪 Testing Data Source Clients...")
    
    try:
        from data_sources.alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        data = alpaca.get_market_data_for_symbol("AAPL", "1d")
        print(f"✅ Alpaca: Retrieved {len(data)} records for AAPL")
    except Exception as e:
        print(f"❌ Alpaca failed: {e}")
    
    try:
        from data_sources.sec_edgar_client import SECEdgarClient
        sec = SECEdgarClient()
        filings = sec.get_company_filings(forms=["10-K"], limit=5)
        print(f"✅ SEC EDGAR: Retrieved {len(filings)} recent 10-K filings")
    except Exception as e:
        print(f"❌ SEC EDGAR failed: {e}")
    
    try:
        from data_sources.fred_client import FREDClient
        fred = FREDClient()
        data = fred.get_series_data(["GDP"])
        print(f"✅ FRED: Retrieved {len(data)} GDP data points")
    except Exception as e:
        print(f"❌ FRED failed: {e}")
    
    try:
        from data_sources.binance_client import BinanceClient
        binance = BinanceClient()
        import asyncio
        data = asyncio.run(binance.get_historical_klines("BTCUSDT", "1d", 10))
        print(f"✅ Binance: Retrieved {len(data)} BTCUSDT klines")
    except Exception as e:
        print(f"❌ Binance failed: {e}")

def test_database_schema():
    """Test database schema creation"""
    print("\n🗄️ Testing Database Schema...")
    
    try:
        from database.schema import create_database_engine, create_tables, get_database_url
        
        db_url = get_database_url()
        print(f"Database URL: {db_url}")
        
        engine = create_database_engine()
        print("✅ Database engine created")
        
        create_tables(engine)
        print("✅ Database tables created successfully")
        
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            print("✅ Database connection test successful")
            
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")

def test_modal_integration():
    """Test Modal integration"""
    print("\n🚀 Testing Modal Integration...")
    
    try:
        import modal
        print(f"✅ Modal available (version {modal.__version__})")
        
        from modal_app import app
        print("✅ Modal app configuration loaded")
        
    except Exception as e:
        print(f"❌ Modal integration failed: {e}")

if __name__ == "__main__":
    print("🔍 GIGACONTEXT DATA PIPELINE TEST")
    print("=" * 50)
    
    test_data_sources()
    test_database_schema()
    test_modal_integration()
    
    print("\n" + "=" * 50)
    print("🎯 Pipeline test complete!")
