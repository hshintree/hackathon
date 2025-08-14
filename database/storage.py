import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import logging
import numpy as np
import math

from .schema import (
	MarketData, SECFilings, MacroData, CryptoData, 
	DataIngestionJobs, DocumentEmbeddings,
	create_database_engine, get_session_maker,
	OptionsContract, OptionsBar, NewsArticle
)

logger = logging.getLogger(__name__)

class DataStorage:
	def __init__(self):
		self.engine = create_database_engine()
		self.SessionMaker = get_session_maker(self.engine)
	
	def get_session(self) -> Session:
		"""Get database session"""
		return self.SessionMaker()
	
	def _to_jsonable_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Convert pandas/NumPy/datetime types to JSON-serializable primitives."""
		def convert(value):
			# Normalize pandas/NumPy NaN/NaT to None for Postgres JSON
			try:
				if pd.isna(value):
					return None
			except Exception:
				pass
			if isinstance(value, (pd.Timestamp, datetime)):
				# Convert to ISO string
				return value.isoformat()
			if isinstance(value, (np.integer,)):
				return int(value)
			if isinstance(value, (np.floating,)):
				v = float(value)
				return None if math.isnan(v) else v
			if isinstance(value, (np.bool_,)):
				return bool(value)
			return value
		return {k: convert(v) for k, v in data.items()}
	
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
						meta_data=self._to_jsonable_dict(row.to_dict())
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
				# Skip if empty
				if df is None or df.empty:
					return 0
				# Preload existing accession_numbers to avoid unique violations
				existing = set(
					row[0]
					for row in session.query(SECFilings.accession_number).filter(
						SECFilings.accession_number.in_(df['accession_number'].astype(str).tolist())
					).all()
				)
				records = []
				for _, row in df.iterrows():
					acc = str(row['accession_number'])
					if acc in existing:
						continue
					record = SECFilings(
						cik=row['cik'],
						company_name=row.get('company_name'),
						ticker=row.get('ticker'),
						form_type=row['form'],
						filing_date=row['filing_date'],
						report_date=row.get('report_date'),
						accession_number=acc,
						primary_document=row.get('primary_document'),
						document_description=row.get('primary_doc_description')
					)
					records.append(record)
				
				if records:
					session.add_all(records)
					session.commit()
					logger.info(f"Stored {len(records)} SEC filing records")
					return len(records)
				return 0
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
						meta_data=self._to_jsonable_dict(row.to_dict())
					)
					records.append(record)
				
				session.add_all(records)
				session.commit()
				
				logger.info(f"Stored {len(records)} crypto data records")
				return len(records)
				
		except Exception as e:
			logger.error(f"Error storing crypto data: {e}")
			raise
	
	def store_options_contracts(self, df: pd.DataFrame):
		"""Upsert-like insert for options contracts."""
		try:
			with self.get_session() as session:
				inserted = 0
				for _, row in df.iterrows():
					# Simple get-or-insert by symbol
					existing = session.query(OptionsContract).filter(OptionsContract.symbol == row['symbol']).first()
					if existing:
						continue
					rec = OptionsContract(
						symbol=row['symbol'],
						root_symbol=row.get('root_symbol') or row.get('root_symbol', row.get('underlying_symbol')),
						underlying_symbol=row.get('underlying_symbol'),
						expiration_date=pd.to_datetime(row.get('expiration_date')) if row.get('expiration_date') else None,
						option_type=row.get('type'),
						strike_price=float(row.get('strike_price')) if row.get('strike_price') is not None else None,
						style=row.get('style'),
						size=int(row.get('size')) if row.get('size') else None,
						status=row.get('status'),
						tradable=bool(row.get('tradable')) if row.get('tradable') is not None else None,
						open_interest=float(row.get('open_interest')) if row.get('open_interest') is not None else None,
						open_interest_date=pd.to_datetime(row.get('open_interest_date')) if row.get('open_interest_date') else None,
						close_price=float(row.get('close_price')) if row.get('close_price') is not None else None,
						close_price_date=pd.to_datetime(row.get('close_price_date')) if row.get('close_price_date') else None,
						meta_data=self._to_jsonable_dict(row.to_dict())
					)
					session.add(rec)
					inserted += 1
				session.commit()
				logger.info(f"Stored {inserted} options contracts")
				return inserted
		except Exception as e:
			logger.error(f"Error storing options contracts: {e}")
			raise
	
	def store_options_bars(self, df: pd.DataFrame, timeframe: str, source: str = "alpaca"):
		"""Store options bars."""
		try:
			with self.get_session() as session:
				records = []
				for _, row in df.iterrows():
					record = OptionsBar(
						symbol=row['symbol'],
						timestamp=pd.to_datetime(row.get('t') or row.get('timestamp')),
						timeframe=timeframe,
						source=source,
						open_price=row.get('o') or row.get('open'),
						high_price=row.get('h') or row.get('high'),
						low_price=row.get('l') or row.get('low'),
						close_price=row.get('c') or row.get('close'),
						volume=row.get('v') or row.get('volume'),
						trade_count=row.get('n') or row.get('trade_count'),
						vwap=row.get('vw') or row.get('vwap')
					)
					records.append(record)
				session.add_all(records)
				session.commit()
				logger.info(f"Stored {len(records)} options bars")
				return len(records)
		except Exception as e:
			logger.error(f"Error storing options bars: {e}")
			raise
	
	def store_news_articles(self, rows: List[Dict[str, Any]]):
		"""Store a list of news articles. Each row may include symbol, headline, summary, url, publisher, author, published_at, sentiment_score, sentiment_label, raw, source."""
		try:
			with self.get_session() as session:
				records = []
				for row in rows:
					records.append(NewsArticle(
						source=row.get('source', 'alpaca'),
						symbol=row.get('symbol'),
						headline=row.get('headline'),
						summary=row.get('summary'),
						url=row.get('url'),
						publisher=row.get('publisher'),
						author=row.get('author'),
						published_at=pd.to_datetime(row.get('published_at')) if row.get('published_at') else None,
						sentiment_score=row.get('sentiment_score'),
						sentiment_label=row.get('sentiment_label'),
						raw=self._to_jsonable_dict(row.get('raw') or {}) if isinstance(row.get('raw'), dict) else None,
						created_at=datetime.now()
					))
				session.add_all(records)
				session.commit()
				return len(records)
		except Exception as e:
			logger.error(f"Error storing news articles: {e}")
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
