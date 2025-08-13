import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import logging

from .schema import (
    MarketData, SECFilings, MacroData, CryptoData, 
    DataIngestionJobs, DocumentEmbeddings,
    create_database_engine, get_session_maker
)

logger = logging.getLogger(__name__)

class DataStorage:
    def __init__(self):
        self.engine = create_database_engine()
        self.SessionMaker = get_session_maker(self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionMaker()
    
    def store_market_data(self, df: pd.DataFrame, source: str = "alpaca"):
        """Store market data in database"""
        try:
            with self.get_session() as session:
                records = []
                for _, row in df.iterrows():
                    record = MarketData(
                        symbol=row['symbol'],
                        timestamp=row['timestamp'],
                        source=source,
                        open_price=row.get('open'),
                        high_price=row.get('high'),
                        low_price=row.get('low'),
                        close_price=row.get('close'),
                        volume=row.get('volume'),
                        trade_count=row.get('trade_count'),
                        vwap=row.get('vwap'),
                        metadata=row.to_dict()
                    )
                    records.append(record)
                
                session.add_all(records)
                session.commit()
                
                logger.info(f"Stored {len(records)} market data records from {source}")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            raise
    
    def store_sec_filings(self, df: pd.DataFrame):
        """Store SEC filings in database"""
        try:
            with self.get_session() as session:
                records = []
                for _, row in df.iterrows():
                    record = SECFilings(
                        cik=row['cik'],
                        company_name=row.get('company_name'),
                        ticker=row.get('ticker'),
                        form_type=row['form'],
                        filing_date=row['filing_date'],
                        report_date=row.get('report_date'),
                        accession_number=row['accession_number'],
                        primary_document=row.get('primary_document'),
                        document_description=row.get('primary_doc_description')
                    )
                    records.append(record)
                
                session.add_all(records)
                session.commit()
                
                logger.info(f"Stored {len(records)} SEC filing records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error storing SEC filings: {e}")
            raise
    
    def store_macro_data(self, df: pd.DataFrame):
        """Store macro/economic data in database"""
        try:
            with self.get_session() as session:
                records = []
                for _, row in df.iterrows():
                    record = MacroData(
                        series_id=row['series_id'],
                        date=row['date'],
                        value=row['value'],
                        realtime_start=row.get('realtime_start'),
                        realtime_end=row.get('realtime_end')
                    )
                    records.append(record)
                
                session.add_all(records)
                session.commit()
                
                logger.info(f"Stored {len(records)} macro data records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error storing macro data: {e}")
            raise
    
    def store_crypto_data(self, df: pd.DataFrame):
        """Store crypto data in database"""
        try:
            with self.get_session() as session:
                records = []
                for _, row in df.iterrows():
                    record = CryptoData(
                        symbol=row['symbol'],
                        timestamp=row['timestamp'],
                        data_type=row.get('type', 'ticker'),
                        open_price=row.get('open'),
                        high_price=row.get('high'),
                        low_price=row.get('low'),
                        close_price=row.get('close', row.get('price')),
                        volume=row.get('volume'),
                        quote_volume=row.get('quote_volume'),
                        trade_count=row.get('trade_count'),
                        price_change_percent=row.get('price_change_percent'),
                        metadata=row.to_dict()
                    )
                    records.append(record)
                
                session.add_all(records)
                session.commit()
                
                logger.info(f"Stored {len(records)} crypto data records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error storing crypto data: {e}")
            raise
    
    def get_market_data(self, symbols: List[str], start_date: datetime, end_date: datetime, source=None) -> pd.DataFrame:
        """Retrieve market data from database"""
        try:
            with self.get_session() as session:
                query = session.query(MarketData).filter(
                    and_(
                        MarketData.symbol.in_(symbols),
                        MarketData.timestamp >= start_date,
                        MarketData.timestamp <= end_date
                    )
                )
                
                if source:
                    query = query.filter(MarketData.source == source)
                
                query = query.order_by(MarketData.symbol, MarketData.timestamp)
                
                results = query.all()
                
                data = []
                for record in results:
                    data.append({
                        'symbol': record.symbol,
                        'timestamp': record.timestamp,
                        'open': record.open_price,
                        'high': record.high_price,
                        'low': record.low_price,
                        'close': record.close_price,
                        'volume': record.volume,
                        'source': record.source
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            raise
    
    def get_sec_filings(self, tickers=None, forms=None, limit: int = 100) -> pd.DataFrame:
        """Retrieve SEC filings from database"""
        try:
            with self.get_session() as session:
                query = session.query(SECFilings)
                
                if tickers:
                    query = query.filter(SECFilings.ticker.in_(tickers))
                
                if forms:
                    query = query.filter(SECFilings.form_type.in_(forms))
                
                query = query.order_by(desc(SECFilings.filing_date)).limit(limit)
                
                results = query.all()
                
                data = []
                for record in results:
                    data.append({
                        'cik': record.cik,
                        'company_name': record.company_name,
                        'ticker': record.ticker,
                        'form': record.form_type,
                        'filing_date': record.filing_date,
                        'report_date': record.report_date,
                        'accession_number': record.accession_number
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error retrieving SEC filings: {e}")
            raise
    
    def get_macro_data(self, series_ids: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Retrieve macro data from database"""
        try:
            with self.get_session() as session:
                query = session.query(MacroData).filter(
                    and_(
                        MacroData.series_id.in_(series_ids),
                        MacroData.date >= start_date,
                        MacroData.date <= end_date
                    )
                ).order_by(MacroData.series_id, MacroData.date)
                
                results = query.all()
                
                data = []
                for record in results:
                    data.append({
                        'series_id': record.series_id,
                        'date': record.date,
                        'value': record.value
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error retrieving macro data: {e}")
            raise
    
    def get_crypto_data(self, symbols: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Retrieve crypto data from database"""
        try:
            with self.get_session() as session:
                query = session.query(CryptoData).filter(
                    and_(
                        CryptoData.symbol.in_(symbols),
                        CryptoData.timestamp >= start_date,
                        CryptoData.timestamp <= end_date
                    )
                ).order_by(CryptoData.symbol, CryptoData.timestamp)
                
                results = query.all()
                
                data = []
                for record in results:
                    data.append({
                        'symbol': record.symbol,
                        'timestamp': record.timestamp,
                        'type': record.data_type,
                        'open': record.open_price,
                        'high': record.high_price,
                        'low': record.low_price,
                        'close': record.close_price,
                        'volume': record.volume
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error retrieving crypto data: {e}")
            raise
    
    def store_job_status(self, job_id: str, job_type: str, status: str, parameters=None, results=None, error_message=None):
        """Store data ingestion job status"""
        try:
            with self.get_session() as session:
                existing_job = session.query(DataIngestionJobs).filter(DataIngestionJobs.job_id == job_id).first()
                
                if existing_job:
                    existing_job.status = status
                    if status == "running" and not existing_job.started_at:
                        existing_job.started_at = datetime.now()
                    elif status in ["completed", "failed"]:
                        existing_job.completed_at = datetime.now()
                    if error_message:
                        existing_job.error_message = error_message
                    if results:
                        existing_job.results = results
                else:
                    job = DataIngestionJobs(
                        job_id=job_id,
                        job_type=job_type,
                        status=status,
                        created_at=datetime.now(),
                        parameters=parameters,
                        results=results,
                        error_message=error_message
                    )
                    session.add(job)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error storing job status: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get data ingestion job status"""
        try:
            with self.get_session() as session:
                job = session.query(DataIngestionJobs).filter(DataIngestionJobs.job_id == job_id).first()
                
                if job:
                    return {
                        'job_id': job.job_id,
                        'job_type': job.job_type,
                        'status': job.status,
                        'created_at': job.created_at,
                        'started_at': job.started_at,
                        'completed_at': job.completed_at,
                        'error_message': job.error_message,
                        'parameters': job.parameters,
                        'results': job.results
                    }
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error retrieving job status: {e}")
            raise
