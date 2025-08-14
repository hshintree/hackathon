#!/usr/bin/env python3
"""
CLI for setting up the database and ingesting data from supported sources.

Usage examples:
  - Setup DB (create tables):
      python ingest.py setup-db

  - Ingest Alpaca bars:
      python ingest.py ingest-alpaca --symbols AAPL MSFT --start 2024-01-01 --end 2024-01-10 --timeframe 1Day

  - Ingest SEC filings (many companies):
      python ingest.py ingest-sec-all --forms 10-K 10-Q --per-company-limit 5 --max-companies 200

  - Ingest FRED series:
      python ingest.py ingest-fred --series GDP UNRATE CPIAUCSL --start 2023-01-01 --end 2024-01-01

  - Ingest Binance klines:
      python ingest.py ingest-crypto --symbols BTCUSDT ETHUSDT --interval 1d --limit 1000

  - Ingest Finnhub candles for many US stocks (to MarketData):
      python ingest.py ingest-finnhub --resolution D --start 2015-01-01 --end 2020-12-31 --max-symbols 500
"""

import argparse
import os
import sys
from datetime import datetime
from datetime import timezone as dt_timezone
from typing import List, Optional
from dotenv import load_dotenv

# Load .env early so API keys/DB vars are available
load_dotenv()

from database.schema import create_database_engine, create_tables
from database.storage import DataStorage
from database.schema import TextChunks

# Data source clients
from data_sources.alpaca_client import AlpacaClient
from data_sources.sec_edgar_client import SECEdgarClient
from data_sources.fred_client import FREDClient
from data_sources.binance_client import BinanceClient
from data_sources.finnhub_client import FinnhubClient
from data_sources.alpaca_options_client import AlpacaOptionsClient
from data_sources.alpaca_news_client import AlpacaNewsClient

import asyncio
import time
import math
import pandas as pd
import hashlib


def _now_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def setup_db() -> None:
    print("🔧 Creating tables...")
    engine = create_database_engine()
    create_tables(engine)
    print("✅ Tables created or already exist.")


def ingest_alpaca(symbols: List[str], start: str, end: str, timeframe: str) -> int:
    job_id = _now_id("alpaca")
    storage = DataStorage()
    storage.store_job_status(job_id, "alpaca_bars", "pending", parameters={
        "symbols": symbols, "start": start, "end": end, "timeframe": timeframe
    })
    storage.store_job_status(job_id, "alpaca_bars", "running")
    try:
        client = AlpacaClient()
        df = client.get_historical_data(symbols, start, end, timeframe=timeframe)
        if df is None or df.empty:
            storage.store_job_status(job_id, "alpaca_bars", "completed", results={"records": 0})
            print("ℹ️ No data returned from Alpaca.")
            return 0
        inserted = storage.store_market_data(df, source="alpaca")
        storage.store_job_status(job_id, "alpaca_bars", "completed", results={"records": inserted})
        print(f"✅ Ingested {inserted} Alpaca bar records.")
        return inserted
    except Exception as e:
        storage.store_job_status(job_id, "alpaca_bars", "failed", error_message=str(e))
        raise


def ingest_sec(forms: List[str], limit: int, cik_list: Optional[List[str]] = None) -> int:
    job_id = _now_id("sec")
    storage = DataStorage()
    storage.store_job_status(job_id, "sec_filings", "pending", parameters={
        "forms": forms, "limit": limit, "cik_list": cik_list
    })
    storage.store_job_status(job_id, "sec_filings", "running")
    try:
        client = SECEdgarClient()
        df = client.get_company_filings(cik_list=cik_list, forms=forms, limit=limit)
        if df is None or df.empty:
            storage.store_job_status(job_id, "sec_filings", "completed", results={"records": 0})
            print("ℹ️ No SEC filings returned.")
            return 0
        inserted = storage.store_sec_filings(df)
        storage.store_job_status(job_id, "sec_filings", "completed", results={"records": inserted})
        print(f"✅ Ingested {inserted} SEC filing records.")
        return inserted
    except Exception as e:
        storage.store_job_status(job_id, "sec_filings", "failed", error_message=str(e))
        raise


