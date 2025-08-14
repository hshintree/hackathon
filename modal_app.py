import modal
import os
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import json
import uuid
import numpy as np

app = modal.App("trading-agent-data")

volume = modal.Volume.from_name("trading-data", create_if_missing=True)
secrets = modal.Secret.from_name("trading-secrets")

image = modal.Image.debian_slim().pip_install([
    "alpaca-py",
    "pandas",
    "numpy",
    "scipy",
    "requests",
    "websockets",
    "psycopg2-binary",
    "pgvector",
    "pyarrow",
    "fastapi",
    "pydantic",
    # ML / NLP
    "transformers",
    "sentence-transformers",
    "torch",
    "beautifulsoup4",
    # Portfolio optimization
    "pypfopt",
])

@app.function(image=image, secrets=[secrets], timeout=600)
def embed_texts_384(texts: list, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> list:
    """Return 384-d embeddings for a list of strings."""
    from transformers import AutoTokenizer, AutoModel
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    embeddings = []
    batch_size = 64
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        with torch.no_grad():
            inputs = tokenizer(batch, padding=True, truncation=True, return_tensors="pt")
            outputs = model(**inputs)
            last_hidden = outputs.last_hidden_state
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked = last_hidden * attention_mask
            sum_embeddings = masked.sum(dim=1)
            sum_mask = attention_mask.sum(dim=1)
            vecs = (sum_embeddings / sum_mask).cpu().tolist()
            embeddings.extend(vecs)
    return embeddings

# Existing ingestion functions below

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/data": volume},
    timeout=3600
)
def ingest_market_data(symbols: list, start_date: str, end_date: str):
    """Ingest market data from Alpaca and store in Parquet format"""
    from data_sources.alpaca_client import AlpacaClient
    
    client = AlpacaClient()
    data = client.get_historical_data(symbols, start_date, end_date)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/data/market_data/alpaca_{timestamp}.parquet"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data.to_parquet(filename)
    
    volume.commit()
    return {"status": "success", "file": filename, "records": len(data)}

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/data": volume},
    timeout=7200
)
def ingest_sec_filings(cik_list: list = None, forms: list = None):
    """Ingest SEC EDGAR filings and store in Parquet format"""
    from data_sources.sec_edgar_client import SECEdgarClient
    
    client = SECEdgarClient()
    data = client.get_company_filings(cik_list, forms)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/data/sec_filings/edgar_{timestamp}.parquet"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data.to_parquet(filename)
    
    volume.commit()
    return {"status": "success", "file": filename, "records": len(data)}

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/data": volume},
    timeout=1800
)
def ingest_macro_data(series_ids: list, start_date: str, end_date: str):
    """Ingest macro data from FRED and store in Parquet format"""
    from data_sources.fred_client import FREDClient
    
    client = FREDClient()
    data = client.get_series_data(series_ids, start_date, end_date)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/data/macro_data/fred_{timestamp}.parquet"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data.to_parquet(filename)
    
    volume.commit()
    return {"status": "success", "file": filename, "records": len(data)}

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/data": volume},
    timeout=86400
)
async def ingest_crypto_data(symbols: list, duration_hours: int = 24):
    """Ingest crypto data from Binance websockets and store in Parquet format"""
    from data_sources.binance_client import BinanceClient
    
    client = BinanceClient()
    data = await client.collect_websocket_data(symbols, duration_hours)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/data/crypto_data/binance_{timestamp}.parquet"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data.to_parquet(filename)
    
    volume.commit()
    return {"status": "success", "file": filename, "records": len(data)}

