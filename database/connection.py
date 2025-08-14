#!/usr/bin/env python3
"""
Database connection utility for the trading agent.
Handles connection pooling and health checks.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.schema import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._connected = False

    def create_engine(self):
        """Create database engine with connection pooling"""
        try:
            # Get database configuration from environment variables
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "trading_agent")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "postgres")

            # Create connection URL
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info("Database engine created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return False

    def test_connection(self):
        """Test database connection"""
        try:
            if not self.engine:
                logger.error("Database engine not initialized")
                return False
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                self._connected = True
                logger.info("Database connection test successful")
                return True
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            self._connected = False
            return False

    def create_tables(self):
        """Create all database tables"""
        try:
            if not self.engine:
                logger.error("Database engine not initialized")
                return False
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False

    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            logger.error("Database session factory not initialized")
            return None
        
        return self.SessionLocal()

    def is_connected(self):
        """Check if database is connected"""
        return self._connected

    def get_connection_info(self):
        """Get database connection information"""
        if not self.engine:
            return None
        
        try:
            with self.engine.connect() as conn:
                # Get PostgreSQL version
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                
                # Get connection count
                count_result = conn.execute(text("SELECT count(*) FROM pg_stat_activity"))
                connection_count = count_result.fetchone()[0]
                
                return {
                    "version": version,
                    "connection_count": connection_count,
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow()
                }
                
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return None

# Global database connection instance
db_connection = DatabaseConnection()

def initialize_database():
    """Initialize database connection and create tables"""
    logger.info("Initializing database...")
    
    # Create engine
    if not db_connection.create_engine():
        logger.error("Failed to create database engine")
        return False
    
    # Test connection
    if not db_connection.test_connection():
        logger.error("Failed to test database connection")
        return False
    
    # Create tables
    if not db_connection.create_tables():
        logger.error("Failed to create database tables")
        return False
    
    logger.info("Database initialization completed successfully")
    return True

def get_db_session():
    """Get database session"""
    return db_connection.get_session()

def is_database_connected():
    """Check if database is connected"""
    return db_connection.is_connected()

def get_database_info():
    """Get database connection information"""
    return db_connection.get_connection_info()

if __name__ == "__main__":
    # Test database connection
    if initialize_database():
        print("✅ Database connection successful")
        
        # Get connection info
        info = get_database_info()
        if info:
            print(f"📊 Database Info:")
            print(f"   Version: {info['version']}")
            print(f"   Active Connections: {info['connection_count']}")
            print(f"   Pool Size: {info['pool_size']}")
            print(f"   Checked In: {info['checked_in']}")
            print(f"   Checked Out: {info['checked_out']}")
            print(f"   Overflow: {info['overflow']}")
    else:
        print("❌ Database connection failed")
        sys.exit(1) 