def ingest_sec_all(forms: List[str], per_company_limit: int, max_companies: Optional[int]) -> int:
    job_id = _now_id("sec-all")
    storage = DataStorage()
    storage.store_job_status(job_id, "sec_filings_bulk", "pending", parameters={
        "forms": forms, "per_company_limit": per_company_limit, "max_companies": max_companies
    })
    storage.store_job_status(job_id, "sec_filings_bulk", "running")
    try:
        client = SECEdgarClient()
        tickers_df = client.get_company_tickers()
        if tickers_df.empty:
            storage.store_job_status(job_id, "sec_filings_bulk", "completed", results={"records": 0})
            print("ℹ️ No companies returned by SEC.")
            return 0
        if max_companies:
            tickers_df = tickers_df.head(max_companies)
        total_inserted = 0
        batch_size = 50
        for i in range(0, len(tickers_df), batch_size):
            batch = tickers_df.iloc[i:i+batch_size]
            cik_list = batch['cik'].tolist()
            df = client.get_company_filings(cik_list=cik_list, forms=forms, limit=per_company_limit)
            if df is not None and not df.empty:
                inserted = storage.store_sec_filings(df)
                total_inserted += inserted
                print(f"✅ SEC filings inserted: +{inserted} (total {total_inserted})")
            time.sleep(0.2)
        storage.store_job_status(job_id, "sec_filings_bulk", "completed", results={"records": total_inserted})
        print(f"✅ Ingested total {total_inserted} SEC filing records across companies.")
        return total_inserted
    except Exception as e:
        storage.store_job_status(job_id, "sec_filings_bulk", "failed", error_message=str(e))
        raise


def ingest_fred(series: List[str], start: Optional[str], end: Optional[str]) -> int:
    job_id = _now_id("fred")
    storage = DataStorage()
    storage.store_job_status(job_id, "fred_series", "pending", parameters={
        "series": series, "start": start, "end": end
    })
    storage.store_job_status(job_id, "fred_series", "running")
    try:
        client = FREDClient()
        df = client.get_series_data(series, start, end)
        if df is None or df.empty:
            storage.store_job_status(job_id, "fred_series", "completed", results={"records": 0})
            print("ℹ️ No FRED data returned.")
            return 0
        inserted = storage.store_macro_data(df)
        storage.store_job_status(job_id, "fred_series", "completed", results={"records": inserted})
        print(f"✅ Ingested {inserted} FRED records.")
        return inserted
    except Exception as e:
        storage.store_job_status(job_id, "fred_series", "failed", error_message=str(e))
        raise


def ingest_crypto(symbols: List[str], interval: str, limit: int) -> int:
    job_id = _now_id("crypto")
    storage = DataStorage()
    storage.store_job_status(job_id, "binance_klines", "pending", parameters={
        "symbols": symbols, "interval": interval, "limit": limit
    })
    storage.store_job_status(job_id, "binance_klines", "running")
    try:
        client = BinanceClient()
        # Fetch sequentially for now
        frames = []
        for sym in symbols:
            df = asyncio.run(client.get_historical_klines(sym, interval=interval, limit=limit))
            frames.append(df)
        data = pd.concat(frames, ignore_index=True) if frames else None
        if data is None or data.empty:
            storage.store_job_status(job_id, "binance_klines", "completed", results={"records": 0})
            print("ℹ️ No Binance kline data returned.")
            return 0
        inserted = storage.store_crypto_data(data)
        storage.store_job_status(job_id, "binance_klines", "completed", results={"records": inserted})
        print(f"✅ Ingested {inserted} Binance kline records.")
        return inserted
    except Exception as e:
        storage.store_job_status(job_id, "binance_klines", "failed", error_message=str(e))
        raise


