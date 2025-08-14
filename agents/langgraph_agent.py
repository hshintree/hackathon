from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import os, httpx, json, re
from llm_client import chat

from agents.retrieval_tools import search_text, get_doc, get_prices
from graph_rag import search_graph as _search_graph
import pandas as pd
import numpy as np

MODAL_GRID_SCAN_URL = "https://hshindy--trading-agent-data-run-grid-scan.modal.run"
MODAL_VAR_URL = "https://hshindy--trading-agent-data-run-var.modal.run"
MODAL_OPTIMIZE_URL = "https://hshindy--trading-agent-data-run-optimize.modal.run"
MODAL_GRAPH_QUERY_URL = "https://hshindy--trading-agent-data-query-graph.modal.run"

USE_MODAL = os.getenv("USE_MODAL", "0") == "1"


class AgentState(TypedDict, total=False):
	query: str
	intent: str
	context: List[Dict[str, Any]]
	plan: str
	result: Dict[str, Any]
	error: Optional[str]



def create_fallback_response(path: str, payload: Dict[str, Any], error: str) -> Dict[str, Any]:
	if "/search_corpus" in path:
		query = payload.get("query", "")
		return {
			"results": [
				{"content": f"Mock search result for '{query}': Apple Inc. (AAPL) stock analysis shows strong fundamentals with recent price movements indicating bullish sentiment.", "score": 0.95},
				{"content": f"Financial data for '{query}': Current market cap $3.2T, P/E ratio 28.5, showing growth potential in AI and services sectors.", "score": 0.87},
				{"content": f"Technical analysis for '{query}': Stock shows upward trend with support at $180 and resistance at $200.", "score": 0.82}
			],
			"fallback": True,
			"error": f"MCP service unavailable: {error}"
		}
	elif "/run_backtest" in path:
		return {
			"metrics": {
				"total_return": 0.156,
				"annual_return": 0.124,
				"max_drawdown": -0.089,
				"sharpe_ratio": 1.23,
				"win_rate": 0.67
			},
			"fallback": True,
			"error": f"MCP service unavailable: {error}"
		}
	elif "/compute_var" in path:
		return {
			"var_95": -0.032,
			"var_99": -0.048,
			"expected_shortfall": -0.041,
			"fallback": True,
			"error": f"MCP service unavailable: {error}"
		}
	elif "/optimize_portfolio" in path:
		symbols = payload.get("symbols", ["AAPL", "GOOGL", "MSFT"])
		weights = [1.0/len(symbols)] * len(symbols)
		return {
			"optimal_weights": dict(zip(symbols, weights)),
			"expected_return": 0.12,
			"volatility": 0.18,
			"fallback": True,
			"error": f"MCP service unavailable: {error}"
		}
	else:
		return {
			"result": "Fallback response - MCP service unavailable",
			"fallback": True,
			"error": f"MCP service unavailable: {error}"
		}


