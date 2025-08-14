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
    "requests",
    "websockets",
    "psycopg2-binary",
    "pgvector",
    "pyarrow",
    "fastapi",
    "pydantic",
    # Added for embedding/chunking
    "transformers",
    "sentence-transformers",
    "torch",
    "beautifulsoup4",
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
