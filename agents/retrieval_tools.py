from typing import List, Dict, Any

from retrieval_layer import retrieve, search_dense, search_bm25
from sqlalchemy import text
from database.storage import DataStorage
from datetime import datetime
from sqlalchemy import and_, asc
from database.schema import MarketData, OptionsBar, OptionsContract
from database.schema import MacroData


def search_text(query: str, top_k: int = 20, alpha: float = 0.5, use_bm25: bool = True, rerank: bool = True) -> List[Dict[str, Any]]:
	"""Hybrid retrieval with optional reranking."""
	return retrieve(query=query, top_k=top_k, alpha=alpha, use_bm25=use_bm25, rerank=rerank)


def search_dense_only(query: str, top_k: int = 20) -> List[Dict[str, Any]]:
	return search_dense(query, top_n=top_k)


def search_bm25_only(query: str, top_k: int = 20) -> List[Dict[str, Any]]:
	return search_bm25(query, top_n=top_k)


def get_doc(chunk_id: int) -> Dict[str, Any]:
	"""Fetch a chunk row by id."""
	s = DataStorage()
	with s.get_session() as db:
		row = db.execute(text("select id, source, symbol, document_id, chunk_index, content from text_chunks where id=:id"), {"id": chunk_id}).mappings().first()
		return dict(row) if row else {}

# ---------------------------
# Structured data fetchers
# ---------------------------

def _ts(dt: datetime | None) -> str | None:
	return dt.isoformat() if isinstance(dt, datetime) else None


def get_prices(assets: List[str], start: str, end: str, source: str | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
	"""Fetch OHLCV rows from market_data for given symbols and window; JSON-serializable."""
	s = DataStorage()
	with s.get_session() as db:
		start_dt = datetime.fromisoformat(start) if start else None
		end_dt = datetime.fromisoformat(end) if end else None
		q = db.query(MarketData).filter(MarketData.symbol.in_(assets))
		if start_dt is not None:
			q = q.filter(MarketData.timestamp >= start_dt)
		if end_dt is not None:
			q = q.filter(MarketData.timestamp <= end_dt)
		if source:
			q = q.filter(MarketData.source == source)
		q = q.order_by(MarketData.symbol.asc(), MarketData.timestamp.asc())
		if limit:
			q = q.limit(limit)
		rows = q.all()
		out: List[Dict[str, Any]] = []
		for r in rows:
			out.append({
				"symbol": r.symbol,
				"timestamp": _ts(r.timestamp),
				"open": r.open_price,
				"high": r.high_price,
				"low": r.low_price,
				"close": r.close_price,
				"volume": r.volume,
				"trade_count": r.trade_count,
				"vwap": r.vwap,
				"source": r.source,
			})
		return out


def get_option_bars(option_symbols: List[str], start: str, end: str, timeframe: str | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
	"""Fetch options bars for OCC symbols and window; optionally filter by timeframe."""
	s = DataStorage()
	with s.get_session() as db:
		start_dt = datetime.fromisoformat(start) if start else None
		end_dt = datetime.fromisoformat(end) if end else None
		q = db.query(OptionsBar).filter(OptionsBar.symbol.in_(option_symbols))
		if start_dt is not None:
			q = q.filter(OptionsBar.timestamp >= start_dt)
		if end_dt is not None:
			q = q.filter(OptionsBar.timestamp <= end_dt)
		if timeframe:
			q = q.filter(OptionsBar.timeframe == timeframe)
		q = q.order_by(OptionsBar.symbol.asc(), OptionsBar.timestamp.asc())
		if limit:
			q = q.limit(limit)
		rows = q.all()
		out: List[Dict[str, Any]] = []
		for r in rows:
			out.append({
				"symbol": r.symbol,
				"timestamp": _ts(r.timestamp),
				"timeframe": r.timeframe,
				"open": r.open_price,
				"high": r.high_price,
				"low": r.low_price,
				"close": r.close_price,
				"volume": r.volume,
				"trade_count": r.trade_count,
				"vwap": r.vwap,
				"source": r.source,
			})
		return out


def get_option_contracts(underlyings: List[str] | None = None,
						  status: str | None = "active",
						  tradable: bool | None = None,
						  min_open_interest: float | None = None,
						  exp_gte: str | None = None,
						  exp_lte: str | None = None,
						  limit: int | None = 1000) -> List[Dict[str, Any]]:
	"""Fetch options contracts metadata with common filters; JSON-serializable."""
	s = DataStorage()
	with s.get_session() as db:
		q = db.query(OptionsContract)
		if underlyings:
			q = q.filter(OptionsContract.underlying_symbol.in_(underlyings))
		if status:
			q = q.filter(OptionsContract.status == status)
		if tradable is not None:
			q = q.filter(OptionsContract.tradable == tradable)
		if min_open_interest is not None:
			q = q.filter(OptionsContract.open_interest >= float(min_open_interest))
		if exp_gte:
			q = q.filter(OptionsContract.expiration_date >= datetime.fromisoformat(exp_gte))
		if exp_lte:
			q = q.filter(OptionsContract.expiration_date <= datetime.fromisoformat(exp_lte))
		q = q.order_by(OptionsContract.underlying_symbol.asc(), OptionsContract.expiration_date.asc(), OptionsContract.strike_price.asc())
		if limit:
			q = q.limit(limit)
		rows = q.all()
		out: List[Dict[str, Any]] = []
		for r in rows:
			out.append({
				"symbol": r.symbol,
				"root_symbol": r.root_symbol,
				"underlying_symbol": r.underlying_symbol,
				"expiration_date": _ts(r.expiration_date),
				"option_type": r.option_type,
				"strike_price": r.strike_price,
				"style": r.style,
				"size": r.size,
				"status": r.status,
				"tradable": r.tradable,
				"open_interest": r.open_interest,
				"open_interest_date": _ts(r.open_interest_date),
				"close_price": r.close_price,
				"close_price_date": _ts(r.close_price_date),
			})
		return out


def get_fred(series_ids: List[str], start: str | None = None, end: str | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
	"""Fetch macro series from MacroData table."""
	s = DataStorage()
	with s.get_session() as db:
		q = db.query(MacroData).filter(MacroData.series_id.in_(series_ids))
		if start:
			q = q.filter(MacroData.date >= datetime.fromisoformat(start))
		if end:
			q = q.filter(MacroData.date <= datetime.fromisoformat(end))
		q = q.order_by(MacroData.series_id.asc(), MacroData.date.asc())
		if limit:
			q = q.limit(limit)
		rows = q.all()
		out: List[Dict[str, Any]] = []
		for r in rows:
			out.append({
				"series_id": r.series_id,
				"date": _ts(r.date),
				"value": r.value,
				"series_title": getattr(r, "series_title", None),
				"units": getattr(r, "units", None),
			})
		return out 