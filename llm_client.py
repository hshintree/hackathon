import os
from typing import Optional, List, Dict, Any
from openai import OpenAI


def get_openai() -> OpenAI:
	base_url = os.getenv("OPENAI_BASE_URL")
	api_key = os.getenv("OPENAI_API_KEY")
	if base_url and api_key:
		return OpenAI(base_url=base_url, api_key=api_key)
	return OpenAI()


def chat(messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
	# If no credentials configured, return empty to trigger rule-based planning
	if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL")):
		return ""
	try:
		client = get_openai()
		m = model or os.getenv("OPENAI_PLANNER_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
		resp = client.chat.completions.create(model=m, messages=messages, **kwargs)
		return resp.choices[0].message.content or ""
	except Exception:
		# Swallow errors and let callers use rule-based fallback
		return "" 