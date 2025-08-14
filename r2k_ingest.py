#!/usr/bin/env python3
import os
import argparse
from typing import List
from dotenv import load_dotenv
from datetime import datetime

from data_sources.alpaca_client import AlpacaClient
from ingest import ingest_alpaca, ingest_alpaca_options
from database.storage import DataStorage
from database.schema import MarketData, OptionsContract, OptionsBar


def build_r2000_like_universe(max_symbols: int = 2000) -> List[str]:
	assets_df = AlpacaClient().get_assets(asset_class="us_equity", status="active")
	symbols = assets_df['symbol'].dropna().astype(str).str.upper().unique().tolist()
	symbols = [s for s in symbols if s.isalnum() and len(s) <= 5]
	etf_exclude = {"SPY","QQQ","IWM","DIA","VTI","VOO","XLK","XLF","XLE","XLV","XLY","XLP","XLI","XLU","IEMG","TLT","HYG","SCHX"}
	symbols = [s for s in symbols if s not in etf_exclude]
	return symbols[:max_symbols]


def chunk_list(items: List[str], size: int) -> List[List[str]]:
	return [items[i:i+size] for i in range(0, len(items), size)]


def main():
	load_dotenv()
	parser = argparse.ArgumentParser(description="Ingest Russell 2000–like universe for equities and options")
	parser.add_argument("--equities", action="store_true", help="Run equities ingestion")
	parser.add_argument("--options", action="store_true", help="Run options ingestion")
	parser.add_argument("--equity-start", default="2015-01-01")
	parser.add_argument("--equity-end", default="2025-01-01")
	parser.add_argument("--equity-timeframe", default="1Day")
	parser.add_argument("--option-start", default="2025-06-01T00:00:00Z")
	parser.add_argument("--option-end", default="2025-06-10T00:00:00Z")
	parser.add_argument("--option-timeframe", default="15Min")
	parser.add_argument("--max-contracts", type=int, default=500)
	parser.add_argument("--max-symbols", type=int, default=2000)
	args = parser.parse_args()

	universe = build_r2000_like_universe(args.max_symbols)
	print(f"Universe size: {len(universe)}")

	storage = DataStorage()

	if args.equities:
		batches = chunk_list(universe, 100)
		for i, batch in enumerate(batches, 1):
			print(f"[Equities] Batch {i}/{len(batches)} ({len(batch)} symbols) {args.equity_start}→{args.equity_end}")
			try:
				ingest_alpaca(batch, args.equity_start, args.equity_end, timeframe=args.equity_timeframe)
			except Exception as e:
				print("Equities batch error:", e)
				continue
			with storage.get_session() as db:
				print("MarketData:", db.query(MarketData).count())

	if args.options:
		batches = chunk_list(universe, 50)
		for i, under in enumerate(batches, 1):
			print(f"[Options] Batch {i}/{len(batches)} ({len(under)} underlyings) {args.option_start}→{args.option_end}")
			try:
				ingest_alpaca_options(under, timeframe=args.option_timeframe, start_iso=args.option_start, end_iso=args.option_end, exp_gte=None, exp_lte=None, max_contracts=args.max_contracts)
			except Exception as e:
				print("Options batch error:", e)
				continue
			with storage.get_session() as db:
				print("OptionsContracts:", db.query(OptionsContract).count())
				print("OptionsBars:", db.query(OptionsBar).count())

	print("Done.")


if __name__ == "__main__":
	main() 