# ---------- Modal analytics endpoints ----------

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=3600)
def grid_scan_parent(param_grid: dict, price_payload: dict) -> dict:
    ts = price_payload.get("timestamps", [])
    syms = price_payload.get("symbols", [])
    mat = price_payload.get("prices", [])  # rows align to ts, columns to syms
    if not ts or not syms or not mat:
        return {"error": "missing price payload"}
    df = pd.DataFrame(mat, index=pd.to_datetime(ts), columns=syms).sort_index()
    results = []
    ma_short = param_grid.get("ma_short", [10])
    ma_long = param_grid.get("ma_long", [30])
    for s in ma_short:
        for l in ma_long:
            fast = df.rolling(window=int(s)).mean()
            slow = df.rolling(window=int(l)).mean()
            entries = (fast > slow).shift(1).fillna(False)
            rets = df.pct_change().fillna(0)
            port = (rets * entries.astype(float)).mean(axis=1)
            equity = (1 + port).cumprod()
            n = len(port)
            cagr = float(equity.iloc[-1] ** (252/max(n,1)) - 1.0) if n>0 else 0.0
            sharpe = float(port.mean() / (port.std() + 1e-12) * np.sqrt(252)) if n>0 else 0.0
            mdd = float(((equity / equity.cummax()) - 1.0).min()) if n>0 else 0.0
            results.append({"params": {"ma_short": s, "ma_long": l}, "metrics": {"cagr": cagr, "sharpe": sharpe, "max_drawdown": mdd}})
    out = {
        "symbols": syms,
        "timestamps": [str(t) for t in df.index],
        "results": results,
        "created_at": datetime.utcnow().isoformat(),
    }
    os.makedirs("/data/results", exist_ok=True)
    path = f"/data/results/grid_{uuid.uuid4().hex}.json"
    with open(path, "w") as f:
        json.dump(out, f)
    volume.commit()
    return {"status": "ok", "path": path, "count": len(results)}

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=1200)
def var_mc(price_payload: dict, alpha: float = 0.95, horizon_days: int = 10, paths: int = 1000) -> dict:
    ts = price_payload.get("timestamps", [])
    syms = price_payload.get("symbols", [])
    mat = price_payload.get("prices", [])
    if not ts or not syms or not mat:
        return {"error": "missing price payload"}
    df = pd.DataFrame(mat, index=pd.to_datetime(ts), columns=syms).sort_index()
    rets = df.pct_change().dropna()
    if rets.empty:
        return {"error": "no returns"}
    port = rets.mean(axis=1)
    mu, sigma = float(port.mean()), float(port.std())
    sim = np.random.normal(mu, sigma, size=(paths, horizon_days))
    cum = sim.sum(axis=1)
    var = float(-np.quantile(cum, 1 - alpha))
    out = {"alpha": alpha, "horizon_days": horizon_days, "paths": paths, "var": var}
    os.makedirs("/data/results", exist_ok=True)
    path = f"/data/results/var_{uuid.uuid4().hex}.json"
    with open(path, "w") as f:
        json.dump(out, f)
    volume.commit()
    return {"status": "ok", "path": path, "metrics": out}

