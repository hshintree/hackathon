#!/usr/bin/env python3
"""
Database connection test and exploration script
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from database.schema import create_database_engine
from sqlalchemy import text

def test_connection():
    """Test database connection and show basic info."""
    print("🔗 Testing Database Connection...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Create engine
        engine = create_database_engine()
        
        # Test connection
        with engine.connect() as conn:
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to: {version}")
            
            # Check pgvector extension
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector extension is available")
            else:
                print("❌ pgvector extension not found")
            
            # List all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Available tables: {', '.join(tables)}")
            
            # Show table counts
            print("\n📊 Table Record Counts:")
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"   {table}: {count} records")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def explore_table(table_name):
    """Explore a specific table structure and sample data."""
    print(f"\n🔍 Exploring table: {table_name}")
    
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Get table structure
            result = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            
            print(f"📋 Structure of {table_name}:")
            for row in result.fetchall():
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"   {row[0]}: {row[1]} ({nullable})")
            
            # Get sample data
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
            rows = result.fetchall()
            
            if rows:
                print(f"\n📄 Sample data from {table_name}:")
                for i, row in enumerate(rows, 1):
                    print(f"   Row {i}: {row}")
            else:
                print(f"   No data in {table_name}")
                
    except Exception as e:
        print(f"❌ Error exploring {table_name}: {e}")

def main():
    """Main function to test and explore database."""
    print("🗄️ Database Connection and Exploration Tool")
    print("=" * 50)
    
    # Test basic connection
    if not test_connection():
        return 1
    
    # Explore specific tables
    tables_to_explore = ['market_data', 'sec_filings', 'macro_data']
    
    for table in tables_to_explore:
        explore_table(table)
    
    print("\n" + "=" * 50)
    print("✅ Database exploration complete!")
    print("\n💡 Tips:")
    print("   - Use PgAdmin at http://localhost:5050 for visual exploration")
    print("   - Use 'docker exec -it pgvector-db psql -U postgres -d trading_agent' for command line")
    print("   - Check the .env file for connection details")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 