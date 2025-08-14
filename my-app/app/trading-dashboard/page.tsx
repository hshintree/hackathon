"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, AlertTriangle } from "lucide-react"

export default function TradingDashboard() {
  const [positions, setPositions] = useState([
    { symbol: "AAPL", quantity: 100, avgPrice: 175.5, currentPrice: 178.25, pnl: 275.0 },
    { symbol: "TSLA", quantity: 50, avgPrice: 245.8, currentPrice: 242.15, pnl: -182.5 },
    { symbol: "NVDA", quantity: 25, avgPrice: 890.2, currentPrice: 925.75, pnl: 888.75 },
  ])

  const [marketData, setMarketData] = useState({
    spx: { price: 4185.25, change: 12.45 },
    vix: { price: 18.75, change: -0.85 },
    dxy: { price: 103.25, change: 0.15 },
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setPositions((prev) =>
        prev.map((pos) => ({
          ...pos,
          currentPrice: pos.currentPrice + (Math.random() - 0.5) * 2,
          pnl: (pos.currentPrice - pos.avgPrice) * pos.quantity,
        })),
      )

      setMarketData((prev) => ({
        spx: { ...prev.spx, price: prev.spx.price + (Math.random() - 0.5) * 5 },
        vix: { ...prev.vix, price: prev.vix.price + (Math.random() - 0.5) * 0.5 },
        dxy: { ...prev.dxy, price: prev.dxy.price + (Math.random() - 0.5) * 0.2 },
      }))
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0)

  return (
    <div className="p-6 space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Total P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${totalPnL >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              ${totalPnL.toFixed(2)}
            </div>
            <div className="text-xs text-neutral-500">Today: +$1,247.85</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Portfolio Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">$127,450</div>
            <div className="text-xs text-emerald-400">+2.4% today</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Active Positions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{positions.length}</div>
            <div className="text-xs text-neutral-500">3 long, 0 short</div>
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
            <div className="text-2xl font-bold text-yellow-400">MEDIUM</div>
            <div className="text-xs text-neutral-500">Beta: 1.2</div>
          </CardContent>
        </Card>
      </div>

      {/* Market Overview */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400">Market Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(marketData).map(([key, data]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-neutral-800 rounded">
                <div>
                  <div className="text-sm text-neutral-400">{key.toUpperCase()}</div>
                  <div className="text-lg font-bold text-white">{data.price.toFixed(2)}</div>
                </div>
                <div className={`flex items-center gap-1 ${data.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {data.change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  <span className="text-sm">
                    {data.change >= 0 ? "+" : ""}
                    {data.change.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Current Positions */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400">Current Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {positions.map((position, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-neutral-800 rounded">
                <div className="flex items-center gap-4">
                  <div>
                    <div className="font-bold text-white">{position.symbol}</div>
                    <div className="text-sm text-neutral-400">{position.quantity} shares</div>
                  </div>
                  <div>
                    <div className="text-sm text-neutral-400">Avg: ${position.avgPrice.toFixed(2)}</div>
                    <div className="text-sm text-white">Current: ${position.currentPrice.toFixed(2)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-bold ${position.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    ${position.pnl.toFixed(2)}
                  </div>
                  <Badge variant={position.pnl >= 0 ? "default" : "destructive"} className="text-xs">
                    {(((position.currentPrice - position.avgPrice) / position.avgPrice) * 100).toFixed(1)}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400">Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { symbol: "MSFT", action: "BUY", quantity: 75, price: 412.5, time: "10:30 AM" },
              { symbol: "GOOGL", action: "SELL", quantity: 30, price: 138.75, time: "09:45 AM" },
              { symbol: "AMZN", action: "BUY", quantity: 40, price: 145.2, time: "09:15 AM" },
            ].map((trade, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-neutral-800 rounded">
                <div className="flex items-center gap-4">
                  <Badge variant={trade.action === "BUY" ? "default" : "secondary"}>{trade.action}</Badge>
                  <div>
                    <div className="font-bold text-white">{trade.symbol}</div>
                    <div className="text-sm text-neutral-400">
                      {trade.quantity} shares @ ${trade.price}
                    </div>
                  </div>
                </div>
                <div className="text-sm text-neutral-400">{trade.time}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
