import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys, os

# Ensure local project root is on sys.path so 'agents' resolves to this repo
_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _ROOT not in sys.path:
	sys.path.insert(0, _ROOT)

# ---------- Librarian ----------

def test_librarian_search_and_get_chunk(monkeypatch):
	from agents import mcp_librarian as srv

	# Stub search_text and get_doc in the module
	monkeypatch.setattr(srv, "search_text", lambda q, top_k=10, alpha=0.5, use_bm25=True, rerank=True: [
		{"id": 1, "source": "news", "symbol": "AAPL", "document_id": "doc1", "chunk_index": 0, "content": "dummy"}
	])
	monkeypatch.setattr(srv, "get_doc", lambda cid: {"id": cid, "source": "news", "content": "dummy"})

	client = TestClient(srv.app)
	resp = client.post("/tools/search_corpus", json={"query": "apple", "top_k": 2})
	assert resp.status_code == 200
	data = resp.json()
	assert "results" in data and isinstance(data["results"], list)

	resp2 = client.post("/tools/get_chunk", json={"id": 123})
	assert resp2.status_code == 200
	doc = resp2.json()["doc"]
	assert doc["id"] == 123


# ---------- Data ----------

def test_data_endpoints(monkeypatch):
	from agents import mcp_data as srv
	now = datetime(2024,1,1)
	# Stubs
	monkeypatch.setattr(srv, "get_prices", lambda assets, start, end, source=None, limit=None: [
		{"symbol": assets[0], "timestamp": (now+timedelta(days=i)).isoformat(), "open": 1+i, "high": 1+i, "low": 1+i, "close": 1+i, "volume": 100, "trade_count": 10, "vwap": 1+i, "source": source or "alpaca"}
		for i in range(3)
	])
	monkeypatch.setattr(srv, "get_option_bars", lambda symbols, start, end, timeframe=None, limit=None: [
		{"symbol": symbols[0], "timestamp": now.isoformat(), "timeframe": timeframe or "Day", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "trade_count": 1, "vwap": 1, "source": "alpaca"}
	])
	monkeypatch.setattr(srv, "get_option_contracts", lambda underlyings, status, tradable, min_oi, gte, lte, limit: [
		{"symbol": "AAPL250620C00100000", "underlying_symbol": "AAPL", "expiration_date": now.isoformat(), "option_type": "call", "strike_price": 100.0}
	])
	monkeypatch.setattr(srv, "get_fred", lambda series_ids, start, end, limit: [
		{"series_id": series_ids[0], "date": now.isoformat(), "value": 3.14}
	])
	client = TestClient(srv.app)
	assert client.post("/tools/get_prices", json={"assets":["AAPL"], "start":"2024-01-01T00:00:00", "end":"2024-01-10T00:00:00"}).status_code == 200
	assert client.post("/tools/get_option_bars", json={"symbols":["AAPL250620C00100000"], "start":"2025-06-01T00:00:00", "end":"2025-06-10T00:00:00"}).status_code == 200
	assert client.post("/tools/get_option_contracts", json={"underlyings":["AAPL"]}).status_code == 200
	assert client.post("/tools/get_fred", json={"series_ids":["UNRATE"]}).status_code == 200


# ---------- Quant ----------

def test_quant_run_backtest_and_grid(monkeypatch):
	from agents import mcp_quant as srv
	now = datetime(2024,1,1)
	def stub_prices(assets, start, end, source=None, limit=None):
		rows = []
		for i in range(30):
			for a in assets:
				rows.append({"symbol": a, "timestamp": (now+timedelta(days=i)).isoformat(), "open": 100+i, "high": 100+i, "low": 100+i, "close": 100+i, "volume": 1000, "trade_count": 10, "vwap": 100+i, "source": source or "alpaca"})
		return rows
	monkeypatch.setattr(srv, "get_prices", stub_prices)
	client = TestClient(srv.app)
	resp = client.post("/tools/run_backtest", json={"params": {"strategy":"ma_cross","ma_short":5,"ma_long":10}, "universe":["AAPL","MSFT"], "start":"2024-01-01T00:00:00", "end":"2024-02-01T00:00:00"})
	assert resp.status_code == 200
	assert "metrics" in resp.json()
	resp2 = client.post("/tools/grid_scan", json={"param_grid": {"ma_short": [5], "ma_long": [10]}, "universe":["AAPL"], "start":"2024-01-01T00:00:00", "end":"2024-02-01T00:00:00"})
	assert resp2.status_code == 200


# ---------- Risk ----------

def test_risk_var_and_stress(monkeypatch):
	from agents import mcp_risk as srv
	now = datetime(2024,1,1)
	def stub_prices(assets, start, end, source=None, limit=None):
		rows = []
		for i in range(30):
			for a in assets:
				rows.append({"symbol": a, "timestamp": (now+timedelta(days=i)).isoformat(), "open": 100+i, "high": 100+i, "low": 100+i, "close": 100+i, "volume": 1000, "trade_count": 10, "vwap": 100+i, "source": source or "alpaca"})
		return rows
	monkeypatch.setattr(srv, "get_prices", stub_prices)
	client = TestClient(srv.app)
	resp = client.post("/tools/compute_var", json={"assets":["AAPL"], "start":"2024-01-01T00:00:00", "end":"2024-02-01T00:00:00", "horizon_days":5, "paths":500, "alpha":0.95})
	assert resp.status_code == 200
	resp2 = client.post("/tools/stress_test", json={"assets":["AAPL"], "start":"2024-01-01T00:00:00", "end":"2024-02-01T00:00:00", "scenarios":[{"name":"-5%","shock_pct":-0.05}]})
	assert resp2.status_code == 200


# ---------- Allocator ----------

def test_allocator_opt():
	from agents import mcp_allocator as srv
	client = TestClient(srv.app)
	resp = client.post("/tools/optimize_portfolio", json={"assets":["AAPL","MSFT"], "method":"HRP"})
	assert resp.status_code == 200
	js = resp.json()
	assert "weights" in js and abs(sum(js["weights"].values()) - 1.0) < 1e-6 