# ---------- GraphRAG (NER-based lightweight) ----------

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=36000)
def build_graph_index(limit: int = None) -> dict:
    """Build a lightweight entity co-occurrence graph index from text_chunks in Postgres.
    Stores index at /data/graphrag/index.json with:
      - entity_to_chunk_ids: {entity: [chunk_id,...]}
      - chunk_meta: {chunk_id: {id, source, symbol, document_id, chunk_index, content}}
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from transformers import pipeline
    os.makedirs("/data/graphrag", exist_ok=True)

    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        port=os.getenv("PGPORT", 5432),
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    q = "select id, source, symbol, document_id, chunk_index, content from text_chunks order by id asc"
    if limit:
        q += f" limit {int(limit)}"
    cur.execute(q)
    rows = cur.fetchall()
    cur.close(); conn.close()

    nlp = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")

    entity_to_chunk_ids = {}
    chunk_meta = {}
    for r in rows:
        cid = int(r["id"])  # type: ignore
        text = (r.get("content") or "")[:1500]
        ents = nlp(text)
        # normalize entities
        uniq = set()
        for e in ents:
            label = str(e.get("word") or e.get("entity_group") or "").strip()
            if not label:
                continue
            norm = label.upper()
            uniq.add(norm)
        for ent in uniq:
            entity_to_chunk_ids.setdefault(ent, []).append(cid)
        chunk_meta[str(cid)] = {
            "id": cid,
            "source": r.get("source"),
            "symbol": r.get("symbol"),
            "document_id": r.get("document_id"),
            "chunk_index": r.get("chunk_index"),
            "content": r.get("content"),
        }
    index = {"entity_to_chunk_ids": entity_to_chunk_ids, "chunk_meta": chunk_meta}
    path = "/data/graphrag/index.json"
    with open(path, "w") as f:
        json.dump(index, f)
    volume.commit()
    return {"status": "ok", "path": path, "entities": len(entity_to_chunk_ids)}

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=600)
def query_graph_index(query: str, top_k: int = 20) -> dict:
    """Query the entity graph index by NER over the query and return top-k matching chunks.
    Ranking: number of matched entities per chunk, tie-broken by chunk_id asc.
    """
    from transformers import pipeline
    path = "/data/graphrag/index.json"
    if not os.path.exists(path):
        return {"results": []}
    with open(path, "r") as f:
        index = json.load(f)
    e2c = index.get("entity_to_chunk_ids", {})
    meta = index.get("chunk_meta", {})

    nlp = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
    ents = nlp(query)
    query_ents = set()
    for e in ents:
        label = str(e.get("word") or e.get("entity_group") or "").strip()
        if not label:
            continue
        query_ents.add(label.upper())
    # score chunks
    scores = {}
    for ent in query_ents:
        for cid in e2c.get(ent, []):
            scores[cid] = scores.get(cid, 0) + 1
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:max(1, int(top_k))]
    results = []
    for cid, s in ranked:
        m = meta.get(str(cid)) or {}
        m["graph_score"] = float(s)
        results.append(m)
    return {"results": results}

# ---------- Web endpoints ----------

@app.web_endpoint(method="POST")
def trigger_market_data_ingestion(request_data: dict):
    """Web endpoint to trigger market data ingestion"""
    symbols = request_data.get("symbols", ["AAPL", "GOOGL", "MSFT"])
    start_date = request_data.get("start_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
    end_date = request_data.get("end_date", datetime.now().strftime("%Y-%m-%d"))
    
    job = ingest_market_data.spawn(symbols, start_date, end_date)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def trigger_sec_ingestion(request_data: dict):
    """Web endpoint to trigger SEC filings ingestion"""
    cik_list = request_data.get("cik_list")
    forms = request_data.get("forms", ["10-K", "10-Q"])
    
    job = ingest_sec_filings.spawn(cik_list, forms)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def trigger_macro_ingestion(request_data: dict):
    """Web endpoint to trigger macro data ingestion"""
    series_ids = request_data.get("series_ids", ["GDP", "UNRATE", "CPIAUCSL"])
    start_date = request_data.get("start_date", (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
    end_date = request_data.get("end_date", datetime.now().strftime("%Y-%m-%d"))
    
    job = ingest_macro_data.spawn(series_ids, start_date, end_date)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def trigger_crypto_ingestion(request_data: dict):
    """Web endpoint to trigger crypto data ingestion"""
    symbols = request_data.get("symbols", ["BTCUSDT", "ETHUSDT"])
    duration_hours = request_data.get("duration_hours", 24)
    
    job = ingest_crypto_data.spawn(symbols, duration_hours)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def trigger_graph_build(request_data: dict):
    """Web endpoint to trigger GraphRAG index build"""
    limit = request_data.get("limit")
    job = build_graph_index.spawn(limit)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def query_graph(request_data: dict):
    """Web endpoint to query GraphRAG index with a text query"""
    q = request_data.get("query", "")
    top_k = int(request_data.get("top_k", 20))
    res = query_graph_index.call(q, top_k)
    return res

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=2400)
def grid_scan_child(param_list: list, price_payload: dict) -> dict:
    """Child job: run a batch of MA-cross backtests over param_list and write results to a shard file."""
    ts = price_payload.get("timestamps", [])
    syms = price_payload.get("symbols", [])
    mat = price_payload.get("prices", [])
    if not ts or not syms or not mat:
        return {"error": "missing price payload"}
    df = pd.DataFrame(mat, index=pd.to_datetime(ts), columns=syms).sort_index()
    results = []
    for params in param_list:
        s = int(params.get("ma_short", 10))
        l = int(params.get("ma_long", 30))
        fast = df.rolling(window=s).mean()
        slow = df.rolling(window=l).mean()
        entries = (fast > slow).shift(1).fillna(False)
        rets = df.pct_change().fillna(0)
        port = (rets * entries.astype(float)).mean(axis=1)
        equity = (1 + port).cumprod()
        n = len(port)
        cagr = float(equity.iloc[-1] ** (252/max(n,1)) - 1.0) if n>0 else 0.0
        sharpe = float(port.mean() / (port.std() + 1e-12) * np.sqrt(252)) if n>0 else 0.0
        mdd = float(((equity / equity.cummax()) - 1.0).min()) if n>0 else 0.0
        results.append({"params": {"ma_short": s, "ma_long": l}, "metrics": {"cagr": cagr, "sharpe": sharpe, "max_drawdown": mdd}})
    os.makedirs("/data/results/shards", exist_ok=True)
    path = f"/data/results/shards/grid_{uuid.uuid4().hex}.json"
    with open(path, "w") as f:
        json.dump({"results": results}, f)
    volume.commit()
    return {"status": "ok", "path": path, "count": len(results)}

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=3600)
def grid_scan_parent_mapreduce(param_grid: dict, price_payload: dict, shard_size: int = 50) -> dict:
    """Parent job: shard parameter combinations across many child jobs, then aggregate results."""
    # enumerate combinations
    shorts = [int(x) for x in param_grid.get("ma_short", [10])]
    longs = [int(x) for x in param_grid.get("ma_long", [30])]
    combos = [{"ma_short": s, "ma_long": l} for s in shorts for l in longs]
    if not combos:
        return {"error": "no params"}
    # shard
    shards = [combos[i:i+max(1, int(shard_size))] for i in range(0, len(combos), max(1, int(shard_size)))]
    # spawn children
    calls = []
    for chunk in shards:
        calls.append(grid_scan_child.spawn(chunk, price_payload))
    # wait and collect
    shard_paths = []
    for c in calls:
        try:
            res = c.get()
            if isinstance(res, dict) and res.get("path"):
                shard_paths.append(res["path"])
        except Exception:
            pass
    # aggregate
    all_results = []
    for p in shard_paths:
        try:
            with open(p, "r") as f:
                data = json.load(f)
                all_results.extend(data.get("results", []))
        except Exception:
            continue
    out = {
        "shards": shard_paths,
        "results": all_results,
        "created_at": datetime.utcnow().isoformat(),
    }
    os.makedirs("/data/results", exist_ok=True)
    path = f"/data/results/grid_mapreduce_{uuid.uuid4().hex}.json"
    with open(path, "w") as f:
        json.dump(out, f)
    volume.commit()
    return {"status": "ok", "path": path, "count": len(all_results)}

@app.function(image=image, secrets=[secrets], volumes={"/data": volume}, timeout=1200)
def optimize_portfolio_advanced(price_payload: dict, method: str = "HRP", constraints: dict | None = None) -> dict:
    """Advanced optimization using PyPortfolioOpt (HRP/MeanVar/BL)."""
    constraints = constraints or {}
    ts = price_payload.get("timestamps", [])
    syms = price_payload.get("symbols", [])
    mat = price_payload.get("prices", [])
    if not ts or not syms or not mat:
        return {"error": "missing price payload"}
    df = pd.DataFrame(mat, index=pd.to_datetime(ts), columns=syms).sort_index()
    wide = df
    rets = wide.pct_change().dropna()
    if wide.shape[1] == 0 or rets.empty:
        return {"error": "no data"}

    min_w = float(constraints.get("min_weight", 0.0))
    max_w = float(constraints.get("max_weight", 1.0))
    target_return = constraints.get("target_return")

    try:
        m = method.upper()
        if m in {"MEANVAR", "MEAN_VAR", "MV", "MEANVARIANCE"}:
            from pypfopt import EfficientFrontier, risk_models, expected_returns
            mu = expected_returns.mean_historical_return(wide, frequency=252)
            S = risk_models.CovarianceShrinkage(wide).ledoit_wolf()
            ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))
            if target_return is not None:
                ef.efficient_return(float(target_return))
            else:
                ef.max_sharpe()
            weights = ef.clean_weights()
            perf = ef.portfolio_performance(verbose=False)
            return {"weights": weights, "method": "MeanVar", "metrics": {"ret": float(perf[0]), "vol": float(perf[1]), "sharpe": float(perf[2])}}
        if m == "HRP":
            from pypfopt.hierarchical_portfolio import HRPOpt
            hrp = HRPOpt(returns=rets)
            weights = hrp.optimize()
            return {"weights": {k: float(v) for k, v in weights.items()}, "method": "HRP"}
        if m == "BL":
            from pypfopt import black_litterman, risk_models, EfficientFrontier
            mcaps = constraints.get("market_caps")  # {symbol: cap}
            views = constraints.get("views")        # {symbol: view}
            if not mcaps or not isinstance(mcaps, dict):
                return {"error": "market_caps required for BL"}
            S = risk_models.CovarianceShrinkage(wide).ledoit_wolf()
            delta = black_litterman.market_implied_risk_aversion(wide.pct_change().mean())
            prior = black_litterman.market_implied_prior_returns({k: float(v) for k, v in mcaps.items()}, delta, S)
            if views and isinstance(views, dict):
                Q = {k: float(v) for k, v in views.items()}
                bl = black_litterman.BlackLittermanModel(S, pi=prior, absolute_views=Q)
                mu = bl.bl_returns()
            else:
                mu = prior
            ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))
            ef.max_sharpe()
            weights = ef.clean_weights()
            return {"weights": weights, "method": "BL"}
    except Exception as e:
        return {"error": f"optimization failed: {e}"}

    return {"error": f"unknown method {method}"}

# ---------- Web endpoints for compute ----------

@app.web_endpoint(method="POST")
def run_grid_scan(request_data: dict):
    param_grid = request_data.get("param_grid", {"ma_short": [10,20,30], "ma_long": [50,100]})
    price_payload = request_data.get("price_payload")
    shard_size = int(request_data.get("shard_size", 50))
    job = grid_scan_parent_mapreduce.spawn(param_grid, price_payload, shard_size)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def run_var(request_data: dict):
    price_payload = request_data.get("price_payload")
    alpha = float(request_data.get("alpha", 0.95))
    horizon_days = int(request_data.get("horizon_days", 10))
    paths = int(request_data.get("paths", 1000))
    job = var_mc.spawn(price_payload, alpha, horizon_days, paths)
    return {"job_id": job.object_id, "status": "started"}

@app.web_endpoint(method="POST")
def run_optimize(request_data: dict):
    price_payload = request_data.get("price_payload")
    method = request_data.get("method", "HRP")
    constraints = request_data.get("constraints", {})
    job = optimize_portfolio_advanced.spawn(price_payload, method, constraints)
    return {"job_id": job.object_id, "status": "started"}
