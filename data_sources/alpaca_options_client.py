import os
import time
from datetime import datetime
from typing import List, Optional
import requests
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AlpacaOptionsClient:
	def __init__(self):
		self.api_key = os.getenv("APCA_API_KEY_ID")
		self.secret_key = os.getenv("APCA_API_SECRET_KEY")
		self.base_trading = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
		self.base_data = os.getenv("APCA_DATA_URL", "https://data.alpaca.markets")
		if not self.api_key or not self.secret_key:
			raise ValueError("Alpaca API credentials not found in environment variables")
		self._rate_delay = float(os.getenv("ALPACA_RATE_DELAY_SEC", "0.35"))  # ~200/min => 0.3s

	def _headers(self):
		return {
			"APCA-API-KEY-ID": self.api_key,
			"APCA-API-SECRET-KEY": self.secret_key,
		}

	def list_option_contracts(self, underlying_symbols: List[str], expiration_gte: Optional[str] = None, expiration_lte: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
		"""Fetch option contracts metadata for given underlying symbols (paged)."""
		contracts = []
		params = {
			"underlying_symbols": ",".join(underlying_symbols),
			"limit": limit,
		}
		if expiration_gte:
			params["expiration_date_gte"] = expiration_gte
		if expiration_lte:
			params["expiration_date_lte"] = expiration_lte
		page_token = None
		while True:
			if page_token:
				params["page_token"] = page_token
			url = f"{self.base_trading}/v2/options/contracts"
			time.sleep(self._rate_delay)
			r = requests.get(url, headers=self._headers(), params=params)
			if r.status_code == 429:
				time.sleep(5)
				continue
			r.raise_for_status()
			data = r.json()
			contracts.extend(data.get("option_contracts", []))
			page_token = data.get("page_token")
			if not page_token:
				break
		return pd.DataFrame(contracts)

	def get_option_bars(self, symbols: List[str], timeframe: str, start_iso: str, end_iso: str, per_request_limit: int = 10000) -> pd.DataFrame:
		"""Fetch historical option bars for a set of symbols. Returns a long DataFrame."""
		all_rows = []
		chunk = 50  # Alpaca allows comma-separated symbols; keep modest
		for i in range(0, len(symbols), chunk):
			batch = symbols[i:i+chunk]
			params = {
				"symbols": ",".join(batch),
				"timeframe": timeframe,
				"start": start_iso,
				"end": end_iso,
				"limit": per_request_limit,
			}
			url = f"{self.base_data}/v1beta1/options/bars"
			time.sleep(self._rate_delay)
			r = requests.get(url, headers=self._headers(), params=params)
			if r.status_code == 429:
				time.sleep(5)
				# retry once
				r = requests.get(url, headers=self._headers(), params=params)
			r.raise_for_status()
			bars = r.json().get("bars", {})
			for sym, rows in bars.items():
				if not rows:
					continue
				df = pd.DataFrame(rows)
				df["symbol"] = sym
				all_rows.append(df)
		return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame() 