def ingest_finnhub(resolution: str, start: str, end: str, max_symbols: Optional[int], exchange: str = "US") -> int:
    job_id = _now_id("finnhub")
    storage = DataStorage()
    storage.store_job_status(job_id, "finnhub_candles", "pending", parameters={
        "resolution": resolution, "start": start, "end": end, "max_symbols": max_symbols, "exchange": exchange
    })
    storage.store_job_status(job_id, "finnhub_candles", "running")
    try:
        client = FinnhubClient()
        symbols_df = client.get_stock_symbols(exchange=exchange)
        if symbols_df.empty:
            storage.store_job_status(job_id, "finnhub_candles", "completed", results={"records": 0})
            print("ℹ️ No Finnhub symbols returned.")
            return 0
        # Filter to common stocks in USD on major US exchanges when possible
        if 'type' in symbols_df.columns:
            symbols_df = symbols_df[symbols_df['type'].isin(['Common Stock', 'ETP', 'ADR'])]
        if 'currency' in symbols_df.columns:
            symbols_df = symbols_df[symbols_df['currency'] == 'USD']
        if 'mic' in symbols_df.columns:
            symbols_df = symbols_df[symbols_df['mic'].isin(['XNYS','XNAS','BATS','ARCX','XASE','IEXG','XNGS'])]
        # Keep simple uppercase tickers A-Z up to 5 chars
        if 'symbol' in symbols_df.columns:
            import re
            symbols_df = symbols_df[symbols_df['symbol'].str.match(r'^[A-Z]{1,5}$', na=False)]
        if max_symbols:
            symbols_df = symbols_df.head(max_symbols)
        start_unix = int(pd.Timestamp(start).timestamp())
        end_unix = int(pd.Timestamp(end).timestamp())
        total_inserted = 0
        batch_records: List[pd.DataFrame] = []
        batch_size = 25  # number of symbols per commit
        for idx, row in symbols_df.iterrows():
            symbol = row['symbol'] if 'symbol' in row else row.get('symbol')
            if not symbol:
                continue
            try:
                df = client.get_stock_candles(symbol, resolution, start_unix, end_unix)
                if df is not None and not df.empty:
                    batch_records.append(df)
            except Exception as e:
                print(f"⚠️ Finnhub candles error for {symbol}: {e}")
                continue
            if len(batch_records) >= batch_size:
                data = pd.concat(batch_records, ignore_index=True)
                inserted = storage.store_market_data(data, source="finnhub")
                total_inserted += inserted
                print(f"✅ Finnhub inserted batch: +{inserted} (total {total_inserted})")
                batch_records = []
        # Flush remaining
        if batch_records:
            data = pd.concat(batch_records, ignore_index=True)
            inserted = storage.store_market_data(data, source="finnhub")
            total_inserted += inserted
            print(f"✅ Finnhub inserted final batch: +{inserted} (total {total_inserted})")
        storage.store_job_status(job_id, "finnhub_candles", "completed", results={"records": total_inserted})
        print(f"✅ Ingested total {total_inserted} Finnhub candle records.")
        return total_inserted
    except Exception as e:
        storage.store_job_status(job_id, "finnhub_candles", "failed", error_message=str(e))
        raise


