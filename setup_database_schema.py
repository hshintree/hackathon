#!/usr/bin/env python3
"""
Database Schema Setup Script
Applies all the new database tables and functions needed for backend integration
"""

import os
import sys
from pathlib import Path
import logging
import re

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database_schema():
    """Apply database schema updates"""
    try:
        # Set database environment variables
        os.environ.update({
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "trading_agent",
            "DB_USER": "postgres",
            "DB_PASSWORD": "Y2RUH53T"
        })
        
        # Import database connection
        from database.connection import initialize_database, get_db_session
        from sqlalchemy import text
        
        logger.info("Initializing database connection...")
        initialize_database()
        
        # Read and execute schema updates
        schema_file = Path(__file__).parent / "database" / "schema_updates.sql"
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        logger.info("Reading schema updates...")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Remove comments and split into statements
        # Remove single-line comments
        schema_sql = re.sub(r'--.*$', '', schema_sql, flags=re.MULTILINE)
        # Remove multi-line comments
        schema_sql = re.sub(r'/\*.*?\*/', '', schema_sql, flags=re.DOTALL)
        
        # Split SQL into individual statements
        statements = []
        for stmt in schema_sql.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
        
        logger.info(f"Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        session = get_db_session()
        try:
            for i, statement in enumerate(statements, 1):
                if statement:
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    session.execute(text(statement))
                    session.commit()
                    logger.info(f"✓ Statement {i} executed successfully")
        except Exception as e:
            logger.error(f"Error executing statement {i}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
        
        logger.info("✅ Database schema setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database schema: {e}")
        return False

def verify_schema_setup():
    """Verify that all tables were created successfully"""
    try:
        from database.connection import get_db_session
        from sqlalchemy import text
        
        session = get_db_session()
        
        # List of tables that should exist
        expected_tables = [
            'agents', 'strategies', 'agent_decisions', 'system_metrics',
            'trades', 'portfolio_snapshots', 'market_data_cache',
            'news_articles', 'economic_indicators', 'sec_filings', 'backtest_results'
        ]
        
        logger.info("Verifying table creation...")
        
        for table in expected_tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                logger.info(f"✓ Table '{table}' exists with {count} records")
            except Exception as e:
                logger.error(f"✗ Table '{table}' not found or error: {e}")
                return False
        
        session.close()
        logger.info("✅ All tables verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying schema: {e}")
        return False

def test_data_service():
    """Test the data service functionality"""
    try:
        from database.data_service import DataService
        
        logger.info("Testing data service...")
        
        with DataService() as service:
            # Test agent operations
            agents = service.get_all_agents()
            logger.info(f"✓ Found {len(agents)} agents")
            
            # Test strategy operations
            strategies = service.get_all_strategies()
            logger.info(f"✓ Found {len(strategies)} strategies")
            
            # Test adding a system metric
            service.add_system_metric("test_metric", 42.0)
            logger.info("✓ Added test system metric")
            
            # Test getting database stats
            stats = service.get_database_stats()
            logger.info(f"✓ Database stats: {stats}")
        
        logger.info("✅ Data service test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing data service: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 Starting database schema setup...")
    
    # Step 1: Setup schema
    if not setup_database_schema():
        logger.error("❌ Schema setup failed")
        return False
    
    # Step 2: Verify setup
    if not verify_schema_setup():
        logger.error("❌ Schema verification failed")
        return False
    
    # Step 3: Test data service
    if not test_data_service():
        logger.error("❌ Data service test failed")
        return False
    
    logger.info("🎉 Database setup completed successfully!")
    logger.info("📊 All tables created and verified")
    logger.info("🔧 Data service is working correctly")
    logger.info("🚀 Ready for backend integration!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 