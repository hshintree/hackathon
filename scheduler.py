#!/usr/bin/env python3
"""
Long-running scheduler to build the database over time with rate limiting.

Usage:
  DB_HOST=... DB_PORT=... DB_NAME=... DB_USER=... DB_PASSWORD=... \
  FINNHUB_API_KEY=... APCA_API_KEY_ID=... APCA_API_SECRET_KEY=... \
  conda run -n hack python scheduler.py --mode equities-macro --hours 6

Modes:
  - sec-wide: Iterate SEC across many companies (forms 10-K/10-Q/8-K)
  - equities-macro: Mix Finnhub candles and FRED series
  - options: Crawl Alpaca options contracts and bars for selected underlyings
  - news: Pull Alpaca historical news incrementally for symbols
  - equities: Pull Alpaca OHLCV bars incrementally for symbols
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Ensure .env is loaded for API keys and DB settings
load_dotenv()

# Optional progress bar
try:
	from tqdm.auto import tqdm
except Exception:
	class _DummyTqdm:
		def __init__(self, *args, **kwargs):
			pass
		def update(self, *args, **kwargs):
			pass
		def close(self):
			pass
	def tqdm(*args, **kwargs):
		return _DummyTqdm()

from ingest import (
    ingest_sec_all,
    ingest_fred,
    ingest_finnhub,
    ingest_alpaca_options,
    ingest_alpaca,
    ingest_news,
)


def sleep_with_log(seconds: float):
    print(f"⏳ Sleeping {seconds:.1f}s to respect rate limits...")
    time.sleep(seconds)


def run_sec_wide(hours: int):
    end_time = time.time() + hours * 3600 if hours else None
    est_cycle_s = 60.0
    total_iters = int((hours * 3600) / est_cycle_s) if hours else None
    pbar = tqdm(total=total_iters, desc="SEC Filings", unit="batch")
    total_inserted = 0
    while True:
        print("🔁 SEC wide sweep batch...")
        try:
            inserted = ingest_sec_all(forms=["10-K", "10-Q", "8-K"], per_company_limit=5, max_companies=200)
            total_inserted += (inserted or 0)
            print(f"📈 Cumulative SEC records: {total_inserted}")
        except Exception as e:
            print(f"SEC batch error: {e}")
        pbar.update(1)
        sleep_with_log(60)
        if end_time and time.time() > end_time:
            break
    pbar.close()


def run_equities_macro(hours: int):
    end_time = time.time() + hours * 3600 if hours else None
    fred_series = [
        "GDP", "GDPC1", "UNRATE", "CPIAUCSL", "CPILFESL", "FEDFUNDS", "DGS10", "DGS2",
        "DGS3MO", "PAYEMS", "HOUST", "INDPRO", "UMCSENT", "PCE", "PCEPI", "M2SL"
    ]
    est_cycle_s = 60.0
    total_iters = int((hours * 3600) / est_cycle_s) if hours else None
    pbar = tqdm(total=total_iters, desc="Equities/Macro", unit="cycle")
    while True:
        print("📈 Finnhub daily candles batch...")
        try:
            ingest_finnhub(resolution="D", start="2005-01-01", end=datetime.now().strftime("%Y-%m-%d"), max_symbols=1000, exchange="US")
        except Exception as e:
            print(f"Finnhub batch error: {e}")
        sleep_with_log(30)
        print("🏛️ FRED series batch...")
        try:
            ingest_fred(fred_series, start="1990-01-01", end=datetime.now().strftime("%Y-%m-%d"))
        except Exception as e:
            print(f"FRED batch error: {e}")
        pbar.update(1)
        sleep_with_log(30)
        if end_time and time.time() > end_time:
            break
    pbar.close()


def run_options(hours: int):
    end_time = time.time() + hours * 3600 if hours else None
    underlyings = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
    est_cycle_s = 60.0
    total_iters = int((hours * 3600) / est_cycle_s) if hours else None
    pbar = tqdm(total=total_iters, desc="Options", unit="batch")
    total_inserted = 0
    while True:
        print("🧾 Alpaca options batch...")
        start_iso = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        end_iso = datetime.now(timezone.utc).isoformat()
        try:
            inserted = ingest_alpaca_options(underlyings=underlyings, timeframe="15Min", start_iso=start_iso, end_iso=end_iso, exp_gte=None, exp_lte=None, max_contracts=1000)
            total_inserted += (inserted or 0)
            print(f"📈 Cumulative options bars: {total_inserted}")
        except Exception as e:
            print(f"Options batch error: {e}")
        pbar.update(1)
        sleep_with_log(60)
        if end_time and time.time() > end_time:
            break
    pbar.close()


def run_news(hours: int, symbols: list, window_days: int):
    end_time = time.time() + hours * 3600 if hours else None
    total_iters = hours if hours else None
    pbar = tqdm(total=total_iters, desc="News", unit="hour")
    while True:
        end_iso = datetime.now(timezone.utc).isoformat()
        start_iso = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
        print(f"📰 News batch {start_iso} → {end_iso} for {len(symbols)} symbols")
        try:
            ingest_news(symbols, start_iso, end_iso, use_finbert=False, max_articles=10000)
        except Exception as e:
            print(f"News batch error: {e}")
        pbar.update(1)
        sleep_with_log(3600)
        if end_time and time.time() > end_time:
            break
    pbar.close()


def run_equities(hours: int, symbols: list, timeframe: str, window_days: int):
    end_time = time.time() + hours * 3600 if hours else None
    total_iters = hours if hours else None
    pbar = tqdm(total=total_iters, desc="Equities", unit="hour")
    while True:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=window_days)
        print(f"📊 Equities batch {start_dt.date()} → {end_dt.date()} timeframe {timeframe} for {len(symbols)} symbols")
        try:
            ingest_alpaca(symbols, start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'), timeframe)
        except Exception as e:
            print(f"Equities batch error: {e}")
        pbar.update(1)
        sleep_with_log(3600)
        if end_time and time.time() > end_time:
            break
    pbar.close()


def main():
    parser = argparse.ArgumentParser(description="Long-running ingestion scheduler")
    parser.add_argument("--mode", choices=["sec-wide", "equities-macro", "options", "news", "equities"], required=True)
    parser.add_argument("--hours", type=int, default=None, help="How long to run; default is indefinitely")
    parser.add_argument("--symbols", nargs="*", default=None, help="Symbols for news/equities modes")
    parser.add_argument("--timeframe", default="1Day", help="Timeframe for equities mode")
    parser.add_argument("--window-days", type=int, default=1, help="Lookback window for incremental pull")
    args = parser.parse_args()

    if args.mode == "sec-wide":
        run_sec_wide(args.hours)
    elif args.mode == "equities-macro":
        run_equities_macro(args.hours)
    elif args.mode == "options":
        run_options(args.hours)
    elif args.mode == "news":
        symbols = args.symbols or ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","SPY","QQQ"]
        run_news(args.hours or 1, symbols, args.window_days)
    elif args.mode == "equities":
        symbols = args.symbols or ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","JPM","JNJ"]
        run_equities(args.hours or 1, symbols, args.timeframe, args.window_days)


if __name__ == "__main__":
    sys.exit(main()) 