"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Target, TrendingUp, BarChart3, Play, Pause, Settings, AlertTriangle } from "lucide-react"

export default function StrategyOperations() {
  const [strategies, setStrategies] = useState([
    {
      id: "momentum-1",
      name: "Momentum Strategy Alpha",
      status: "running",
      allocation: 35000,
      pnl: 2847.5,
      sharpe: 1.85,
      maxDrawdown: -5.2,
      winRate: 68,
      trades: 47,
      lastTrade: "2 min ago",
    },
    {
      id: "mean-reversion",
      name: "Mean Reversion Pro",
      status: "paused",
      allocation: 25000,
      pnl: -432.1,
      sharpe: 0.92,
      maxDrawdown: -8.1,
      winRate: 55,
      trades: 23,
      lastTrade: "1 hour ago",
    },
    {
      id: "pairs-trading",
      name: "Statistical Arbitrage",
      status: "running",
      allocation: 40000,
      pnl: 1205.75,
      sharpe: 2.1,
      maxDrawdown: -3.8,
      winRate: 72,
      trades: 89,
      lastTrade: "5 min ago",
    },
  ])

  const [backtestResults, setBacktestResults] = useState([
    {
      strategy: "Volatility Breakout",
      period: "2023-2024",
      returns: 24.5,
      sharpe: 1.67,
      maxDD: -12.3,
      status: "completed",
    },
    {
      strategy: "Sector Rotation",
      period: "2023-2024",
      returns: 18.2,
      sharpe: 1.45,
      maxDD: -9.8,
      status: "completed",
    },
    {
      strategy: "ML Momentum",
      period: "2024 YTD",
      returns: 31.7,
      sharpe: 2.23,
      maxDD: -7.1,
      status: "running",
    },
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      setStrategies((prev) =>
        prev.map((strategy) => ({
          ...strategy,
          pnl: strategy.pnl + (Math.random() - 0.5) * 50,
          trades: strategy.status === "running" ? strategy.trades + Math.floor(Math.random() * 2) : strategy.trades,
        })),
      )
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Strategy Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Active Strategies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {strategies.filter((s) => s.status === "running").length}
            </div>
            <div className="text-xs text-emerald-400">2 running, 1 paused</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Total Strategy P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">
              ${strategies.reduce((sum, s) => sum + s.pnl, 0).toFixed(2)}
            </div>
            <div className="text-xs text-neutral-500">+12.4% this month</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Avg Sharpe Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {(strategies.reduce((sum, s) => sum + s.sharpe, 0) / strategies.length).toFixed(2)}
            </div>
            <div className="text-xs text-emerald-400">Above benchmark</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Risk Level
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">MODERATE</div>
            <div className="text-xs text-neutral-500">Max DD: -8.1%</div>
          </CardContent>
        </Card>
      </div>

      {/* Active Strategies */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400">Active Strategies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {strategies.map((strategy) => (
              <div key={strategy.id} className="p-4 bg-neutral-800 rounded">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div>
                      <h3 className="font-bold text-white">{strategy.name}</h3>
                      <div className="text-sm text-neutral-400">
                        Allocation: ${strategy.allocation.toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={strategy.status === "running" ? "default" : "secondary"}
                      className={strategy.status === "running" ? "bg-emerald-500" : ""}
                    >
                      {strategy.status.toUpperCase()}
                    </Badge>
                    <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-white">
                      {strategy.status === "running" ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-white">
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm">
                  <div>
                    <div className="text-neutral-400">P&L</div>
                    <div className={`font-bold ${strategy.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      ${strategy.pnl.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-neutral-400">Sharpe</div>
                    <div className="font-bold text-white">{strategy.sharpe}</div>
                  </div>
                  <div>
                    <div className="text-neutral-400">Max DD</div>
                    <div className="font-bold text-red-400">{strategy.maxDrawdown}%</div>
                  </div>
                  <div>
                    <div className="text-neutral-400">Win Rate</div>
                    <div className="font-bold text-white">{strategy.winRate}%</div>
                  </div>
                  <div>
                    <div className="text-neutral-400">Trades</div>
                    <div className="font-bold text-white">{strategy.trades}</div>
                  </div>
                  <div>
                    <div className="text-neutral-400">Last Trade</div>
                    <div className="font-bold text-neutral-300">{strategy.lastTrade}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Backtest Results */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400">Backtest Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {backtestResults.map((result, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-neutral-800 rounded">
                <div>
                  <div className="font-bold text-white">{result.strategy}</div>
                  <div className="text-sm text-neutral-400">{result.period}</div>
                </div>
                <div className="grid grid-cols-4 gap-6 text-sm">
                  <div className="text-center">
                    <div className="text-neutral-400">Returns</div>
                    <div className="font-bold text-emerald-400">{result.returns}%</div>
                  </div>
                  <div className="text-center">
                    <div className="text-neutral-400">Sharpe</div>
                    <div className="font-bold text-white">{result.sharpe}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-neutral-400">Max DD</div>
                    <div className="font-bold text-red-400">{result.maxDD}%</div>
                  </div>
                  <div className="text-center">
                    <Badge variant={result.status === "completed" ? "default" : "secondary"}>{result.status}</Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