def ingest_alpaca_options(underlyings: List[str], timeframe: str, start_iso: str, end_iso: str, exp_gte: Optional[str], exp_lte: Optional[str], max_contracts: Optional[int]) -> int:
    job_id = _now_id("alpaca-options")
    storage = DataStorage()
    storage.store_job_status(job_id, "alpaca_options", "pending", parameters={
        "underlyings": underlyings, "timeframe": timeframe, "start": start_iso, "end": end_iso,
        "expiration_gte": exp_gte, "expiration_lte": exp_lte, "max_contracts": max_contracts
    })
    storage.store_job_status(job_id, "alpaca_options", "running")
    try:
        client = AlpacaOptionsClient()
        contracts_df = client.list_option_contracts(underlyings, expiration_gte=exp_gte, expiration_lte=exp_lte)
        if contracts_df.empty:
            storage.store_job_status(job_id, "alpaca_options", "completed", results={"records": 0})
            print("ℹ️ No option contracts returned.")
            return 0
        # Normalize types
        if 'expiration_date' in contracts_df.columns:
            contracts_df['expiration_date'] = pd.to_datetime(contracts_df['expiration_date'], errors='coerce')
        for col in ['open_interest', 'close_price']:
            if col in contracts_df.columns:
                contracts_df[col] = pd.to_numeric(contracts_df[col], errors='coerce')
        # Prefer active, tradable, with open interest and near the start date
        if 'status' in contracts_df.columns:
            contracts_df = contracts_df[contracts_df['status'].str.lower() == 'active']
        if 'tradable' in contracts_df.columns:
            contracts_df = contracts_df[contracts_df['tradable'] == True]
        if 'open_interest' in contracts_df.columns:
            contracts_df = contracts_df[(contracts_df['open_interest'].fillna(0) > 0)]
        # If no expiration filters provided, focus on expirations within +/- 120 days of the start
        if not exp_gte and not exp_lte and 'expiration_date' in contracts_df.columns:
            start_dt = pd.to_datetime(start_iso, errors='coerce')
            if pd.notna(start_dt):
                lo = start_dt - pd.Timedelta(days=30)
                hi = start_dt + pd.Timedelta(days=180)
                contracts_df = contracts_df[(contracts_df['expiration_date'] >= lo) & (contracts_df['expiration_date'] <= hi)]
        # Prefer higher OI first
        if 'open_interest' in contracts_df.columns:
            contracts_df = contracts_df.sort_values(['open_interest'], ascending=[False])
        # Cap total contracts
        if max_contracts:
            contracts_df = contracts_df.head(max_contracts)
        if contracts_df.empty:
            storage.store_job_status(job_id, "alpaca_options", "completed", results={"records": 0})
            print("ℹ️ No option contracts after filtering.")
            return 0
        # Store contracts
        storage.store_options_contracts(contracts_df)
        symbols = contracts_df['symbol'].tolist()
        # Fetch bars in chunks and store
        total_inserted = 0
        batch_size = 200
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            bars_df = client.get_option_bars(batch, timeframe, start_iso, end_iso)
            if bars_df is None or bars_df.empty:
                # Fallback: try Daily bars to capture EOD activity
                if timeframe.lower() != 'day':
                    bars_df = client.get_option_bars(batch, 'Day', start_iso, end_iso)
            if bars_df is not None and not bars_df.empty:
                inserted = storage.store_options_bars(bars_df, timeframe=(timeframe if not bars_df.empty else 'Day'), source="alpaca")
                total_inserted += inserted
                print(f"✅ Options bars inserted: +{inserted} (total {total_inserted})")
        storage.store_job_status(job_id, "alpaca_options", "completed", results={"records": total_inserted})
        return total_inserted
    except Exception as e:
        storage.store_job_status(job_id, "alpaca_options", "failed", error_message=str(e))
        raise


def ingest_news(symbols: List[str], start_iso: str, end_iso: str, use_finbert: bool = False, max_articles: int = 5000) -> int:
    job_id = _now_id("news")
    storage = DataStorage()
    storage.store_job_status(job_id, "news_alpaca", "pending", parameters={
        "symbols": symbols, "start": start_iso, "end": end_iso, "use_finbert": use_finbert, "max_articles": max_articles
    })
    storage.store_job_status(job_id, "news_alpaca", "running")
    try:
        client = AlpacaNewsClient()
        articles = client.get_news(symbols, start_iso, end_iso, page_limit=max_articles)
        if not articles:
            storage.store_job_status(job_id, "news_alpaca", "completed", results={"records": 0})
            print("ℹ️ No news articles returned.")
            return 0
        if use_finbert:
            try:
                from transformers import pipeline
                nlp = pipeline("sentiment-analysis", model="ProsusAI/finbert")
                for a in articles:
                    text = f"{a.get('headline','')}. {a.get('summary','')}".strip()
                    if not text:
                        continue
                    res = nlp(text)[0]
                    label = res.get('label','neutral').lower()
                    score = float(res.get('score',0))
                    if label == 'positive':
                        a['sentiment_score'] = score
                        a['sentiment_label'] = 'positive'
                    elif label == 'negative':
                        a['sentiment_score'] = -score
                        a['sentiment_label'] = 'negative'
                    else:
                        a['sentiment_score'] = 0.0
                        a['sentiment_label'] = 'neutral'
            except Exception as e:
                print(f"⚠️ FinBERT unavailable or failed: {e}")
        inserted = storage.store_news_articles(articles)
        storage.store_job_status(job_id, "news_alpaca", "completed", results={"records": inserted})
        print(f"✅ Ingested {inserted} news articles.")
        return inserted
    except Exception as e:
        storage.store_job_status(job_id, "news_alpaca", "failed", error_message=str(e))
        raise


