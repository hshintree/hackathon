import os
from typing import List, Dict, Any, Optional

from sqlalchemy import text

from database.storage import DataStorage

# Load environment variables for DB credentials (works when run as a script)
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	pass

# One-time guards per process
_FTS_READY = False
_VEC_READY = False


def _ensure_fts_column() -> None:
	"""Ensure a tsvector column + GIN index exist for BM25-style search.
	Avoid full-table refresh per call; run once per process.
	"""
	global _FTS_READY
	if _FTS_READY:
		return
	s = DataStorage()
	with s.get_session() as db:
		# Try to create a generated column (best), fall back to plain tsvector
		try:
			db.execute(text("""
				alter table if exists text_chunks
				add column if not exists content_tsv tsvector generated always as (to_tsvector('english', coalesce(content,''))) stored
			"""))
		except Exception:
			# Fallback: plain column + fill nulls only once
			db.execute(text("""
				alter table if exists text_chunks
				add column if not exists content_tsv tsvector
			"""))
			db.execute(text("""
				update text_chunks set content_tsv = to_tsvector('english', coalesce(content,''))
				where content_tsv is null
			"""))
		# Index exists check/create
		db.execute(text("""
			create index if not exists text_chunks_tsv_idx
			on text_chunks using gin(content_tsv)
		"""))
		db.commit()
		_FTS_READY = True


def _ensure_vector_index() -> None:
	"""Ensure an IVF index exists for pgvector ANN.
	Avoid analyze per call; run once per process.
	"""
	global _VEC_READY
	if _VEC_READY:
		return
	s = DataStorage()
	with s.get_session() as db:
		db.execute(text("""
			create index if not exists text_chunks_embedding_ivf
			on text_chunks using ivfflat (embedding vector_cosine_ops)
			with (lists = 100)
		"""))
		db.commit()
		_VEC_READY = True


def _embed_query_384(query: str) -> List[float]:
	"""Embed a single query to 384-dim using the existing ingest embedding path (Modal or local)."""
	from ingest import _embed_texts_384
	vecs = _embed_texts_384([query])
	vec = vecs[0]
	return vec.tolist() if hasattr(vec, "tolist") else list(vec)


def _as_vector_literal(vec: List[float]) -> str:
	"""Serialize a vector to pgvector literal: '[v1, v2, ...]'."""
	return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"


def _dedup_by_docid(rows: List[Dict[str, Any]], allowed_sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
	"""Keep best row per document_id, optionally filtering by source."""
	best: Dict[str, Dict[str, Any]] = {}
	for r in rows:
		if allowed_sources and r.get("source") not in allowed_sources:
			continue
		doc = r.get("document_id")
		if not doc:
			continue
		score = (
			- r.get("rerank_score", float("nan")) if r.get("rerank_score") is not None else None
		)
		# lower is better for dist; we invert rerank above
		if score is None:
			score = r.get("dist")
		if score is None:
			score = 1.0 - float(r.get("bm25", 0.0))
		prev = best.get(doc)
		if prev is None or score < prev.get("__score", float("inf")):
			r2 = dict(r)
			r2["__score"] = score
			best[doc] = r2
	out = list(best.values())
	# sort by our internal score
	out.sort(key=lambda x: x.get("__score", 0.0))
	for r in out:
		r.pop("__score", None)
	return out


def search_dense(query: str, top_n: int = 200) -> List[Dict[str, Any]]:
	_ensure_vector_index()
	q_vec = _embed_query_384(query)
	vec_lit = _as_vector_literal(q_vec)
	s = DataStorage()
	with s.get_session() as db:
		rows = db.execute(text(
			"""
			select id, source, symbol, document_id, chunk_index, content,
			       embedding <-> (:vec)::vector as dist
			from text_chunks
			order by dist asc
			limit :k
			"""
		), {"vec": vec_lit, "k": top_n}).mappings().all()
		return [dict(r) for r in rows]


def search_bm25(query: str, top_n: int = 200) -> List[Dict[str, Any]]:
	_ensure_fts_column()
	s = DataStorage()
	with s.get_session() as db:
		rows = db.execute(text(
			"""
			select id, source, symbol, document_id, chunk_index, content,
			       ts_rank_cd(content_tsv, websearch_to_tsquery('english', :q)) as bm25
			from text_chunks
			where content_tsv @@ websearch_to_tsquery('english', :q)
			order by bm25 desc
			limit :k
			"""
		), {"q": query, "k": top_n}).mappings().all()
		return [dict(r) for r in rows]


def search_hybrid(query: str, alpha: float = 0.5, pool_n: int = 200) -> List[Dict[str, Any]]:
	"""Hybrid retrieval: combine dense ANN and BM25 (top-N pools), merge on IDs, score, return pool."""
	_ensure_vector_index()
	_ensure_fts_column()
	q_vec = _embed_query_384(query)
	vec_lit = _as_vector_literal(q_vec)
	s = DataStorage()
	with s.get_session() as db:
		rows = db.execute(text(
			"""
			with dense as (
			  select id, (embedding <-> (:vec)::vector) as dist
			  from text_chunks
			  order by dist asc
			  limit :pool
			),
			sparse as (
			  select id, ts_rank_cd(content_tsv, websearch_to_tsquery('english', :q)) as bm25
			  from text_chunks
			  where content_tsv @@ websearch_to_tsquery('english', :q)
			  order by bm25 desc
			  limit :pool
			),
			ids as (
			  select id,
			         min(dist) as dist,
			         max(bm25) as bm25
			  from (
			    select id, dist, null::float as bm25 from dense
			    union all
			    select id, null::float as dist, bm25 from sparse
			  ) u
			  group by id
			)
			select t.id, t.source, t.symbol, t.document_id, t.chunk_index, t.content,
			       ids.dist, ids.bm25,
			       (coalesce(ids.dist, 1.0)) * :alpha + (1.0 - least(coalesce(ids.bm25,0),1.0)) * (1 - :alpha) as hybrid_score
			from ids
			join text_chunks t on t.id = ids.id
			order by hybrid_score asc
			limit :pool
			"""
		), {"vec": vec_lit, "q": query, "pool": pool_n, "alpha": alpha}).mappings().all()
		return [dict(r) for r in rows]


def rerank_cross_encoder(query: str, candidates: List[Dict[str, Any]], model_name: str = "BAAI/bge-reranker-large", top_k: int = 20) -> List[Dict[str, Any]]:
	"""Cross-encoder re-ranking. Falls back to MiniLM cross-encoder if BGE unavailable."""
	try:
		from transformers import AutoTokenizer, AutoModelForSequenceClassification
		import torch
		tokenizer = AutoTokenizer.from_pretrained(model_name)
		model = AutoModelForSequenceClassification.from_pretrained(model_name)
	except Exception:
		from transformers import AutoTokenizer, AutoModelForSequenceClassification
		import torch
		model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
		tokenizer = AutoTokenizer.from_pretrained(model_name)
		model = AutoModelForSequenceClassification.from_pretrained(model_name)
	pairs_left = [(query, c.get("content", "")[:3500]) for c in candidates]
	if not pairs_left:
		return []
	inputs = tokenizer([p[0] for p in pairs_left], [p[1] for p in pairs_left], padding=True, truncation=True, return_tensors="pt", max_length=4096)
	with torch.no_grad():
		scores = model(**inputs).logits.squeeze(-1).tolist()
	for c, s in zip(candidates, scores):
		c["rerank_score"] = float(s)
	return sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)[:top_k]


