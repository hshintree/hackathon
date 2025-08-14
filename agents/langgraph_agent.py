from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import os, httpx, json, re
from llm_client import chat

LIB_URL = os.getenv("MCP_LIBRARIAN_URL", "http://localhost:8001")
DATA_URL = os.getenv("MCP_DATA_URL", "http://localhost:8002")
QUANT_URL = os.getenv("MCP_QUANT_URL", "http://localhost:8003")
RISK_URL = os.getenv("MCP_RISK_URL", "http://localhost:8004")
ALLOC_URL = os.getenv("MCP_ALLOC_URL", "http://localhost:8005")

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


async def call_tool(url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
	try:
		async with httpx.AsyncClient(timeout=10.0) as client:
			r = await client.post(f"{url}{path}", json=payload)
			r.raise_for_status()
			return r.json()
	except Exception as e:
		return create_fallback_response(path, payload, str(e))

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

def build_price_payload(symbols: List[str], start: str, end: str) -> Dict[str, Any]:
	"""Build price payload for Modal functions from database"""
	try:
		from agents.retrieval_tools import get_prices
		import pandas as pd
		
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
	res = await call_tool(LIB_URL, "/tools/search_corpus", {"query": q, "top_k": top_k, "alpha": 0.5, "rerank": True})
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
			res = await call_tool(QUANT_URL, "/tools/grid_scan", pl)
	else:
		res = await call_tool(QUANT_URL, "/tools/run_backtest", pl)
	
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
			res = await call_tool(RISK_URL, "/tools/compute_var", pl)
	else:
		path = "/tools/compute_var" if intent == "compute_var" else "/tools/stress_test"
		res = await call_tool(RISK_URL, path, pl)
	
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
			res = await call_tool(ALLOC_URL, "/tools/optimize_portfolio", pl)
	else:
		res = await call_tool(ALLOC_URL, "/tools/optimize_portfolio", pl)
	
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