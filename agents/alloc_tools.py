from typing import Dict, Any, List
import numpy as np
import pandas as pd
from .retrieval_tools import get_prices


def optimize_portfolio(method: str, assets: List[str], constraints: Dict[str, Any] = None) -> Dict[str, Any]:
	constraints = constraints or {}
	assets = assets or []
	if not assets:
		return {"weights": {}, "note": "no assets provided", "method": method}
	df = pd.DataFrame(get_prices(assets, start=None, end=None, source=None, limit=None))
	if df.empty:
		return {"weights": {}, "note": "no data", "method": method}
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
	rets = wide.pct_change().dropna()
	if rets.empty:
		return {"weights": {}, "note": "insufficient returns", "method": method}
	mu = rets.mean() * 252.0
	cov = rets.cov() * 252.0
	if method.upper() in {"MEANVAR", "MV"}:
		# Simple mean-variance with lambda from constraints (risk_aversion)
		lam = float(constraints.get('risk_aversion', 1.0))
		try:
			inv = np.linalg.pinv(cov.values)
			w = inv @ mu.values
			w = w / (np.sum(w) + 1e-12)
			w = (1.0 - lam) * (np.ones_like(w) / len(w)) + lam * w
			w = np.maximum(w, 0.0)
			w = w / (np.sum(w) + 1e-12)
			weights = {sym: float(wi) for sym, wi in zip(rets.columns, w)}
			return {"weights": weights, "method": method}
		except Exception:
			pass
	# Default: equal weight
	w = np.ones(len(rets.columns)) / len(rets.columns)
	weights = {sym: float(wi) for sym, wi in zip(rets.columns, w)}
	return {"weights": weights, "method": method} 