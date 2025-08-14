from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from agents.retrieval_tools import get_prices

app = FastAPI(title="quant-mcp")

class BacktestReq(BaseModel):
	params: Dict[str, Any] = {}
	universe: List[str]
	start: str
	end: str

class GridReq(BaseModel):
	param_grid: Dict[str, List[Any]]
	universe: List[str]
	start: str
	end: str

@app.post("/tools/run_backtest")
async def run_backtest(req: BacktestReq):
	prices = get_prices(req.universe, req.start, req.end, source=None, limit=None)
	import pandas as pd
	import numpy as np
	try:
		import vectorbt as vbt
	except Exception:
		vbt = None
	df = pd.DataFrame(prices)
	if df.empty:
		return {"metrics": {}, "note": "no data"}
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
	if vbt is not None and req.params.get('strategy', 'ma_cross') == 'ma_cross':
		short = int(req.params.get('ma_short', 10))
		long = int(req.params.get('ma_long', 30))
		fast = wide.vbt.rolling_mean(window=short)
		slow = wide.vbt.rolling_mean(window=long)
		entries = fast > slow
		exits = fast < slow
		pf = vbt.Portfolio.from_signals(wide, entries, exits, fees=0.0005, slippage=0.0005, freq='D')
		stats = pf.stats()
		metrics = {
			"total_return": float(stats.get('Total Return [%]', np.nan))/100.0 if 'Total Return [%]' in stats else float(pf.total_return()),
			"cagr": float(stats.get('CAGR [%]', np.nan))/100.0 if 'CAGR [%]' in stats else float(pf.annualized_return()),
			"sharpe": float(stats.get('Sharpe Ratio', np.nan)) if 'Sharpe Ratio' in stats else float(pf.sharpe_ratio()),
			"max_drawdown": float(stats.get('Max Drawdown [%]', np.nan))/100.0 if 'Max Drawdown [%]' in stats else float(pf.max_drawdown()),
		}
		return {"metrics": metrics}
	# Fallback: equal-weight daily rebalanced
	rets = wide.pct_change().dropna()
	if rets.empty:
		return {"metrics": {}}
	w = np.ones(len(rets.columns)) / len(rets.columns)
	port = (rets.fillna(0) @ w)
	equity = (1 + port).cumprod()
	n = len(port)
	metrics = {
		"total_return": float(equity.iloc[-1] - 1.0),
		"cagr": float(equity.iloc[-1] ** (252/max(n,1)) - 1.0),
		"sharpe": float(port.mean()/ (port.std() + 1e-12) * np.sqrt(252)),
		"max_drawdown": float(((equity / equity.cummax()) - 1.0).min()),
	}
	return {"metrics": metrics}

@app.post("/tools/grid_scan")
async def grid_scan(req: GridReq):
	use_modal = os.getenv("USE_MODAL", "0") == "1"
	if use_modal:
		try:
			# build compact price payload
			px = get_prices(req.universe, req.start, req.end, source=None, limit=None)
			import pandas as pd
			df = pd.DataFrame(px)
			df['timestamp'] = pd.to_datetime(df['timestamp'])
			wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
			payload = {
				"symbols": list(wide.columns),
				"timestamps": [str(t) for t in wide.index],
				"prices": wide.values.tolist()
			}
			import modal
			f = modal.Function.from_name("trading-agent-data", "grid_scan_parent")
			job = f.remote(req.param_grid, payload)
			return {"status": "submitted", "result": job}
		except Exception as e:
			return {"status": "fallback", "error": str(e)}
	# Local fallback: pairwise scan of MA parameters
	results = []
	ma_short = req.param_grid.get('ma_short', [10])
	ma_long = req.param_grid.get('ma_long', [30])
	for s in ma_short:
		for l in ma_long:
			res = await run_backtest(BacktestReq(params={'strategy':'ma_cross','ma_short':s,'ma_long':l}, universe=req.universe, start=req.start, end=req.end))
			results.append({"params": {"ma_short": s, "ma_long": l}, "metrics": res.get("metrics",{})})
	return {"status": "done", "results": results} 