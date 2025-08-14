from typing import Dict, Any, List


def optimize_portfolio(method: str, assets: List[str], constraints: Dict[str, Any] = None) -> Dict[str, Any]:
	"""Optimize weights (HRP/BL/MeanVar). Stub for now; wire to PyPortfolioOpt later."""
	return {"status": "queued", "method": method, "assets": assets, "constraints": constraints or {}} 