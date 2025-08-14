from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agents.retrieval_tools import search_text, get_doc
from graph_rag import search_graph as _search_graph

app = FastAPI(title="librarian-mcp")

class SearchRequest(BaseModel):
	query: str
	top_k: int = 20 #this is lowkey a lot for now
	sources: Optional[List[str]] = None
	alpha: float = 0.5
	rerank: bool = True

class SearchResponse(BaseModel):
	results: List[Dict[str, Any]]

class GetChunkRequest(BaseModel):
	id: int

class GetChunkResponse(BaseModel):
	doc: Dict[str, Any]

class GraphSearchRequest(BaseModel):
	query: str
	top_k: int = 10

class GraphSearchResponse(BaseModel):
	results: List[Dict[str, Any]]

@app.post("/tools/search_corpus", response_model=SearchResponse)
async def search_corpus(req: SearchRequest):
	res = search_text(req.query, top_k=req.top_k, alpha=req.alpha, use_bm25=True, rerank=req.rerank)
	if req.sources:
		res = [r for r in res if r.get("source") in req.sources]
	return {"results": res}

@app.post("/tools/get_chunk", response_model=GetChunkResponse)
async def get_chunk(req: GetChunkRequest):
	return {"doc": get_doc(req.id)}

@app.post("/tools/search_graph", response_model=GraphSearchResponse)
async def search_graph(req: GraphSearchRequest):
	res = _search_graph(req.query, top_k=req.top_k)
	return {"results": res} 