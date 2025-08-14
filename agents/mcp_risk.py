from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import numpy as np

from agents.retrieval_tools import get_prices

app = FastAPI(title="risk-mcp")

class VarReq(BaseModel):
	method: str = "mc"
	horizon_days: int = 10
	paths: int = 1000
	assets: List[str]
	start: str
	end: str
	alpha: float = 0.95

class StressReq(BaseModel):
	scenarios: List[Dict[str, Any]]
	assets: List[str]
	start: str
	end: str

@app.post("/tools/compute_var")
async def compute_var(req: VarReq):
	# Local MC VaR using simple normal on portfolio returns
	prices = get_prices(req.assets, req.start, req.end, source=None, limit=None)
	import pandas as pd
	df = pd.DataFrame(prices)
	if df.empty:
		return {"var": None, "note": "no data"}
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	pivot = df.pivot_table(index='timestamp', columns='symbol', values='close').sort_index()
	rets = pivot.pct_change().dropna()
	port = rets.mean(axis=1)
	mu, sigma = float(port.mean()), float(port.std())
	sim = np.random.normal(mu, sigma, size=(req.paths, req.horizon_days))
	cum = sim.sum(axis=1)
	var = -np.quantile(cum, 1-req.alpha)
	return {"var": float(var), "mu": mu, "sigma": sigma}

@app.post("/tools/stress_test")
async def stress_test(req: StressReq):
	# Apply pct shocks to last close for each asset
	prices = get_prices(req.assets, req.start, req.end, source=None, limit=None)
	import pandas as pd
	df = pd.DataFrame(prices)
	if df.empty:
		return {"scenarios": []}
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	last = df.sort_values('timestamp').groupby('symbol').tail(1).set_index('symbol')
	out = []
	for sc in req.scenarios:
		shock = sc.get('shock_pct', -0.05)
		res = {sym: float(last.loc[sym]['close'] * (1+shock)) for sym in last.index if sym in req.assets}
		out.append({"name": sc.get('name','shock'), "result": res})
	return {"scenarios": out} 