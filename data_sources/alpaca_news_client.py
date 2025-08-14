import os
import time
from datetime import datetime
from typing import List, Optional
import logging
import requests

logger = logging.getLogger(__name__)


class AlpacaNewsClient:
	def __init__(self):
		self.api_key = os.getenv("APCA_API_KEY_ID")
		self.secret_key = os.getenv("APCA_API_SECRET_KEY")
		self.base_data = os.getenv("APCA_DATA_URL", "https://data.alpaca.markets")
		if not self.api_key or not self.secret_key:
			raise ValueError("Alpaca API credentials not found in environment variables")
		self._delay = float(os.getenv("ALPACA_RATE_DELAY_SEC", "0.35"))

	def _headers(self):
		return {
			"APCA-API-KEY-ID": self.api_key,
			"APCA-API-SECRET-KEY": self.secret_key,
		}

	def get_news(self, symbols: List[str], start: str, end: str, limit: int = 50, page_limit: int = 5000):
		"""Fetch historical news between ISO dates; returns list of dicts."""
		params = {
			"symbols": ",".join(symbols),
			"start": start,
			"end": end,
			"limit": limit,
		}
		url = f"{self.base_data}/v1beta1/news"
		articles = []
		fetched = 0
		page_token = None
		while True:
			if page_token:
				params["page_token"] = page_token
			time.sleep(self._delay)
			r = requests.get(url, headers=self._headers(), params=params)
			if r.status_code == 429:
				time.sleep(5)
				continue
			r.raise_for_status()
			data = r.json() or {}
			batch = data.get("news", [])
			for item in batch:
				articles.append({
					'source': 'alpaca',
					'symbol': item.get('symbols', [None])[0] if item.get('symbols') else None,
					'headline': item.get('headline'),
					'summary': item.get('summary'),
					'url': item.get('url'),
					'publisher': item.get('source'),
					'author': item.get('author'),
					'published_at': item.get('created_at'),
					'raw': {k: item.get(k) for k in ('id','updated_at','images','symbols')}
				})
			fetched += len(batch)
			if fetched >= page_limit or not batch:
				break
			page_token = data.get('next_page_token')
			if not page_token:
				break
		return articles 