import modal, os

app = modal.App("vllm-openai")
secrets = modal.Secret.from_name("trading-secrets")

# Choose a model that fits GPU. Good OSS choices:
# - "Qwen/Qwen2.5-7B-Instruct"
# - "meta-llama/Llama-3.1-8B-Instruct"
# - "mistralai/Mistral-7B-Instruct-v0.2"
MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
MAX_TOKENS = int(os.environ.get("VLLM_MAX_MODEL_LEN", "32768"))

image = (
	modal.Image.debian_slim()
	.run_commands("python -m pip install --upgrade pip setuptools wheel")
	.run_commands(
		"python -c \"import os, pathlib; "
		"pathlib.Path('/tmp/pyairports/pyairports').mkdir(parents=True, exist_ok=True); "
		"open('/tmp/pyairports/pyproject.toml','w').write('[project]\\nname = \\\"pyairports\\\"\\nversion = \\\"0.0.0\\\"\\n'); "
		"open('/tmp/pyairports/pyairports/__init__.py','w').write('')\""
	)
	.run_commands("python -m pip install /tmp/pyairports")
	.pip_install([
		"numpy<2.0.0",
		"transformers",
		"torch",
		"accelerate",
		"uvicorn",
		"httpx",
		"fastapi",
		"vllm==0.5.4",
	])
)

@app.function(
	image=image,
	secrets=[secrets],
	gpu="A10G",
	keep_warm=1,
	container_idle_timeout=300,
	timeout=0,
	allow_concurrent_inputs=100,
)
@modal.asgi_app()
def serve():
	from fastapi import FastAPI, Request, Response
	import asyncio, subprocess, httpx

	fa = FastAPI(title="vllm-openai-proxy")

	proc = None
	client = None

	@fa.on_event("startup")
	async def startup():
		nonlocal proc, client
		args = [
			"python", "-m", "vllm.entrypoints.openai.api_server",
			"--model", MODEL,
			"--host", "0.0.0.0",
			"--port", "8000",
			"--max-model-len", str(MAX_TOKENS),
			"--trust-remote-code",
		]
		proc = subprocess.Popen(args)
		client = httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=180.0)
		# wait for server
		for _ in range(60):
			try:
				r = await client.get("/health")
				if r.status_code == 200:
					break
			except Exception:
				pass
			await asyncio.sleep(2)

	@fa.on_event("shutdown")
	async def shutdown():
		nonlocal proc, client
		if client:
			await client.aclose()
		if proc and proc.poll() is None:
			proc.terminate()
			try:
				proc.wait(timeout=10)
			except Exception:
				proc.kill()

	@fa.get("/healthz")
	async def healthz():
		return {"ok": True, "model": MODEL}

	@fa.api_route("/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS","HEAD"])
	async def proxy(request: Request, path: str):
		nonlocal client
		body = await request.body()
		headers = dict(request.headers)
		r = await client.request(
			request.method,
			f"/{path}",
			content=body,
			headers=headers,
		)
		return Response(content=r.content, status_code=r.status_code, headers=dict(r.headers))

	return fa 