def _embed_texts_384(texts: List[str]):
    """Embed texts to 384-dim using modal if USE_MODAL_EMBEDDING=1, else local transformers."""
    if os.getenv("USE_MODAL_EMBEDDING", "0") == "1":
        try:
            import modal
            # Use from_name for deployed function
            f = modal.Function.from_name("gigadataset-embed", "embed_texts_384")
            out = []
            batch_size = int(os.getenv("EMBED_BATCH", "256"))
            for i in range(0, len(texts), batch_size):
                sub = texts[i:i+batch_size]
                vecs = f.remote(sub)
                out.extend(vecs)
            return out
        except Exception as e:
            print(f"⚠️ Modal embedding unavailable, falling back to local: {e}")
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
        model_name = os.getenv("EMBED_MODEL_384", "sentence-transformers/all-MiniLM-L6-v2")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()
        with torch.no_grad():
            inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
            outputs = model(**inputs)
            # Mean pooling
            last_hidden = outputs.last_hidden_state
            attention_mask = inputs['attention_mask'].unsqueeze(-1)
            masked = last_hidden * attention_mask
            sum_embeddings = masked.sum(dim=1)
            sum_mask = attention_mask.sum(dim=1)
            embeddings = (sum_embeddings / sum_mask).cpu().numpy()
        return embeddings
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")


def chunk_and_embed_news(window_start_iso: str, window_end_iso: str, symbols: List[str] = None, batch_size: int = 200):
    """Chunk news summaries/headlines and store embeddings into text_chunks (384-d)."""
    storage = DataStorage()
    s = storage.get_session()
    try:
        from sqlalchemy import and_
        from database.schema import NewsArticle
        with s as db:
            q = db.query(NewsArticle).filter(
                and_(NewsArticle.published_at >= window_start_iso, NewsArticle.published_at <= window_end_iso)
            )
            if symbols:
                q = q.filter(NewsArticle.symbol.in_(symbols))
            total = q.count()
            print(f"Chunking news rows: {total}")
            offset = 0
            inserted = 0
            while offset < total:
                batch = q.order_by(NewsArticle.published_at).offset(offset).limit(batch_size).all()
                if not batch:
                    break
                texts = []
                meta_list = []
                for i, art in enumerate(batch):
                    text = (art.headline or "") + "\n" + (art.summary or "")
                    if not text.strip():
                        continue
                    texts.append(text[:5000])  # safety cap
                    # Build stable doc_id within length constraints
                    base_id = art.url or f"news:{art.id}"
                    if base_id and len(base_id) > 180:
                        doc_id = f"news:{hashlib.sha1(base_id.encode('utf-8')).hexdigest()}"
                    else:
                        doc_id = base_id
                    meta_list.append({
                        'source': art.source,
                        'symbol': art.symbol,
                        'document_id': doc_id,
                        'original_url': art.url
                    })
                if texts:
                    vecs = _embed_texts_384(texts)
                    rows = []
                    for (meta, vec, content) in zip(meta_list, vecs, texts):
                        # vec may be a Python list (from Modal) or a numpy array (local); normalize to list
                        vec_list = vec.tolist() if hasattr(vec, 'tolist') else list(vec)
                        rows.append(TextChunks(
                            source='news',
                            document_id=meta['document_id'][:200] if meta['document_id'] else None,
                            symbol=meta['symbol'],
                            chunk_index=0,
                            content=content,
                            embedding=vec_list,
                            meta_data=meta,
                            created_at=datetime.now(dt_timezone.utc)
                        ))
                    db.add_all(rows)
                    db.commit()
                    inserted += len(rows)
                offset += batch_size
            print(f"✅ Inserted {inserted} news chunks")
            return inserted
    except Exception as e:
        raise


