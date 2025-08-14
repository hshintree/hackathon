from typing import List, Dict, Any

from retrieval_layer import retrieve, search_dense, search_bm25
from sqlalchemy import text
from database.storage import DataStorage


def search_text(query: str, top_k: int = 20, alpha: float = 0.5, use_bm25: bool = True, rerank: bool = True) -> List[Dict[str, Any]]:
	"""Hybrid retrieval with optional reranking."""
	return retrieve(query=query, top_k=top_k, alpha=alpha, use_bm25=use_bm25, rerank=rerank)


def search_dense_only(query: str, top_k: int = 20) -> List[Dict[str, Any]]:
	return search_dense(query, top_n=top_k)


def search_bm25_only(query: str, top_k: int = 20) -> List[Dict[str, Any]]:
	return search_bm25(query, top_n=top_k)


def get_doc(chunk_id: int) -> Dict[str, Any]:
	"""Fetch a chunk row by id."""
	s = DataStorage()
	with s.get_session() as db:
		row = db.execute(text("select id, source, symbol, document_id, chunk_index, content from text_chunks where id=:id"), {"id": chunk_id}).mappings().first()
		return dict(row) if row else {} 