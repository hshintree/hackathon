from typing import Dict, Any, List

# Stubs: wire to Modal endpoints (/jobs/backtest) later

def run_backtest(params: Dict[str, Any], universe: List[str], start: str, end: str) -> Dict[str, Any]:
	"""Run a single backtest; return summary metrics. To be implemented via Modal endpoint."""
	return {"status": "queued", "params": params, "universe": universe, "start": start, "end": end}


def grid_scan(param_grid: Dict[str, List[Any]], universe: List[str], start: str, end: str) -> Dict[str, Any]:
	"""Submit a grid of params to Modal for parallel backtests; returns job handle."""
	return {"status": "queued", "grid": param_grid, "universe": universe, "start": start, "end": end} 