"use client"

import React, { useState } from "react"
import { Send, Bot, TrendingUp, AlertCircle, CheckCircle, Loader2 } from "lucide-react"
import { apiClient, AgentChatResponse } from "@/lib/api"

interface QueryResult {
  intent: string
  result: any
  error?: string
  timestamp: Date
}

export default function QueryInterface() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<QueryResult[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    setLoading(true)
    setError(null)

    try {
      const response: AgentChatResponse = await apiClient.chat({ query })
      
      const result: QueryResult = {
        intent: response.state.intent || "unknown",
        result: response.state.result || {},
        error: response.state.error,
        timestamp: new Date()
      }

      setResults(prev => [result, ...prev])
      setQuery("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  const renderResult = (result: QueryResult) => {
    if (result.error) {
      return (
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-red-400 font-medium">Error</span>
          </div>
          <p className="text-red-300">{result.error}</p>
        </div>
      )
    }

    switch (result.intent) {
      case "search_corpus":
      case "get_chunk":
        return renderSearchResult(result.result)
      case "run_backtest":
      case "grid_scan":
        return renderBacktestResult(result.result)
      case "compute_var":
      case "stress_test":
        return renderRiskResult(result.result)
      case "optimize_portfolio":
        return renderPortfolioResult(result.result)
      default:
        return renderGenericResult(result.result)
    }
  }

  const renderSearchResult = (result: any) => {
    const results = result.results || []
    return (
      <div className="space-y-3">
        <h4 className="text-emerald-400 font-medium">Search Results</h4>
        {results.length > 0 ? (
          results.slice(0, 5).map((item: any, idx: number) => (
            <div key={idx} className="p-3 bg-neutral-800 border border-neutral-700 rounded">
              <div className="text-sm text-neutral-300">
                {item.content || item.text || JSON.stringify(item)}
              </div>
              {item.score && (
                <div className="text-xs text-neutral-500 mt-1">
                  Relevance: {(item.score * 100).toFixed(1)}%
                </div>
              )}
            </div>
          ))
        ) : (
          <p className="text-neutral-500">No results found</p>
        )}
      </div>
    )
  }

  const renderBacktestResult = (result: any) => {
    const metrics = result.metrics || {}
    return (
      <div className="space-y-3">
        <h4 className="text-emerald-400 font-medium">Backtest Results</h4>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(metrics).map(([key, value]) => (
            <div key={key} className="p-3 bg-neutral-800 border border-neutral-700 rounded">
              <div className="text-xs text-neutral-500 uppercase">{key.replace(/_/g, ' ')}</div>
              <div className="text-lg font-bold text-white">
                {typeof value === 'number' ? 
                  (key.includes('return') || key.includes('drawdown') ? 
                    `${(value * 100).toFixed(2)}%` : 
                    value.toFixed(4)
                  ) : 
                  String(value)
                }
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderRiskResult = (result: any) => {
    return (
      <div className="space-y-3">
        <h4 className="text-emerald-400 font-medium">Risk Analysis</h4>
        <div className="p-4 bg-neutral-800 border border-neutral-700 rounded">
          <pre className="text-sm text-neutral-300 whitespace-pre-wrap">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    )
  }

  const renderPortfolioResult = (result: any) => {
    return (
      <div className="space-y-3">
        <h4 className="text-emerald-400 font-medium">Portfolio Optimization</h4>
        <div className="p-4 bg-neutral-800 border border-neutral-700 rounded">
          <pre className="text-sm text-neutral-300 whitespace-pre-wrap">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    )
  }

  const renderGenericResult = (result: any) => {
    return (
      <div className="space-y-3">
        <h4 className="text-emerald-400 font-medium">Result</h4>
        <div className="p-4 bg-neutral-800 border border-neutral-700 rounded">
          <pre className="text-sm text-neutral-300 whitespace-pre-wrap">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-950 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Bot className="w-8 h-8 text-emerald-400" />
            <h1 className="text-emerald-400 font-bold text-2xl tracking-wider">
              AUTONOMOUS TRADING AGENT
            </h1>
          </div>
          <p className="text-neutral-500 text-sm">
            Query Interface • Connected to FastAPI Backend • Modal & MCP Integration
          </p>
        </div>

        {/* Query Form */}
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="space-y-4">
            <div>
              <label htmlFor="query" className="block text-sm font-medium text-neutral-300 mb-2">
                Enter your query
              </label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Examples:&#10;• search for recent Apple stock analysis&#10;• run backtest on AAPL with moving average strategy&#10;• compute VaR for my portfolio&#10;• optimize portfolio allocation for tech stocks"
                className="w-full h-32 px-4 py-3 bg-neutral-900 border border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
                disabled={loading}
              />
            </div>
            
            <button
              type="submit"
              disabled={!query.trim() || loading}
              className="flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-neutral-700 disabled:text-neutral-500 text-white font-medium rounded-lg transition-colors"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              {loading ? "Processing..." : "Execute Query"}
            </button>
          </div>
        </form>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-red-400 font-medium">Error</span>
            </div>
            <p className="text-red-300 mt-1">{error}</p>
          </div>
        )}

        {/* Results */}
        <div className="space-y-6">
          {results.map((result, idx) => (
            <div key={idx} className="p-6 bg-neutral-900 border border-neutral-800 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 font-medium">
                    {result.intent.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <div className="text-xs text-neutral-500">
                  {result.timestamp.toLocaleTimeString()}
                </div>
              </div>
              {renderResult(result)}
            </div>
          ))}
        </div>

        {results.length === 0 && !loading && (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-neutral-700 mx-auto mb-4" />
            <p className="text-neutral-500">
              Enter a query above to get started with the autonomous trading agent
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
