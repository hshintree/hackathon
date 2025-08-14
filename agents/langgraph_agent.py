from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import os, httpx, json, re
from llm_client import chat
from .orchestrator import handle_intent
from datetime import datetime, timedelta

LIB_URL = os.getenv("MCP_LIBRARIAN_URL", "http://localhost:8001")
DATA_URL = os.getenv("MCP_DATA_URL", "http://localhost:8002")
QUANT_URL = os.getenv("MCP_QUANT_URL", "http://localhost:8003")
RISK_URL = os.getenv("MCP_RISK_URL", "http://localhost:8004")
ALLOC_URL = os.getenv("MCP_ALLOC_URL", "http://localhost:8005")
USE_LOCAL_TOOLS = os.getenv("USE_LOCAL_TOOLS", "1") == "1"


class AgentState(TypedDict, total=False):
	query: str
	intent: str
	context: List[Dict[str, Any]]
	plan: str
	result: Dict[str, Any]
	error: Optional[str]


def _extract_symbols(q: str) -> List[str]:
	# Simple uppercase ticker grab with stopwords
	candidates = re.findall(r"\b[A-Z]{1,5}\b", q.upper())
	stops = {"RUN","BACKTEST","WITH","MA","CROSS","COMPUTE","VAR","FOR","PORTFOLIO","USING","MEANVAR","ON","THE","AND","OR","HOW","HAS","RECENTLY"}
	syms: List[str] = []
	for c in candidates:
		if c not in stops and c not in syms:
			syms.append(c)
	return syms


def _default_dates(days: int = 252) -> Dict[str, str]:
	end = datetime.utcnow().date()
	start = end - timedelta(days=days)
	return {"start": f"{start}T00:00:00", "end": f"{end}T00:00:00"}


