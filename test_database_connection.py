"""
Test database connection to user's Docker PostgreSQL setup
"""
import os
import sys
from datetime import datetime

def test_database_connection():
    """Test connection to Docker PostgreSQL container"""
    print("🗄️ Testing Database Connection to Docker PostgreSQL...")
    
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
                return False
        
        print("\n📋 Creating Database Schema...")
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

if __name__ == "__main__":
    print("🔍 DATABASE CONNECTION TEST")
    print("=" * 50)
    
    success = test_database_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 Database connection and schema setup successful!")
    else:
        print("❌ Database setup failed - check Docker configuration")
    
    sys.exit(0 if success else 1)
