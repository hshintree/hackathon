from typing import List, Dict, Any
import os, requests


def _modal_url() -> str:
	return os.getenv("MODAL_GRAPH_URL", os.getenv("MODAL_APP_URL", "https://your-modal-app.modal.run"))


def build_index(limit: int | None = None) -> Dict[str, Any]:
	url = f"{_modal_url()}/trigger_graph_build"
	payload = {"limit": limit}
	r = requests.post(url, json=payload, timeout=30)
	r.raise_for_status()
	return r.json()


def search_graph(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
	url = f"{_modal_url()}/query_graph"
	payload = {"query": query, "top_k": top_k}
	r = requests.post(url, json=payload, timeout=30)
	r.raise_for_status()
	return r.json().get("results", []) 