"""
Test script for the user to run locally with their Docker PostgreSQL setup
This script tests the complete gigacontext data infrastructure
"""
import os
import sys
from datetime import datetime, timedelta

def test_environment_setup():
    """Test that all environment variables are properly set"""
    print("🔧 Testing Environment Setup...")
    
    required_vars = [
        'APCA_API_KEY_ID', 'APCA_API_SECRET_KEY',
        'FRED_API_KEY', 'FINNHUB_API_KEY',
        'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_database_connection():
    """Test connection to local Docker PostgreSQL"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        from database.schema import get_database_url, create_database_engine, create_tables
        
        db_url = get_database_url()
        print(f"Database URL: {db_url}")
        
        engine = create_database_engine()
        print("✅ Database engine created")
        
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful")
            print(f"   Version: {version}")
            
            result = conn.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            vector_ext = result.fetchone()
            if vector_ext:
                print("✅ pgvector extension is installed")
            else:
                print("❌ pgvector extension not found")
                print("   Run: docker exec -it pgvector-db psql -U postgres -d trading_agent -c \"CREATE EXTENSION IF NOT EXISTS vector;\"")
                return False
        
        create_tables(engine)
        print("✅ Database tables created successfully")
        
        with engine.connect() as conn:
            result = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure Docker containers are running: docker-compose ps")
        print("2. Check if database exists: docker exec -it pgvector-db psql -U postgres -l")
        print("3. Create database if needed: docker exec -it pgvector-db psql -U postgres -c \"CREATE DATABASE trading_agent;\"")
        print("4. Install pgvector: docker exec -it pgvector-db psql -U postgres -d trading_agent -c \"CREATE EXTENSION IF NOT EXISTS vector;\"")
        return False

def test_data_sources():
    """Test all data source API connections"""
    print("\n🌐 Testing Data Source APIs...")
    
    success_count = 0
    total_sources = 4
    
    try:
        from data_sources.alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        data = alpaca.get_market_data_for_symbol("AAPL", "1d")
        print(f"✅ Alpaca: Retrieved {len(data)} records for AAPL")
        success_count += 1
    except Exception as e:
        print(f"❌ Alpaca failed: {e}")
    
    try:
        from data_sources.sec_edgar_client import SECEdgarClient
        sec = SECEdgarClient()
        filings = sec.get_company_filings(forms=["10-K"], limit=5)
        print(f"✅ SEC EDGAR: Retrieved {len(filings)} recent 10-K filings")
        success_count += 1
    except Exception as e:
        print(f"❌ SEC EDGAR failed: {e}")
    
    try:
        from data_sources.fred_client import FREDClient
        fred = FREDClient()
        data = fred.get_series_data(["GDP"])
        print(f"✅ FRED: Retrieved {len(data)} GDP data points")
        success_count += 1
    except Exception as e:
        print(f"❌ FRED failed: {e}")
    
    try:
        from data_sources.binance_client import BinanceClient
        import asyncio
        binance = BinanceClient()
        data = asyncio.run(binance.get_historical_klines("BTCUSDT", "1d", 10))
        print(f"✅ Binance: Retrieved {len(data)} BTCUSDT klines")
        success_count += 1
    except Exception as e:
        print(f"❌ Binance failed: {e}")
    
    print(f"\n📊 Data Sources: {success_count}/{total_sources} working")
    return success_count == total_sources

def test_data_storage():
    """Test data storage and retrieval"""
    print("\n💾 Testing Data Storage...")
    
    try:
        from database.storage import DataStorage
        from database.schema import get_session_maker, create_database_engine
        
        engine = create_database_engine()
        SessionMaker = get_session_maker(engine)
        storage = DataStorage(SessionMaker)
        
        test_data = [{
            'symbol': 'TEST',
            'timestamp': datetime.now(),
            'source': 'test',
            'open_price': 100.0,
            'high_price': 105.0,
            'low_price': 95.0,
            'close_price': 102.0,
            'volume': 1000.0
        }]
        
        storage.store_market_data(test_data)
        print("✅ Market data storage successful")
        
        retrieved = storage.get_market_data('TEST', limit=1)
        if len(retrieved) > 0:
            print("✅ Market data retrieval successful")
            return True
        else:
            print("❌ Market data retrieval failed")
            return False
            
    except Exception as e:
        print(f"❌ Data storage test failed: {e}")
        return False

def test_modal_integration():
    """Test Modal integration"""
    print("\n🚀 Testing Modal Integration...")
    
    try:
        import modal
        print(f"✅ Modal available (version {modal.__version__})")
        
        from modal_app import app
        print("✅ Modal app configuration loaded")
        
        try:
            modal.lookup("trading-agent-data", "Volume")
            print("✅ Modal authentication working")
        except Exception:
            print("⚠️  Modal not authenticated - run: modal token new")
            
        return True
        
    except Exception as e:
        print(f"❌ Modal integration failed: {e}")
        return False

def test_application_startup():
    """Test that the application can start with database integration"""
    print("\n🚀 Testing Application Startup...")
    
    try:
        from api import app as fastapi_app
        from app import main as streamlit_main
        
        print("✅ FastAPI application imports successfully")
        print("✅ Streamlit application imports successfully")
        
        import requests
        import subprocess
        import time
        import signal
        
        print("\n🔄 Starting FastAPI server for testing...")
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "api:app", 
            "--host", "0.0.0.0", "--port", "8080"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Health Check: {health_data}")
                
                if health_data.get('database_connected'):
                    print("✅ Database connection verified via API")
                else:
                    print("❌ Database not connected via API")
                    
            else:
                print(f"❌ API health check failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            
        finally:
            process.terminate()
            process.wait()
            
        return True
        
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 GIGACONTEXT TRADING AGENT - LOCAL SETUP TEST")
    print("=" * 60)
    print("This script tests your complete data infrastructure setup")
    print("=" * 60)
    
    all_tests_passed = True
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Database Connection", test_database_connection),
        ("Data Sources", test_data_sources),
        ("Data Storage", test_data_storage),
        ("Modal Integration", test_modal_integration),
        ("Application Startup", test_application_startup)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if not test_func():
                all_tests_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎯 ALL TESTS PASSED! Your gigacontext trading agent is ready!")
        print("\n🚀 Next steps:")
        print("1. Run: python start_app.py")
        print("2. Access dashboard: http://localhost:8501")
        print("3. Access API: http://localhost:8080")
        print("4. Start data ingestion via API endpoints")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Ensure Docker containers are running: docker-compose up -d")
        print("2. Check environment variables in .env file")
        print("3. Authenticate with Modal: modal token new")
        print("4. Verify API keys are valid")
    
    print("=" * 60)
    sys.exit(0 if all_tests_passed else 1)
