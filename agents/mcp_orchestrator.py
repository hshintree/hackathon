from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import requests
import os

from agents.orchestrator import handle_intent as local_handle

app = FastAPI(title="orchestrator-mcp")

LIB_URL = os.getenv("MCP_LIBRARIAN_URL", "http://localhost:8001")
DATA_URL = os.getenv("MCP_DATA_URL", "http://localhost:8002")

class RouteReq(BaseModel):
	intent: str
	payload: Dict[str, Any]

@app.post("/tools/route")
async def route(req: RouteReq):
	# Minimal router: use local tools for now; optionally fan out to HTTP tools
	intent = req.intent
	payload = req.payload
	# Example: forward librarian calls to librarian server if configured
	if intent in {"search_corpus", "get_chunk"} and LIB_URL:
		try:
			if intent == "search_corpus":
				resp = requests.post(f"{LIB_URL}/tools/search_corpus", json={
					"query": payload.get("query",""),
					"top_k": payload.get("top_k",20),
					"sources": payload.get("sources"),
					"alpha": payload.get("alpha",0.5),
					"rerank": payload.get("rerank",False),
				}).json()
				return resp
			elif intent == "get_chunk":
				resp = requests.post(f"{LIB_URL}/tools/get_chunk", json={"id": payload.get("chunk_id")}).json()
				return resp
		except Exception:
			pass
	# Fallback to in-process orchestrator
	return local_handle(intent, payload) 