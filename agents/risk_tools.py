from typing import Dict, Any, List
import numpy as np
import pandas as pd
from .retrieval_tools import get_prices


def compute_var(method: str, horizon_days: int, paths: int = 1000, assets: List[str] = None) -> Dict[str, Any]:
	assets = assets or []
	if not assets:
		return {"metrics": {}, "note": "no assets provided"}
	# Pull last ~2 years of daily prices
	df = pd.DataFrame(get_prices(assets, start=None, end=None, source=None, limit=None))
	if df.empty:
		return {"metrics": {}, "note": "no data"}
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
	rets = wide.pct_change().dropna()
	if rets.empty:
		return {"metrics": {}}
	w = np.ones(len(rets.columns)) / len(rets.columns)
	port = (rets.fillna(0) @ w)
	# Scale to horizon using sqrt(T)
	scale = np.sqrt(max(horizon_days, 1))
	port_h = port * scale
	if method.lower() in {"hs", "historical"}:
		losses = -port_h.values
	elif method.lower() in {"mc", "normal"}:
		mu, sigma = float(port.mean()), float(port.std() + 1e-12)
		sim = np.random.normal(mu, sigma, size=paths)
		losses = -sim * scale
	else:
		losses = -port_h.values
	var_95 = float(np.quantile(losses, 0.95))
	var_99 = float(np.quantile(losses, 0.99))
	es_95 = float(losses[losses >= var_95].mean()) if np.any(losses >= var_95) else float(var_95)
	return {"metrics": {"var_95": var_95, "var_99": var_99, "expected_shortfall_95": es_95, "horizon_days": horizon_days, "method": method}}


def stress_test(scenarios: List[Dict[str, Any]], assets: List[str]) -> Dict[str, Any]:
	if not assets:
		return {"scenarios": [], "note": "no assets provided"}
	df = pd.DataFrame(get_prices(assets, start=None, end=None, source=None, limit=1))
	if df.empty:
		return {"scenarios": [], "note": "no data"}
	latest = df.groupby('symbol')['close'].last()
	results = []
	for sc in scenarios:
		pct = float(sc.get('pct', 0.0))
		shocked = (1.0 + pct) * latest
		results.append({"scenario": sc, "prices": shocked.to_dict()})
	return {"scenarios": results} 