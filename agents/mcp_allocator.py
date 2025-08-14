from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from agents.retrieval_tools import get_prices

app = FastAPI(title="allocator-mcp")

class OptReq(BaseModel):
	method: str = "HRP"  # HRP | MeanVar | BL
	assets: List[str]
	constraints: Dict[str, Any] = {}
	start: Optional[str] = None
	end: Optional[str] = None


@app.post("/tools/optimize_portfolio")
async def optimize_portfolio(req: OptReq):
	# Fetch prices for window
	try:
		px = get_prices(req.assets, req.start or "", req.end or "", source=None, limit=None)
		import pandas as pd
		df = pd.DataFrame(px)
		if df.empty:
			return {"weights": {}, "method": req.method, "note": "no data"}
		df['timestamp'] = pd.to_datetime(df['timestamp'])
		wide = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index().dropna(how='all')
		rets = wide.pct_change().dropna()
	except Exception as e:
		return {"error": f"data error: {e}"}

	# Bounds/targets
	min_w = float(req.constraints.get("min_weight", 0.0))
	max_w = float(req.constraints.get("max_weight", 1.0))
	target_return = req.constraints.get("target_return")
	gamma = float(req.constraints.get("risk_aversion", 1.0))

	# Try PyPortfolioOpt first
	if req.method.upper() in {"MEANVAR", "MEAN_VAR", "MV"}:
		try:
			from pypfopt import EfficientFrontier, risk_models, expected_returns
			mu = expected_returns.mean_historical_return(wide, frequency=252)
			S = risk_models.CovarianceShrinkage(wide).ledoit_wolf()
			ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))
			if target_return is not None:
				w = ef.efficient_return(float(target_return))
			else:
				w = ef.max_sharpe()
			weights = ef.clean_weights()
			perf = ef.portfolio_performance(verbose=False)
			return {"weights": weights, "method": "MeanVar", "metrics": {"ret": float(perf[0]), "vol": float(perf[1]), "sharpe": float(perf[2])}}
		except Exception:
			pass

	if req.method.upper() == "HRP":
		try:
			from pypfopt.hierarchical_portfolio import HRPOpt
			hrp = HRPOpt(returns=rets)
			weights = hrp.optimize()
			return {"weights": {k: float(v) for k, v in weights.items()}, "method": "HRP"}
		except Exception:
			pass

	if req.method.upper() == "BL":
		# Minimal BL: requires prior market caps or views; attempt if provided
		try:
			from pypfopt import black_litterman, risk_models, EfficientFrontier
			mcaps = req.constraints.get("market_caps")  # {symbol: cap}
			views = req.constraints.get("views")        # {symbol: view}
			if not mcaps or not isinstance(mcaps, dict):
				raise ValueError("market_caps required for BL")
			S = risk_models.CovarianceShrinkage(wide).ledoit_wolf()
			delta = black_litterman.market_implied_risk_aversion(wide.pct_change().mean())
			prior = black_litterman.market_implied_prior_returns({k: float(v) for k, v in mcaps.items()}, delta, S)
			if views and isinstance(views, dict):
				Q = {k: float(v) for k, v in views.items()}
				bl = black_litterman.BlackLittermanModel(S, pi=prior, absolute_views=Q)
				mu = bl.bl_returns()
			else:
				mu = prior
			ef = EfficientFrontier(mu, S, weight_bounds=(min_w, max_w))
			w = ef.max_sharpe()
			weights = ef.clean_weights()
			return {"weights": weights, "method": "BL"}
		except Exception:
			pass

	# Fallback: risk parity via riskfolio-lib
	try:
		import riskfolio as rp
		port = rp.Portfolio(returns=rets)
		method_mu = req.constraints.get("method_mu", "hist")
		method_cov = req.constraints.get("method_cov", "shrink")
		port.assets_stats(method_mu=method_mu, method_cov=method_cov, d=0.94)
		# Equal Risk Contribution (ERC)
		w = port.rp_optimization(model="Classic", b=None, rm="MV", rf=0, bnds=(min_w, max_w), hist=True)
		weights = {k: float(v) for k, v in zip(w.index.tolist(), w.values.flatten().tolist())}
		return {"weights": weights, "method": "ERC"}
	except Exception:
		pass

	# Last resort: equal weights
	n = len(req.assets) or 1
	w = 1.0 / n
	weights = {a: w for a in req.assets}
	return {"weights": weights, "method": req.method, "note": "fallback"} 