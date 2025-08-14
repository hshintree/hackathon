from typing import Dict, Any

from .retrieval_tools import search_text, get_doc
from .quant_tools import run_backtest, grid_scan
from .risk_tools import compute_var, stress_test
from .alloc_tools import optimize_portfolio


def handle_intent(intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
	"""Route high-level intents to the appropriate tool."""
	if intent == "search_corpus":
		q = payload.get("query","")
		k = int(payload.get("top_k", 20))
		alpha = float(payload.get("alpha", 0.5))
		return {"results": search_text(q, top_k=k, alpha=alpha)}
	if intent in ("get_doc", "get_chunk"):
		cid = int(payload.get("chunk_id") or payload.get("id"))
		return {"doc": get_doc(cid)}
	if intent == "run_backtest":
		return run_backtest(payload.get("params",{}), payload.get("universe",[]), payload.get("start"), payload.get("end"))
	if intent == "grid_scan":
		return grid_scan(payload.get("param_grid",{}), payload.get("universe",[]), payload.get("start"), payload.get("end"))
	if intent == "compute_var":
		return compute_var(payload.get("method","mc"), int(payload.get("horizon_days",10)), int(payload.get("paths",1000)), payload.get("assets",[]))
	if intent == "stress_test":
		return stress_test(payload.get("scenarios",[]), payload.get("assets",[]))
	if intent == "optimize_portfolio":
		return optimize_portfolio(payload.get("method","HRP"), payload.get("assets",[]), payload.get("constraints",{}))
	return {"error": f"unknown intent {intent}"} 