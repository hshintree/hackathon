from typing import Dict, Any, List


def compute_var(method: str, horizon_days: int, paths: int = 1000, assets: List[str] = None) -> Dict[str, Any]:
	"""Compute VaR/ES. Implement MC/HS later; this returns a stub."""
	return {"status": "queued", "method": method, "horizon_days": horizon_days, "paths": paths, "assets": assets or []}


def stress_test(scenarios: List[Dict[str, Any]], assets: List[str]) -> Dict[str, Any]:
	"""Apply scenario shocks; stub for now."""
	return {"status": "queued", "scenarios": scenarios, "assets": assets} 