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
from typing import List, Optional
from dotenv import load_dotenv

# Load .env early so API keys/DB vars are available
load_dotenv()

from database.schema import create_database_engine, create_tables
from database.storage import DataStorage

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
        if max_contracts:
            contracts_df = contracts_df.head(max_contracts)
        # Store contracts
        storage.store_options_contracts(contracts_df)
        symbols = contracts_df['symbol'].tolist()
        # Fetch bars in chunks and store
        total_inserted = 0
        batch_size = 200
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            bars_df = client.get_option_bars(batch, timeframe, start_iso, end_iso)
            if bars_df is not None and not bars_df.empty:
                inserted = storage.store_options_bars(bars_df, timeframe=timeframe, source="alpaca")
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
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    sys.exit(main()) 