def rerank_with_cohere(query: str, candidates: List[Dict[str, Any]], top_k: int = 20) -> List[Dict[str, Any]]:
	"""Use Cohere Rerank 3.5 if COHERE_API_KEY is available; otherwise return candidates sliced."""
	import os
	api_key = os.getenv("COHERE_API_KEY")
	if not api_key or not candidates:
		return candidates[:top_k]
	try:
		from cohere import Client
		co = Client(api_key)
		docs = [c.get("content", "")[:4000] for c in candidates]
		r = co.rerank(query=query, documents=docs, top_n=min(top_k, len(docs)), model="rerank-3.5")
		for item in r.results:
			idx = item.index
			candidates[idx]["rerank_score"] = float(item.relevance_score)
	except Exception:
		return candidates[:top_k]
	return sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)[:top_k]


def retrieve(query: str, top_k: int = 20, alpha: float = 0.5, use_bm25: bool = False, pool_n: int = 200, rerank: bool = False, rerank_model: str = "BAAI/bge-reranker-large", sources: Optional[List[str]] = None, dedup: bool = True) -> List[Dict[str, Any]]:
	"""End-to-end retrieval: dense-only by default for speed; optional hybrid and re-rank.
	Optionally filter by sources (e.g., ["sec"], ["news"]) and deduplicate per document_id.
	"""
	if use_bm25:
		pool = search_hybrid(query, alpha=alpha, pool_n=pool_n)
	else:
		pool = search_dense(query, top_n=pool_n)
	if not pool:
		return []
	if dedup or sources:
		pool = _dedup_by_docid(pool, allowed_sources=sources)
	if rerank:
		if isinstance(rerank_model, str) and rerank_model.lower().startswith("cohere"):
			pool = rerank_with_cohere(query, pool, top_k=top_k)
		else:
			pool = rerank_cross_encoder(query, pool, model_name=rerank_model, top_k=top_k)
	return pool[:top_k]


# Simple CLI
if __name__ == "__main__":
	import argparse, json
	parser = argparse.ArgumentParser(description="Hybrid retrieval over text_chunks (pgvector + BM25 + rerank)")
	parser.add_argument("query", type=str, help="Query text")
	parser.add_argument("--top-k", type=int, default=10)
	parser.add_argument("--alpha", type=float, default=0.5, help="Weight on dense distance (0..1)")
	parser.add_argument("--no-bm25", action="store_true", help="Disable BM25 (dense only)")
	parser.add_argument("--rerank", action="store_true", help="Enable cross-encoder reranking")
	parser.add_argument("--sources", nargs="*", default=None, help="Filter sources, e.g. sec news")
	parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication by document_id")
	args = parser.parse_args()
	res = retrieve(
		args.query,
		top_k=args.top_k,
		alpha=args.alpha,
		use_bm25=(not args.no_bm25),
		rerank=args.rerank,
		sources=args.sources,
		dedup=(not args.no_dedup),
	)
	for i, r in enumerate(res, 1):
		print(f"{i}. {r.get('source')} {r.get('symbol')} doc={str(r.get('document_id'))[:80]}\n   score={r.get('rerank_score', None)}\n   {r.get('content','')[:200].replace('\n',' ')}\n") 