async def call_modal_endpoint(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
	"""Call Modal web endpoint for compute-intensive operations"""
	try:
		async with httpx.AsyncClient(timeout=60.0) as client:
			r = await client.post(url, json=payload)
			r.raise_for_status()
			return r.json()
	except Exception as e:
		return {"error": f"Modal endpoint failed: {str(e)}", "fallback": True}

def call_search_corpus(query: str, top_k: int = 10, alpha: float = 0.5, rerank: bool = True, sources: Optional[List[str]] = None) -> Dict[str, Any]:
	"""Direct call to search_text with MCP-compatible response format"""
	try:
		res = search_text(query, top_k=top_k, alpha=alpha, use_bm25=True, rerank=rerank)
		if sources:
			res = [r for r in res if r.get("source") in sources]
		return {"results": res}
	except Exception as e:
		return create_fallback_response("/search_corpus", {"query": query}, str(e))

def call_get_chunk(chunk_id: int) -> Dict[str, Any]:
	"""Direct call to get_doc with MCP-compatible response format"""
	try:
		doc = get_doc(chunk_id)
		return {"doc": doc}
	except Exception as e:
		return {"doc": {}, "error": f"Failed to get chunk: {str(e)}"}

def call_search_graph(query: str, top_k: int = 10) -> Dict[str, Any]:
	"""Direct call to search_graph with MCP-compatible response format"""
	try:
		res = _search_graph(query, top_k=top_k)
		return {"results": res}
	except Exception as e:
		return {"results": [], "error": f"Graph search failed: {str(e)}"}

def call_run_backtest(params: Dict[str, Any], universe: List[str], start: str, end: str) -> Dict[str, Any]:
	"""Direct backtest implementation from mcp_quant.py logic"""
	try:
		prices = get_prices(universe, start, end, source=None, limit=None)
		df = pd.DataFrame(prices)
		if df.empty:
			return {"metrics": {}, "note": "no data"}
		
		df['timestamp'] = pd.to_datetime(df['timestamp'])
		wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
		
		try:
			import vectorbt as vbt
			if params.get('strategy', 'ma_cross') == 'ma_cross':
				short = int(params.get('ma_short', 10))
				long = int(params.get('ma_long', 30))
				fast = wide.vbt.rolling_mean(window=short)
				slow = wide.vbt.rolling_mean(window=long)
				entries = fast > slow
				exits = fast < slow
				pf = vbt.Portfolio.from_signals(wide, entries, exits, fees=0.0005, slippage=0.0005, freq='D')
				stats = pf.stats()
				metrics = {
					"total_return": float(stats.get('Total Return [%]', np.nan))/100.0 if 'Total Return [%]' in stats else float(pf.total_return()),
					"cagr": float(stats.get('CAGR [%]', np.nan))/100.0 if 'CAGR [%]' in stats else float(pf.annualized_return()),
					"sharpe": float(stats.get('Sharpe Ratio', np.nan)) if 'Sharpe Ratio' in stats else float(pf.sharpe_ratio()),
					"max_drawdown": float(stats.get('Max Drawdown [%]', np.nan))/100.0 if 'Max Drawdown [%]' in stats else float(pf.max_drawdown()),
				}
				return {"metrics": metrics}
		except ImportError:
			pass
		
		# Fallback: equal-weight daily rebalanced
		rets = wide.pct_change().dropna()
		if rets.empty:
			return {"metrics": {}}
		w = np.ones(len(rets.columns)) / len(rets.columns)
		port = (rets.fillna(0) @ w)
		equity = (1 + port).cumprod()
		n = len(port)
		metrics = {
			"total_return": float(equity.iloc[-1] - 1.0),
			"cagr": float(equity.iloc[-1] ** (252/max(n,1)) - 1.0),
			"sharpe": float(port.mean()/ (port.std() + 1e-12) * np.sqrt(252)),
			"max_drawdown": float(((equity / equity.cummax()) - 1.0).min()),
		}
		return {"metrics": metrics}
	except Exception as e:
		return create_fallback_response("/run_backtest", {"params": params, "universe": universe}, str(e))

def call_compute_var(method: str, horizon_days: int, paths: int, assets: List[str], start: str, end: str, alpha: float = 0.95) -> Dict[str, Any]:
	"""Direct VaR computation from mcp_risk.py logic"""
	try:
		prices = get_prices(assets, start, end, source=None, limit=None)
		df = pd.DataFrame(prices)
		if df.empty:
			return {"var": None, "note": "no data"}
		
		df['timestamp'] = pd.to_datetime(df['timestamp'])
		pivot = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index()
		rets = pivot.pct_change().dropna()
		port = rets.mean(axis=1)
		mu, sigma = float(port.mean()), float(port.std())
		sim = np.random.normal(mu, sigma, size=(paths, horizon_days))
		cum = sim.sum(axis=1)
		var = -np.quantile(cum, 1-alpha)
		return {"var": float(var), "mu": mu, "sigma": sigma}
	except Exception as e:
		return create_fallback_response("/compute_var", {"assets": assets}, str(e))

def call_optimize_portfolio(method: str, assets: List[str], constraints: Dict[str, Any], start: str, end: str) -> Dict[str, Any]:
	"""Direct portfolio optimization from mcp_allocator.py logic"""
	try:
		px = get_prices(assets, start, end, source=None, limit=None)
		df = pd.DataFrame(px)
		if df.empty:
			return {"weights": {}, "method": method, "note": "no data"}
		
		df['timestamp'] = pd.to_datetime(df['timestamp'])
		wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
		rets = wide.pct_change().dropna()
		
		min_w = float(constraints.get("min_weight", 0.0))
		max_w = float(constraints.get("max_weight", 1.0))
		
		if method.upper() in {"MEANVAR", "MEAN_VAR", "MV"}:
			try:
				from pypfopt import EfficientFrontier, risk_models, expected_returns
				mu = expected_returns.mean_historical_return(wide, frequency=252)
				S = risk_models.CovarianceShrinkage(wide).ledoit_wolf()
				ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))
				w = ef.max_sharpe()
				weights = ef.clean_weights()
				perf = ef.portfolio_performance(verbose=False)
				return {"weights": weights, "method": "MeanVar", "metrics": {"ret": float(perf[0]), "vol": float(perf[1]), "sharpe": float(perf[2])}}
			except ImportError:
				pass
		
		if method.upper() == "HRP":
			try:
				from pypfopt.hierarchical_portfolio import HRPOpt
				hrp = HRPOpt(returns=rets)
				weights = hrp.optimize()
				return {"weights": {k: float(v) for k, v in weights.items()}, "method": "HRP"}
			except ImportError:
				pass
		
		n = len(assets) or 1
		w = 1.0 / n
		weights = {a: w for a in assets}
		return {"weights": weights, "method": method, "note": "fallback"}
	except Exception as e:
		return create_fallback_response("/optimize_portfolio", {"symbols": assets}, str(e))

