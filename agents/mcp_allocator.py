from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(title="allocator-mcp")

class OptReq(BaseModel):
	method: str = "HRP"
	assets: List[str]
	constraints: Dict[str, Any] = {}

@app.post("/tools/optimize_portfolio")
async def optimize_portfolio(req: OptReq):
	# Stub: equal weights; wire to PyPortfolioOpt later
	n = len(req.assets) or 1
	w = 1.0 / n
	weights = {a: w for a in req.assets}
	return {"weights": weights, "method": req.method} 