from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agents.retrieval_tools import get_prices, get_option_bars, get_option_contracts, get_fred

app = FastAPI(title="data-mcp")

class PricesReq(BaseModel):
	assets: List[str]
	start: str
	end: str
	source: Optional[str] = None
	limit: Optional[int] = None

@app.post("/tools/get_prices")
async def api_get_prices(req: PricesReq):
	return get_prices(req.assets, req.start, req.end, req.source, req.limit)

class OptBarsReq(BaseModel):
	symbols: List[str]
	start: str
	end: str
	timeframe: Optional[str] = None
	limit: Optional[int] = None

@app.post("/tools/get_option_bars")
async def api_get_option_bars(req: OptBarsReq):
	return get_option_bars(req.symbols, req.start, req.end, req.timeframe, req.limit)

class OptContractsReq(BaseModel):
	underlyings: Optional[List[str]] = None
	status: Optional[str] = "active"
	tradable: Optional[bool] = None
	min_open_interest: Optional[float] = None
	exp_gte: Optional[str] = None
	exp_lte: Optional[str] = None
	limit: Optional[int] = 1000

@app.post("/tools/get_option_contracts")
async def api_get_option_contracts(req: OptContractsReq):
	return get_option_contracts(req.underlyings, req.status, req.tradable, req.min_open_interest, req.exp_gte, req.exp_lte, req.limit)

class FredReq(BaseModel):
	series_ids: List[str]
	start: Optional[str] = None
	end: Optional[str] = None
	limit: Optional[int] = None

@app.post("/tools/get_fred")
async def api_get_fred(req: FredReq):
	return get_fred(req.series_ids, req.start, req.end, req.limit) 