import os
import time
from datetime import datetime
from typing import List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FinnhubClient:
	def __init__(self):
		self.api_key = os.getenv("FINNHUB_API_KEY")
		if not self.api_key:
			raise ValueError("FINNHUB_API_KEY not found in environment variables")
		try:
			import finnhub
			self._fh = finnhub.Client(api_key=self.api_key)
		except Exception as e:
			raise RuntimeError(f"Failed to initialize Finnhub client: {e}")
		self.rate_limit_delay = 0.5

	def get_stock_symbols(self, exchange: str = "US") -> pd.DataFrame:
		"""Fetch stock symbols for an exchange (default US)."""
		try:
			time.sleep(self.rate_limit_delay)
			symbols = self._fh.stock_symbols(exchange=exchange) or []
			return pd.DataFrame(symbols)
		except Exception as e:
			logger.error(f"Error fetching Finnhub symbols for {exchange}: {e}")
			raise

	def get_stock_candles(self, symbol: str, resolution: str, start_unix: int, end_unix: int) -> pd.DataFrame:
		"""Get historical candles for a symbol. Resolution: '1', '5', '15', '30', '60', 'D', 'W', 'M'"""
		try:
			time.sleep(self.rate_limit_delay)
			res = self._fh.stock_candles(symbol, resolution, start_unix, end_unix)
			status = res.get('s')
			if status != 'ok':
				return pd.DataFrame()
			# Convert to DataFrame
			df = pd.DataFrame({
				'timestamp': pd.to_datetime(res['t'], unit='s'),
				'open': res['o'],
				'high': res['h'],
				'low': res['l'],
				'close': res['c'],
				'volume': res['v'],
			})
			df['symbol'] = symbol
			df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
			return df
		except Exception as e:
			logger.error(f"Error fetching Finnhub candles for {symbol}: {e}")
			raise

	def get_company_news(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
		"""Get company news. Dates are YYYY-MM-DD."""
		try:
			time.sleep(self.rate_limit_delay)
			news = self._fh.company_news(symbol, _from=start_date, to=end_date) or []
			return pd.DataFrame(news)
		except Exception as e:
			logger.error(f"Error fetching Finnhub news for {symbol}: {e}")
			raise 