def _html_to_paragraphs(html: str) -> List[str]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        # Remove scripts/styles
        for tag in soup(['script','style']):
            tag.extract()
        text = soup.get_text('\n')
        # Normalize and split to paragraphs
        parts = [p.strip() for p in text.split('\n')]
        # Merge consecutive non-empty lines into paragraphs
        paras = []
        buf = []
        for line in parts:
            if line:
                buf.append(line)
            else:
                if buf:
                    paras.append(' '.join(buf))
                    buf = []
        if buf:
            paras.append(' '.join(buf))
        # Filter very short paragraphs
        paras = [p for p in paras if len(p) >= 200]
        return paras
    except Exception as e:
        return []


def chunk_and_embed_sec(limit: int = 1000, batch_size: int = 50, before: Optional[str] = None, forms: Optional[List[str]] = None):
    """Fetch SEC filing HTML content, chunk to paragraphs, embed (384-d), and store in text_chunks."""
    storage = DataStorage()
    s = storage.get_session()
    client = SECEdgarClient()
    try:
        from database.schema import SECFilings
        with s as db:
            q = db.query(SECFilings)
            if forms:
                q = q.filter(SECFilings.form_type.in_(forms))
            if before:
                try:
                    dtb = pd.to_datetime(before)
                    q = q.filter(SECFilings.filing_date < dtb)
                except Exception:
                    pass
            filings = q.order_by(SECFilings.filing_date.desc()).limit(limit).all()
            total_inserted = 0
            for f in filings:
                doc_id = f"sec:{f.accession_number}"
                # Skip if already chunked
                existing = db.query(TextChunks).filter(TextChunks.document_id == doc_id).first()
                if existing:
                    continue
                if not f.primary_document or not f.accession_number or not f.cik:
                    continue
                try:
                    import time, re
                    import requests
                    base_url = "https://data.sec.gov"
                    accession_clean = f.accession_number.replace('-', '')
                    # Some SEC folders are keyed by the accession-number CIK prefix, not the registrant CIK
                    acc_cik_prefix = f.accession_number.split('-')[0]
                    try:
                        dir_cik = int(acc_cik_prefix)
                    except Exception:
                        dir_cik = int(f.cik)
                    # Be nice to the SEC servers
                    time.sleep(0.5)
                    idx_url = f"{base_url}/Archives/edgar/data/{dir_cik}/{accession_clean}/index.json"
                    r = requests.get(idx_url, headers=client.headers, timeout=10)
                    target = None
                    if r.status_code == 200:
                        data = r.json()
                        items = data.get('directory', {}).get('item', [])
                        # Prefer primary_document if present
                        if f.primary_document:
                            for it in items:
                                if it.get('name','') == f.primary_document:
                                    target = it['name']
                                    break
                        # Otherwise first html file
                        if not target:
                            for it in items:
                                name = it.get('name', '')
                                if name.lower().endswith(('.htm', '.html')):
                                    target = name
                                    break
                    else:
                        # Fallback A: try directory listing page and scrape links
                        dir_url = f"{base_url}/Archives/edgar/data/{dir_cik}/{accession_clean}/"
                        dr = requests.get(dir_url, headers=client.headers, timeout=10)
                        if dr.status_code == 200:
                            links = re.findall(r'href=["\']([^"\']+\.(?:htm|html))', dr.text, flags=re.IGNORECASE)
                            if links:
                                if f.primary_document and f.primary_document in links:
                                    target = f.primary_document
                                else:
                                    target = links[0]
                    # Fallback 1: try direct primary_document via helper
                    html = None
                    if target:
                        file_url = f"{base_url}/Archives/edgar/data/{dir_cik}/{accession_clean}/{target}"
                        hr = requests.get(file_url, headers=client.headers, timeout=15)
                        if hr.status_code == 200:
                            html = hr.text
                    if html is None:
                        try:
                            html = client.get_filing_content(f.cik, f.accession_number, f.primary_document)
                        except Exception:
                            pass
                    # Fallback 2: try full-submission.txt
                    if html is None:
                        alt_url = f"{base_url}/Archives/edgar/data/{dir_cik}/{accession_clean}/full-submission.txt"
                        har = requests.get(alt_url, headers=client.headers, timeout=15)
                        if har.status_code == 200:
                            html = har.text
                            target = 'full-submission.txt'
                    if html is None:
                        print(f"Skip filing (unreachable) {f.cik} {f.accession_number}")
                        continue
                except Exception as e:
                    print(f"SEC chunking error {f.cik} {f.accession_number}: {e}")
                    continue
                paras = _html_to_paragraphs(html)
                if not paras:
                    continue
                # Embed in batches
                inserted_doc = 0
                for i in range(0, len(paras), batch_size):
                    batch = paras[i:i+batch_size]
                    vecs = _embed_texts_384(batch)
                    rows = []
                    for idx, (vec, content) in enumerate(zip(vecs, batch)):
                        vec_list = vec.tolist() if hasattr(vec, 'tolist') else list(vec)
                        rows.append(TextChunks(
                            source='sec',
                            document_id=doc_id,
                            symbol=f.ticker,
                            chunk_index=i+idx,
                            content=content[:8000],
                            embedding=vec_list,
                            meta_data={
                                'cik': f.cik,
                                'ticker': f.ticker,
                                'form_type': f.form_type,
                                'filing_date': f.filing_date.isoformat() if f.filing_date else None,
                                'accession_number': f.accession_number,
                                'primary_document': f.primary_document,
                                'doc_name': target
                            },
                            created_at=datetime.now(dt_timezone.utc)
                        ))
                    db.add_all(rows)
                    db.commit()
                    inserted_doc += len(rows)
                total_inserted += inserted_doc
                print(f"✅ Chunked {inserted_doc} chunks for {doc_id}")
            print(f"✅ Total SEC chunks inserted: {total_inserted}")
            return total_inserted
    except Exception as e:
        raise


