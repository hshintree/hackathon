"""
Test database connection to user's Docker PostgreSQL setup
"""
from database.schema import get_database_url, create_database_engine, create_tables

def test_database_connection():
    """Test connection to Docker PostgreSQL container"""
    print("🗄️ Testing Database Connection to Docker PostgreSQL...")
    
    try:
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
        print("This is expected since database is on user's machine via Docker")
        return False

if __name__ == "__main__":
    test_database_connection()
