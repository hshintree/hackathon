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
            inserted = ingest_sec_all(forms=["10-K", "10-Q", "8-K"], per_company_limit=5, max_companies=500)
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
        "DGS3MO", "PAYEMS", "HOUST", "INDPRO", "RETAILMNSA", "UMCSENT", "PCE", "PCEPI", "M2SL"
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
            inserted = ingest_alpaca_options(underlyings=underlyings, timeframe="15Min", start_iso=start_iso, end_iso=end_iso, exp_gte=None, exp_lte=None, max_contracts=2000)
            total_inserted += (inserted or 0)
            print(f"📈 Cumulative options bars: {total_inserted}")
        except Exception as e:
            print(f"Options batch error: {e}")
        pbar.update(1)
        sleep_with_log(60)
        if end_time and time.time() > end_time:
            break
    pbar.close()


def main():
    parser = argparse.ArgumentParser(description="Long-running ingestion scheduler")
    parser.add_argument("--mode", choices=["sec-wide", "equities-macro", "options"], required=True)
    parser.add_argument("--hours", type=int, default=None, help="How long to run; default is indefinitely")
    args = parser.parse_args()

    if args.mode == "sec-wide":
        run_sec_wide(args.hours)
    elif args.mode == "equities-macro":
        run_equities_macro(args.hours)
    elif args.mode == "options":
        run_options(args.hours)


if __name__ == "__main__":
    sys.exit(main()) 