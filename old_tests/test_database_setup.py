"""
Test database setup and schema creation for Docker PostgreSQL
"""
import os
import sys
from datetime import datetime

def test_database_connection():
    """Test connection to Docker PostgreSQL container"""
    print("🗄️ Testing Database Connection...")
    
    try:
        from database.schema import get_database_url, create_database_engine
        
        db_url = get_database_url()
        print(f"Database URL: {db_url}")
        
        engine = create_database_engine()
        print("✅ Database engine created")
        
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful: {version}")
            
            result = conn.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            vector_ext = result.fetchone()
            if vector_ext:
                print("✅ pgvector extension is installed")
            else:
                print("❌ pgvector extension not found")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_database_schema():
    """Create database schema and tables"""
    print("\n📋 Creating Database Schema...")
    
    try:
        from database.schema import create_database_engine, create_tables, Base
        
        engine = create_database_engine()
        
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
            
            expected_tables = [
                'market_data', 'sec_filings', 'macro_data', 
                'crypto_data', 'data_ingestion_jobs', 'document_embeddings'
            ]
            
            print(f"✅ Created tables: {', '.join(tables)}")
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"❌ Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                print("✅ All expected tables created")
                
        return True
        
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return False

def test_data_storage():
    """Test basic data storage operations"""
    print("\n💾 Testing Data Storage...")
    
    try:
        from database.storage import DataStorage
        from database.schema import get_session_maker, create_database_engine
        
        engine = create_database_engine()
        SessionMaker = get_session_maker(engine)
        storage = DataStorage(SessionMaker)
        
        test_market_data = [{
            'symbol': 'TEST',
            'timestamp': datetime.now(),
            'source': 'test',
            'open_price': 100.0,
            'high_price': 105.0,
            'low_price': 95.0,
            'close_price': 102.0,
            'volume': 1000.0
        }]
        
        storage.store_market_data(test_market_data)
        print("✅ Market data storage test successful")
        
        retrieved_data = storage.get_market_data('TEST', limit=1)
        if len(retrieved_data) > 0:
            print("✅ Market data retrieval test successful")
        else:
            print("❌ Market data retrieval failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Data storage test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DATABASE SETUP TEST")
    print("=" * 50)
    
    success = True
    
    if not test_database_connection():
        success = False
    
    if success and not create_database_schema():
        success = False
    
    if success and not test_data_storage():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 Database setup complete and working!")
    else:
        print("❌ Database setup failed - check configuration")
    
    sys.exit(0 if success else 1)
