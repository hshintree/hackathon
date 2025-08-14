"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export default function QueryRunnerPage() {
	const [query, setQuery] = useState("");
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [state, setState] = useState<any | null>(null);

	async function runQuery() {
		setLoading(true);
		setError(null);
		setState(null);
		try {
			const resp = await fetch("http://localhost:8080/agent/chat", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ query }),
			});
			if (!resp.ok) {
				const t = await resp.text();
				throw new Error(t || `HTTP ${resp.status}`);
			}
			const data = await resp.json();
			setState(data.state);
		} catch (e: any) {
			setError(e?.message || "Request failed");
		} finally {
			setLoading(false);
		}
	}

	function Section({ title, children }: { title: string; children: React.ReactNode }) {
		return (
			<div className="space-y-2">
				<div className="text-sm font-semibold opacity-70">{title}</div>
				<Card className="p-4">{children}</Card>
			</div>
		);
	}

	function renderResult() {
		if (!state) return null;
		const intent = state.intent || state.plan;
		const result = state.result || {};
		const context = state.context || [];

		if (intent === "search_corpus" || intent === "get_chunk") {
			const items = (result.results || context || []).slice(0, 20);
			return (
				<div className="space-y-3">
					{items.map((it: any, idx: number) => (
						<Card key={idx} className="p-3">
							<div className="text-xs opacity-60 mb-1">{it.source || it.symbol || it.id}</div>
							<div className="text-sm whitespace-pre-wrap">{(it.content || it.text || "").slice(0, 500)}</div>
						</Card>
					))}
				</div>
			);
		}

		if (intent === "run_backtest") {
			const metrics = result.metrics || {};
			return (
				<div className="grid grid-cols-2 gap-3">
					{Object.keys(metrics).map((k) => (
						<Card key={k} className="p-3"><div className="text-xs opacity-60">{k}</div><div className="text-base font-semibold">{formatNum(metrics[k])}</div></Card>
					))}
				</div>
			);
		}

		if (intent === "grid_scan") {
			const results = result.results || [];
			return (
				<div className="space-y-3">
					{results.slice(0, 50).map((r: any, idx: number) => (
						<Card key={idx} className="p-3">
							<div className="text-xs opacity-60 mb-1">ma_short={r.params?.ma_short} ma_long={r.params?.ma_long}</div>
							<div className="flex gap-3 text-sm">
								<span>cagr: {formatNum(r.metrics?.cagr)}</span>
								<span>sharpe: {formatNum(r.metrics?.sharpe)}</span>
								<span>maxDD: {formatNum(r.metrics?.max_drawdown)}</span>
							</div>
						</Card>
					))}
				</div>
			);
		}

		if (intent === "compute_var") {
			return (
				<div className="grid grid-cols-3 gap-3">
					<Card className="p-3"><div className="text-xs opacity-60">VaR</div><div className="text-base font-semibold">{formatNum(result.var)}</div></Card>
					<Card className="p-3"><div className="text-xs opacity-60">mu</div><div className="text-base font-semibold">{formatNum(result.mu)}</div></Card>
					<Card className="p-3"><div className="text-xs opacity-60">sigma</div><div className="text-base font-semibold">{formatNum(result.sigma)}</div></Card>
				</div>
			);
		}

		if (intent === "stress_test") {
			const scenarios = result.scenarios || [];
			return (
				<div className="space-y-4">
					{scenarios.map((sc: any, idx: number) => (
						<div key={idx}>
							<div className="text-sm font-medium mb-1">{sc.name}</div>
							<div className="space-y-1">
								{Object.entries(sc.result || {}).map(([sym, px]) => (
									<div key={sym} className="flex items-center gap-2">
										<div className="w-20 text-xs opacity-70">{sym}</div>
										<div className="flex-1 bg-muted h-2 rounded">
											<div className="bg-primary h-2 rounded" style={{ width: barWidth(px as number) }} />
										</div>
										<div className="w-24 text-right text-xs">{formatNum(px as number)}</div>
									</div>
								))}
							</div>
						</div>
					))}
				</div>
			);
		}

		if (intent === "optimize_portfolio") {
			const weights = result.weights || {};
			const entries = Object.entries(weights) as [string, number][];
			return (
				<div className="space-y-2">
					{entries.map(([sym, w]) => (
						<div key={sym} className="flex items-center gap-2">
							<div className="w-20 text-xs opacity-70">{sym}</div>
							<div className="flex-1 bg-muted h-2 rounded">
								<div className="bg-primary h-2 rounded" style={{ width: `${Math.min(100, Math.max(0, (w || 0) * 100))}%` }} />
							</div>
							<div className="w-16 text-right text-xs">{formatNum(w)}</div>
						</div>
					))}
				</div>
			);
		}

		return (
			<pre className="text-xs whitespace-pre-wrap">{JSON.stringify({ intent, result, context }, null, 2)}</pre>
		);
	}

	return (
		<div className="mx-auto max-w-4xl p-6 space-y-6">
			<div className="space-y-1">
				<div className="text-2xl font-semibold">Query Runner</div>
				<div className="text-sm opacity-70">Type a natural language task. The agent will plan, call tools, and return structured results.</div>
			</div>
			<div className="flex gap-2">
				<Input
					placeholder="e.g., run a moving average backtest on AAPL and MSFT from 2023-01-01 to 2023-12-31"
					value={query}
					onChange={(e) => setQuery(e.target.value)}
				/>
				<Button onClick={runQuery} disabled={loading || !query.trim()}>
					{loading ? "Running..." : "Run"}
				</Button>
			</div>
			{error && (
				<Card className="p-3 text-sm text-red-600 bg-red-50 border-red-200">{error}</Card>
			)}
			{state && (
				<div className="space-y-4">
					<Section title="Plan / Intent">
						<div className="text-sm">{state.intent || state.plan}</div>
					</Section>
					<Section title="Output">{renderResult()}</Section>
					<Section title="Raw State">
						<pre className="text-xs whitespace-pre-wrap">{JSON.stringify(state, null, 2)}</pre>
					</Section>
				</div>
			)}
		</div>
	);
}

function formatNum(x: any) {
	if (x === null || x === undefined || Number.isNaN(x)) return "-";
	if (typeof x !== "number") return String(x);
	return Math.abs(x) >= 1 ? x.toFixed(4) : x.toExponential(2);
}

function barWidth(x: number) {
	const v = Math.max(0, Math.min(1, x / (Math.abs(x) + 1e-9)));
	return `${Math.round(v * 100)}%`;
} 