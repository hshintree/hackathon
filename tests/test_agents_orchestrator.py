import os, sys
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

# Ensure local project root is importable
_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _ROOT not in sys.path:
	sys.path.insert(0, _ROOT)


def test_orchestrator_routes_librarian(monkeypatch):
	# Start librarian app with stubs
	from agents import mcp_librarian as lib
	monkeypatch.setattr(lib, "search_text", lambda q, **kw: [{"id": 1, "source": "news", "document_id": "doc1"}])
	monkeypatch.setattr(lib, "get_doc", lambda cid: {"id": cid, "source": "news"})
	lib_client = TestClient(lib.app)

	# Monkeypatch requests.post used by orchestrator to forward to librarian TestClient
	from agents import mcp_orchestrator as orch
	def fake_post(url, json):
		if url.endswith("/tools/search_corpus"):
			return type("Resp", (), {"json": lambda: lib_client.post("/tools/search_corpus", json=json).json()})
		if url.endswith("/tools/get_chunk"):
			return type("Resp", (), {"json": lambda: lib_client.post("/tools/get_chunk", json=json).json()})
		raise RuntimeError("unexpected url: "+url)
	monkeypatch.setattr(orch, "requests", type("Reqs", (), {"post": staticmethod(fake_post)}))

	client = TestClient(orch.app)
	resp = client.post("/tools/route", json={"intent":"search_corpus", "payload": {"query":"test","top_k":2}})
	assert resp.status_code == 200
	assert "results" in resp.json()
	resp2 = client.post("/tools/route", json={"intent":"get_chunk", "payload": {"chunk_id": 42}})
	assert resp2.status_code == 200
	assert resp2.json().get("doc",{}).get("id") == 42


def test_multiserver_flow(monkeypatch):
	# Librarian → Data → Quant pipeline
	from agents import mcp_librarian as lib, mcp_data as data, mcp_quant as quant
	# Librarian stub: returns SEC doc id and AAPL symbol
	monkeypatch.setattr(lib, "search_text", lambda q, **kw: [{"id": 100, "source":"sec", "symbol":"AAPL", "document_id":"sec:doc"}])
	monkeypatch.setattr(lib, "get_doc", lambda cid: {"id": cid, "source": "sec", "content": "10-Q"})
	lib_client = TestClient(lib.app)
	# Data stub: return synthetic price series
	now = datetime(2024,1,1)
	monkeypatch.setattr(data, "get_prices", lambda assets, start, end, source=None, limit=None: [
		{"symbol": assets[0], "timestamp": (now+timedelta(days=i)).isoformat(), "open": 100+i, "high": 100+i, "low": 100+i, "close": 100+i, "volume": 1000, "trade_count": 10, "vwap": 100+i, "source": source or "alpaca"}
		for i in range(30)
	])
	data_client = TestClient(data.app)
	# Quant uses get_prices internally; monkeypatch it too
	monkeypatch.setattr(quant, "get_prices", lambda assets, start, end, source=None, limit=None: [
		{"symbol": assets[0], "timestamp": (now+timedelta(days=i)).isoformat(), "open": 100+i, "high": 100+i, "low": 100+i, "close": 100+i, "volume": 1000, "trade_count": 10, "vwap": 100+i, "source": source or "alpaca"}
		for i in range(30)
	])
	quant_client = TestClient(quant.app)

	# Flow: search → get_chunk → get_prices → run_backtest
	search = lib_client.post("/tools/search_corpus", json={"query":"apple 10-q","top_k":1})
	assert search.status_code == 200
	cid = search.json()["results"][0]["id"]
	doc = lib_client.post("/tools/get_chunk", json={"id": cid}).json()
	assert doc["doc"]["source"] == "sec"
	px = data_client.post("/tools/get_prices", json={"assets":["AAPL"], "start":"2024-01-01T00:00:00", "end":"2024-02-01T00:00:00"}).json()
	assert isinstance(px, list) and len(px) > 0
	bt = quant_client.post("/tools/run_backtest", json={"params": {"strategy":"ma_cross","ma_short":5,"ma_long":10}, "universe":["AAPL"], "start":"2024-01-01T00:00:00", "end":"2024-02-01T00:00:00"}).json()
	assert "metrics" in bt and isinstance(bt["metrics"], dict) 