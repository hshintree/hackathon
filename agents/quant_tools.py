from typing import Dict, Any, List

import pandas as pd
import numpy as np
from .retrieval_tools import get_prices


def run_backtest(params: Dict[str, Any], universe: List[str], start: str, end: str) -> Dict[str, Any]:
	prices = get_prices(universe, start, end, source=None, limit=None)
	df = pd.DataFrame(prices)
	if df.empty:
		return {"metrics": {}, "note": "no data"}
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
	try:
		import vectorbt as vbt
	except Exception:
		vbt = None
	if vbt is not None and params.get('strategy', 'ma_cross') == 'ma_cross':
		short = int(params.get('ma_short', 10))
		long = int(params.get('ma_long', 30))
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
		"sharpe": float(port.mean() / (port.std() + 1e-12) * np.sqrt(252)),
		"max_drawdown": float(((equity / equity.cummax()) - 1.0).min()),
	}
	return {"metrics": metrics}


def grid_scan(param_grid: Dict[str, List[Any]], universe: List[str], start: str, end: str) -> Dict[str, Any]:
	results: List[Dict[str, Any]] = []
	ma_short = param_grid.get('ma_short', [10])
	ma_long = param_grid.get('ma_long', [30])
	for s in ma_short:
		for l in ma_long:
			res = run_backtest({"strategy": "ma_cross", "ma_short": s, "ma_long": l}, universe, start, end)
			results.append({"params": {"ma_short": s, "ma_long": l}, "metrics": res.get("metrics", {})})
	return {"status": "done", "results": results} 