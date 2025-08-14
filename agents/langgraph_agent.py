from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import os, httpx, json, re
from llm_client import chat

LIB_URL = os.getenv("MCP_LIBRARIAN_URL", "http://localhost:8001")
DATA_URL = os.getenv("MCP_DATA_URL", "http://localhost:8002")
QUANT_URL = os.getenv("MCP_QUANT_URL", "http://localhost:8003")
RISK_URL = os.getenv("MCP_RISK_URL", "http://localhost:8004")
ALLOC_URL = os.getenv("MCP_ALLOC_URL", "http://localhost:8005")


class AgentState(TypedDict, total=False):
	query: str
	intent: str
	context: List[Dict[str, Any]]
	plan: str
	result: Dict[str, Any]
	error: Optional[str]


async def call_tool(url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
	async with httpx.AsyncClient(timeout=60.0) as client:
		r = await client.post(f"{url}{path}", json=payload)
		r.raise_for_status()
		return r.json()


def plan_node(state: AgentState) -> AgentState:
	system = (
		"You orchestrate financial tasks by choosing: search_corpus, get_chunk, run_backtest, "
		"grid_scan, compute_var, stress_test, optimize_portfolio. Return a JSON with 'intent' and 'payload'."
	)
	user = f"User: {state['query']}\nReturn a JSON with 'intent' and 'payload'."
	out = chat(
		[{"role":"system","content":system}, {"role":"user","content":user}],
		model=os.getenv("OPENAI_PLANNER_MODEL") or os.getenv("OPENAI_MODEL"),
		temperature=0.1
	)
	m = re.search(r"\{.*\}", out, re.S)
	intent = "search_corpus"; payload = {"query": state["query"], "top_k": 10}
	if m:
		try:
			o = json.loads(m.group(0))
			intent, payload = o.get("intent", intent), o.get("payload", payload)
		except Exception:
			pass
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
	res = await call_tool(QUANT_URL, "/tools/run_backtest", pl)
	state["result"] = res
	return state


async def risk_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
	if state["intent"] == "compute_var":
		path = "/tools/compute_var"
	else:
		path = "/tools/stress_test"
	res = await call_tool(RISK_URL, path, pl)
	state["result"] = res
	return state


async def alloc_node(state: AgentState) -> AgentState:
	pl = state.get("result",{}).get("payload",{})
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