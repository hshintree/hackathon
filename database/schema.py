from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
import os

Base = declarative_base()

class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(20), nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    trade_count = Column(Integer)
    vwap = Column(Float)
    meta_data = Column(JSON)

class SECFilings(Base):
    __tablename__ = 'sec_filings'
    
    id = Column(Integer, primary_key=True)
    cik = Column(String(10), nullable=False, index=True)
    company_name = Column(String(255))
    ticker = Column(String(10), index=True)
    form_type = Column(String(10), nullable=False)
    filing_date = Column(DateTime, nullable=False, index=True)
    report_date = Column(DateTime)
    accession_number = Column(String(25), unique=True)
    primary_document = Column(String(255))
    document_description = Column(Text)
    content_summary = Column(Text)
    embedding = Column(Vector(1536))

class MacroData(Base):
    __tablename__ = 'macro_data'
    
    id = Column(Integer, primary_key=True)
    series_id = Column(String(50), nullable=False, index=True)
    series_title = Column(String(255))
    date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    units = Column(String(100))
    frequency = Column(String(20))
    seasonal_adjustment = Column(String(50))
    realtime_start = Column(DateTime)
    realtime_end = Column(DateTime)

class CryptoData(Base):
    __tablename__ = 'crypto_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    data_type = Column(String(20), nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    quote_volume = Column(Float)
    trade_count = Column(Integer)
    price_change_percent = Column(Float)
    meta_data = Column(JSON)

class DataIngestionJobs(Base):
    __tablename__ = 'data_ingestion_jobs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), unique=True)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    parameters = Column(JSON)
    results = Column(JSON)

class DocumentEmbeddings(Base):
    __tablename__ = 'document_embeddings'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(100), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))
    meta_data = Column(JSON)
    created_at = Column(DateTime, nullable=False)

def get_database_url():
    """Get database URL from environment variables"""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'trading_agent')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def create_database_engine():
    """Create database engine with connection pooling"""
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
    return engine

def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)

def get_session_maker(engine):
    """Get session maker for database operations"""
    return sessionmaker(bind=engine)