def build_price_payload(symbols: List[str], start: str, end: str) -> Dict[str, Any]:
	"""Build price payload for Modal functions from database"""
	try:
		prices = get_prices(symbols, start, end, source=None, limit=None)
		if not prices:
			return {}
			
		df = pd.DataFrame(prices)
		df['timestamp'] = pd.to_datetime(df['timestamp'])
		wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
		
		return {
			"symbols": list(wide.columns),
			"timestamps": [str(t) for t in wide.index],
			"prices": wide.values.tolist()
		}
	except Exception as e:
		return {}


def plan_node(state: AgentState) -> AgentState:
	system = (
		"You orchestrate financial tasks by choosing: search_corpus, get_chunk, run_backtest, "
		"grid_scan, compute_var, stress_test, optimize_portfolio. Return a JSON with 'intent' and 'payload'."
	)
	user = f"User: {state['query']}\nReturn a JSON with 'intent' and 'payload'."
	
	intent = "search_corpus"
	payload = {"query": state["query"], "top_k": 10}
	out = "Fallback: Using default search_corpus intent"
	
	try:
		out = chat(
			[{"role":"system","content":system}, {"role":"user","content":user}],
			model=os.getenv("OPENAI_PLANNER_MODEL") or os.getenv("OPENAI_MODEL"),
			temperature=0.1
		)
		m = re.search(r"\{.*\}", out, re.S)
		if m:
			try:
				o = json.loads(m.group(0))
				intent, payload = o.get("intent", intent), o.get("payload", payload)
			except Exception:
				pass
	except Exception as e:
		query_lower = state["query"].lower()
		if any(word in query_lower for word in ["grid", "scan", "parameter", "sweep", "optimize parameters"]):
			intent = "grid_scan"
			payload = {"universe": ["AAPL"], "start": "2023-01-01", "end": "2023-12-31", "param_grid": {"ma_short": [10, 20], "ma_long": [30, 50]}}
		elif any(word in query_lower for word in ["backtest", "test", "strategy"]):
			intent = "run_backtest"
			payload = {"universe": ["AAPL"], "start": "2023-01-01", "end": "2023-12-31", "params": {"strategy": "ma_cross", "ma_short": 10, "ma_long": 30}}
		elif any(word in query_lower for word in ["risk", "var", "volatility"]):
			intent = "compute_var"
			payload = {"assets": ["AAPL", "GOOGL"], "start": "2023-01-01", "end": "2023-12-31", "alpha": 0.95}
		elif any(word in query_lower for word in ["optimize", "allocation", "portfolio"]):
			intent = "optimize_portfolio"
			payload = {"symbols": ["AAPL", "GOOGL", "MSFT"], "start": "2023-01-01", "end": "2023-12-31"}
		else:
			intent = "search_corpus"
			payload = {"query": state["query"], "top_k": 10}
		out = f"Fallback intent detection: {intent} (OpenAI API error: {str(e)})"
	
	state["intent"] = intent
	state["result"] = {"planner": out, "payload": payload}
	return state


def route_node(state: AgentState) -> AgentState:
	intent = state.get("intent","search_corpus")
	payload = state.get("result",{}).get("payload", {})
	state["plan"] = intent
	state["error"] = None
	state["context"] = []
	state["result"] = {"payload": payload}
	return state


async def librarian_node(state: AgentState) -> AgentState:
	q = state.get("result",{}).get("payload",{}).get("query") or state["query"]
	top_k = state.get("result",{}).get("payload",{}).get("top_k", 10)
	sources = state.get("result",{}).get("payload",{}).get("sources")
	res = call_search_corpus(q, top_k=top_k, alpha=0.5, rerank=True, sources=sources)
	state["context"] = res.get("results", [])
	state["result"] = res
	return state