def _normalize_intent_and_payload(query: str, intent: str, payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
	ql = query.lower()
	# Rule-based intent correction (order matters)
	# 1) Document/search-centric cues first
	if any(k in ql for k in ["search", "find", "10-k", "10k", "10-q", "10q", "sec", "filing", "document", "chunk", "news", "article", "recent"]):
		intent = "search_corpus"
	# 2) Backtest cues
	bt_cue = any(k in ql for k in ["backtest", "ma cross", "moving average", "grid scan"]) 
	# 3) VaR cues (explicit), avoid generic 'risk' to prevent collisions with 10-K "risks"
	vr_cue = any(k in ql for k in ["var", "value at risk"]) or re.search(r"\bvar\b", ql) is not None
	# 4) Allocation cues
	alloc_cue = any(k in ql for k in ["optimize", "allocation", "weights", "portfolio allocation"]) 
	# Multi-intent: backtest + var in one query
	if bt_cue and vr_cue:
		intent = "backtest_then_var"
	elif alloc_cue and not (bt_cue or vr_cue):
		intent = "optimize_portfolio"
	elif vr_cue and not bt_cue:
		intent = "compute_var"
	elif bt_cue and intent != "search_corpus":
		intent = "run_backtest" if "grid" not in ql else "grid_scan"
	# Populate defaults per intent
	symbols = _extract_symbols(query)
	if intent == "run_backtest":
		pl = dict(payload or {})
		if not pl.get("universe"):
			pl["universe"] = symbols or ["AAPL"]
		if not pl.get("params"):
			pl["params"] = {"strategy": "ma_cross", "ma_short": 10, "ma_long": 30}
		if not pl.get("start") or not pl.get("end"):
			pl |= _default_dates(252)
		return intent, pl
	if intent == "grid_scan":
		pl = dict(payload or {})
		if not pl.get("universe"):
			pl["universe"] = symbols or ["AAPL"]
		if not pl.get("param_grid"):
			pl["param_grid"] = {"ma_short": [5,10,20], "ma_long": [30,50,100]}
		if not pl.get("start") or not pl.get("end"):
			pl |= _default_dates(252)
		return intent, pl
	if intent == "compute_var":
		pl = dict(payload or {})
		if not pl.get("assets"):
			pl["assets"] = symbols or ["AAPL", "MSFT"]
		pl.setdefault("method", "historical")
		pl.setdefault("horizon_days", 10)
		pl.setdefault("paths", 1000)
		return intent, pl
	if intent == "backtest_then_var":
		# Compose payloads for both steps
		pl = dict(payload or {})
		bt = pl.get("backtest") or {}
		vr = pl.get("var") or {}
		# Fill backtest defaults
		if not bt.get("universe"):
			bt["universe"] = symbols or ["AAPL"]
		bt.setdefault("params", {"strategy": "ma_cross", "ma_short": 10, "ma_long": 30})
		if not bt.get("start") or not bt.get("end"):
			bt |= _default_dates(252)
		# Fill var defaults
		if not vr.get("assets"):
			# If AAPL in backtest, and MSFT also in query, include both
			assets = symbols or bt.get("universe", ["AAPL"]) 
			vr["assets"] = assets
		vr.setdefault("method", "historical")
		vr.setdefault("horizon_days", 10)
		vr.setdefault("paths", 1000)
		return intent, {"backtest": bt, "var": vr}
	if intent == "optimize_portfolio":
		pl = dict(payload or {})
		if not pl.get("assets"):
			pl["assets"] = symbols or ["AAPL", "MSFT", "GOOGL"]
		pl.setdefault("method", "MEANVAR")
		pl.setdefault("constraints", {"risk_aversion": 0.5})
		return intent, pl
	if intent in {"search_corpus", "get_chunk"}:
		pl = dict(payload or {})
		pl.setdefault("query", query)
		pl.setdefault("top_k", 10)
		return intent, pl
	return intent, payload or {}


async def call_tool(url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
	try:
		async with httpx.AsyncClient(timeout=10.0) as client:
			r = await client.post(f"{url}{path}", json=payload)
			r.raise_for_status()
			return r.json()
	except Exception as e:
		return create_fallback_response(path, payload, str(e))

def create_fallback_response(path: str, payload: Dict[str, Any], error: str) -> Dict[str, Any]:
	# Do not fabricate results; return an explicit error only
	return {
		"fallback": True,
		"error": f"service unavailable for {path}: {error}"
	}


def plan_node(state: AgentState) -> AgentState:
	system = (
		"You orchestrate financial tasks by choosing: search_corpus, get_chunk, run_backtest, "
		"grid_scan, compute_var, stress_test, optimize_portfolio. Return a JSON with 'intent' and 'payload'."
	)
	user = f"User: {state['query']}\nReturn a JSON with 'intent' and 'payload'."
	
	intent = "search_corpus"
	payload: Dict[str, Any] = {"query": state["query"], "top_k": 10}
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
		# Rule-based fallback if LLM planning fails
		intent = "search_corpus"
		payload = {"query": state["query"], "top_k": 10}
		out = f"Fallback intent detection: {intent} (OpenAI API error: {str(e)})"
	
	# Rule-based correction + payload population
	intent, payload = _normalize_intent_and_payload(state["query"], intent, payload)
	
	state["intent"] = intent
	state["result"] = {"planner": out, "payload": payload}
	return state


def route_node(state: AgentState) -> AgentState:
	intent = state.get("intent","search_corpus")
	payload = state.get("result",{}).get("payload", {})
	# Final guard: ensure payload has defaults
	intent, payload = _normalize_intent_and_payload(state.get("query",""), intent, payload)
	state["plan"] = intent
	state["error"] = None
	state["context"] = []
	state["result"] = {"payload": payload}
	return state


async def librarian_node(state: AgentState) -> AgentState:
	q = state.get("result",{}).get("payload",{}).get("query") or state["query"]
	top_k = state.get("result",{}).get("payload",{}).get("top_k", 10)
	if USE_LOCAL_TOOLS:
		res = handle_intent("search_corpus", {"query": q, "top_k": top_k, "alpha": 0.5, "rerank": True})
	else:
		res = await call_tool(LIB_URL, "/tools/search_corpus", {"query": q, "top_k": top_k, "alpha": 0.5, "rerank": True})
	state["context"] = res.get("results", [])
	state["result"] = res
	return state


async def quant_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	if USE_LOCAL_TOOLS:
		res = handle_intent(state.get("intent", "run_backtest"), pl)
	else:
		res = await call_tool(QUANT_URL, "/tools/run_backtest", pl)
	state["result"] = res
	return state


async def risk_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	if USE_LOCAL_TOOLS:
		res = handle_intent(state.get("intent", "compute_var"), pl)
	else:
		path = "/tools/compute_var" if state["intent"] == "compute_var" else "/tools/stress_test"
		res = await call_tool(RISK_URL, path, pl)
	state["result"] = res
	return state


async def alloc_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	if USE_LOCAL_TOOLS:
		res = handle_intent("optimize_portfolio", pl)
	else:
		res = await call_tool(ALLOC_URL, "/tools/optimize_portfolio", pl)
	state["result"] = res
	return state


async def pipeline_node(state: AgentState) -> AgentState:
	"""Handle combined intents like backtest_then_var with minimal changes."""
	pl = state.get("result",{}).get("payload",{})
	if state.get("intent") == "backtest_then_var":
		bt = pl.get("backtest", {})
		vr = pl.get("var", {})
		if USE_LOCAL_TOOLS:
			bt_res = handle_intent("run_backtest", bt)
			vr_res = handle_intent("compute_var", vr)
		else:
			bt_res = await call_tool(QUANT_URL, "/tools/run_backtest", bt)
			vr_res = await call_tool(RISK_URL, "/tools/compute_var", vr)
		state["result"] = {"backtest": bt_res, "var": vr_res}
		return state
	state["result"] = {"error": "unknown pipeline intent"}
	return state


def build_graph():
	g = StateGraph(AgentState)
	g.add_node("plan", plan_node)
	g.add_node("route", route_node)
	g.add_node("librarian", librarian_node)
	g.add_node("quant", quant_node)
	g.add_node("risk", risk_node)
	g.add_node("alloc", alloc_node)
	g.add_node("pipeline", pipeline_node)

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
		if intent in {"backtest_then_var"}:
			return "pipeline"
		return "librarian"

	g.add_conditional_edges("route", choose_next, {"librarian":"librarian","quant":"quant","risk":"risk","alloc":"alloc","pipeline":"pipeline"})
	g.add_edge("librarian", END)
	g.add_edge("quant", END)
	g.add_edge("risk", END)
	g.add_edge("alloc", END)
	g.add_edge("pipeline", END)
	return g.compile()    