def main():
    parser = argparse.ArgumentParser(description="Database setup and ingestion CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("setup-db", help="Create database tables")

    p_alpaca = sub.add_parser("ingest-alpaca", help="Ingest Alpaca OHLCV bars")
    p_alpaca.add_argument("--symbols", nargs="+", required=True)
    p_alpaca.add_argument("--start", required=True, help="YYYY-MM-DD")
    p_alpaca.add_argument("--end", required=True, help="YYYY-MM-DD")
    p_alpaca.add_argument("--timeframe", default="1Day", choices=["1Min", "5Min", "15Min", "1Hour", "1Day"])

    p_sec = sub.add_parser("ingest-sec", help="Ingest SEC filings")
    p_sec.add_argument("--forms", nargs="+", default=["10-K", "10-Q"])
    p_sec.add_argument("--limit", type=int, default=50)
    p_sec.add_argument("--cik", nargs="*", default=None, help="Optional CIK list")

    p_sec_all = sub.add_parser("ingest-sec-all", help="Ingest SEC filings across many companies")
    p_sec_all.add_argument("--forms", nargs="+", default=["10-K", "10-Q"])
    p_sec_all.add_argument("--per-company-limit", type=int, default=5)
    p_sec_all.add_argument("--max-companies", type=int, default=None)

    p_fred = sub.add_parser("ingest-fred", help="Ingest FRED series")
    p_fred.add_argument("--series", nargs="+", required=True)
    p_fred.add_argument("--start", default=None)
    p_fred.add_argument("--end", default=None)

    p_crypto = sub.add_parser("ingest-crypto", help="Ingest Binance klines")
    p_crypto.add_argument("--symbols", nargs="+", required=True)
    p_crypto.add_argument("--interval", default="1d")
    p_crypto.add_argument("--limit", type=int, default=1000)

    p_finn = sub.add_parser("ingest-finnhub", help="Ingest Finnhub candles for many symbols into MarketData")
    p_finn.add_argument("--resolution", default="D", help="1,5,15,30,60,D,W,M")
    p_finn.add_argument("--start", required=True, help="YYYY-MM-DD")
    p_finn.add_argument("--end", required=True, help="YYYY-MM-DD")
    p_finn.add_argument("--max-symbols", type=int, default=500)
    p_finn.add_argument("--exchange", default="US")

    p_opt = sub.add_parser("ingest-alpaca-options", help="Ingest Alpaca options contracts and bars")
    p_opt.add_argument("--underlyings", nargs="+", required=True)
    p_opt.add_argument("--timeframe", default="15Min")
    p_opt.add_argument("--start", required=True, help="RFC3339/ISO timestamp, e.g. 2025-06-01T00:00:00Z")
    p_opt.add_argument("--end", required=True, help="RFC3339/ISO timestamp")
    p_opt.add_argument("--expiration-gte", default=None)
    p_opt.add_argument("--expiration-lte", default=None)
    p_opt.add_argument("--max-contracts", type=int, default=None)

    p_news = sub.add_parser("ingest-news", help="Ingest historical news via Alpaca with optional FinBERT sentiment")
    p_news.add_argument("--symbols", nargs="+", required=True)
    p_news.add_argument("--start", required=True, help="ISO 8601: 2025-01-01T00:00:00Z")
    p_news.add_argument("--end", required=True, help="ISO 8601")
    p_news.add_argument("--use-finbert", action="store_true")
    p_news.add_argument("--max-articles", type=int, default=5000)

    p_chunk_news = sub.add_parser("chunk-news", help="Chunk and embed news into text_chunks")
    p_chunk_news.add_argument("--start", required=True, help="ISO 8601 start")
    p_chunk_news.add_argument("--end", required=True, help="ISO 8601 end")
    p_chunk_news.add_argument("--symbols", nargs="*", default=None)
    p_chunk_news.add_argument("--batch-size", type=int, default=200)

    p_chunk_sec = sub.add_parser("chunk-sec", help="Chunk and embed SEC filings into text_chunks")
    p_chunk_sec.add_argument("--limit", type=int, default=200, help="Max filings to process")
    p_chunk_sec.add_argument("--batch-size", type=int, default=50)
    p_chunk_sec.add_argument("--before", default=None, help="Only process filings before this date (YYYY-MM-DD)")
    p_chunk_sec.add_argument("--forms", nargs="*", default=None, help="Filter forms to process (e.g., 10-K 10-Q)")

    args = parser.parse_args()

    if args.command == "setup-db":
        setup_db()
    elif args.command == "ingest-alpaca":
        ingest_alpaca(args.symbols, args.start, args.end, args.timeframe)
    elif args.command == "ingest-sec":
        ingest_sec(args.forms, args.limit, args.cik)
    elif args.command == "ingest-sec-all":
        ingest_sec_all(args.forms, args.per_company_limit, args.max_companies)
    elif args.command == "ingest-fred":
        ingest_fred(args.series, args.start, args.end)
    elif args.command == "ingest-crypto":
        ingest_crypto(args.symbols, args.interval, args.limit)
    elif args.command == "ingest-finnhub":
        ingest_finnhub(args.resolution, args.start, args.end, args.max_symbols, args.exchange)
    elif args.command == "ingest-alpaca-options":
        ingest_alpaca_options(args.underlyings, args.timeframe, args.start, args.end, args.expiration_gte, args.expiration_lte, args.max_contracts)
    elif args.command == "ingest-news":
        ingest_news(args.symbols, args.start, args.end, args.use_finbert, args.max_articles)
    elif args.command == "chunk-news":
        chunk_and_embed_news(args.start, args.end, args.symbols, args.batch_size)
    elif args.command == "chunk-sec":
        chunk_and_embed_sec(args.limit, args.batch_size, args.before, args.forms)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    sys.exit(main()) 