async def quant_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	intent = state.get("intent", "run_backtest")
	
	if intent == "grid_scan" and USE_MODAL:
		symbols = pl.get("universe", ["AAPL"])
		start = pl.get("start", "2023-01-01")
		end = pl.get("end", "2023-12-31")
		param_grid = pl.get("param_grid", {"ma_short": [10, 20], "ma_long": [30, 50]})
		
		price_payload = build_price_payload(symbols, start, end)
		if price_payload:
			modal_payload = {
				"param_grid": param_grid,
				"price_payload": price_payload
			}
			res = await call_modal_endpoint(MODAL_GRID_SCAN_URL, modal_payload)
		else:
			results = []
			ma_short = param_grid.get('ma_short', [10])
			ma_long = param_grid.get('ma_long', [30])
			for s in ma_short:
				for l in ma_long:
					backtest_res = call_run_backtest({'strategy':'ma_cross','ma_short':s,'ma_long':l}, symbols, start, end)
					results.append({"params": {"ma_short": s, "ma_long": l}, "metrics": backtest_res.get("metrics",{})})
			res = {"status": "done", "results": results}
	else:
		params = pl.get("params", {"strategy": "ma_cross", "ma_short": 10, "ma_long": 30})
		universe = pl.get("universe", ["AAPL"])
		start = pl.get("start", "2023-01-01")
		end = pl.get("end", "2023-12-31")
		res = call_run_backtest(params, universe, start, end)
	
	state["result"] = res
	return state


async def risk_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	intent = state.get("intent", "compute_var")
	
	if intent == "compute_var" and USE_MODAL:
		assets = pl.get("assets", pl.get("portfolio", ["AAPL", "GOOGL"]))
		start = pl.get("start", "2023-01-01")
		end = pl.get("end", "2023-12-31")
		
		price_payload = build_price_payload(assets, start, end)
		if price_payload:
			modal_payload = {
				"price_payload": price_payload,
				"alpha": pl.get("alpha", pl.get("confidence_level", 0.95)),
				"horizon_days": pl.get("horizon_days", 10),
				"paths": pl.get("paths", 1000)
			}
			res = await call_modal_endpoint(MODAL_VAR_URL, modal_payload)
		else:
			method = pl.get("method", "mc")
			horizon_days = pl.get("horizon_days", 10)
			paths = pl.get("paths", 1000)
			alpha = pl.get("alpha", pl.get("confidence_level", 0.95))
			res = call_compute_var(method, horizon_days, paths, assets, start, end, alpha)
	else:
		if intent == "compute_var":
			method = pl.get("method", "mc")
			horizon_days = pl.get("horizon_days", 10)
			paths = pl.get("paths", 1000)
			assets = pl.get("assets", ["AAPL", "GOOGL"])
			start = pl.get("start", "2023-01-01")
			end = pl.get("end", "2023-12-31")
			alpha = pl.get("alpha", 0.95)
			res = call_compute_var(method, horizon_days, paths, assets, start, end, alpha)
		else:
			res = {"scenarios": [], "note": "stress test not implemented in direct tools"}
	
	state["result"] = res
	return state


async def alloc_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	
	if USE_MODAL:
		symbols = pl.get("symbols", ["AAPL", "GOOGL", "MSFT"])
		start = pl.get("start", "2023-01-01")
		end = pl.get("end", "2023-12-31")
		
		price_payload = build_price_payload(symbols, start, end)
		if price_payload:
			modal_payload = {
				"price_payload": price_payload,
				"method": pl.get("method", "HRP"),
				"constraints": pl.get("constraints", {})
			}
			res = await call_modal_endpoint(MODAL_OPTIMIZE_URL, modal_payload)
		else:
			method = pl.get("method", "HRP")
			constraints = pl.get("constraints", {})
			res = call_optimize_portfolio(method, symbols, constraints, start, end)
	else:
		method = pl.get("method", "HRP")
		symbols = pl.get("symbols", ["AAPL", "GOOGL", "MSFT"])
		start = pl.get("start", "2023-01-01")
		end = pl.get("end", "2023-12-31")
		constraints = pl.get("constraints", {})
		res = call_optimize_portfolio(method, symbols, constraints, start, end)
	
	state["result"] = res
	return state


def build_graph():
	g = StateGraph(AgentState)
	g.add_node("plan", plan_node)
	g.add_node("route", route_node)
	g.add_node("librarian", librarian_node)
	g.add_node("quant", quant_node)
	g.add_node("risk", risk_node)
	g.add_node("alloc", alloc_node)

	g.add_edge(START, "plan")
	g.add_edge("plan", "route")

	def choose_next(state: AgentState):
		intent = state.get("intent","search_corpus")
		if intent in {"search_corpus", "get_chunk"}:
			return "librarian"
		if intent in {"run_backtest", "grid_scan"}:
			return "quant"
		if intent in {"compute_var", "stress_test"}:
			return "risk"
		if intent in {"optimize_portfolio"}:
			return "alloc"
		return "librarian"

	g.add_conditional_edges("route", choose_next, {"librarian":"librarian","quant":"quant","risk":"risk","alloc":"alloc"})
	g.add_edge("librarian", END)
	g.add_edge("quant", END)
	g.add_edge("risk", END)
	g.add_edge("alloc", END)
	return g.compile()            