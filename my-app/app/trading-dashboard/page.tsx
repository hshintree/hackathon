"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, AlertTriangle } from "lucide-react"
import { usePortfolioData, useMarketData } from "@/lib/hooks"

// REAL BACKEND INTEGRATION: Trading Dashboard Component
// This component displays real-time portfolio data and trading positions
// Connected to FastAPI backend with WebSocket real-time updates

export default function TradingDashboard() {
  // REAL BACKEND INTEGRATION - Using custom hooks for API calls
  const { portfolioData, loading: portfolioLoading, error: portfolioError } = usePortfolioData()
  const { marketData, loading: marketLoading, error: marketError } = useMarketData()

  // Real portfolio positions from Alpaca API
  const positions = portfolioData?.positions || []
  
  // Real market data from Finnhub/Alpaca APIs
  const marketOverview = marketData?.overview || {
    spx: { price: 0, change: 0 },
    vix: { price: 0, change: 0 },
    dxy: { price: 0, change: 0 },
  }

  // Calculate real portfolio metrics
  const totalPnL = portfolioData?.totalPnL || 0
  const dailyPnL = portfolioData?.dailyPnL || 0
  const portfolioValue = portfolioData?.portfolioValue || 0
  const dailyChange = portfolioData?.dailyChange || 0
  const riskMetrics = portfolioData?.riskMetrics || {
    sharpeRatio: 0,
    beta: 0,
    maxDrawdown: 0,
  }

  // Real trade history from Alpaca API
  const recentTrades = portfolioData?.recentTrades || []

  // Loading states
  if (portfolioLoading || marketLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading trading data...</div>
      </div>
    )
  }

  // Error states
  if (portfolioError || marketError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">
          Error loading trading data: {portfolioError || marketError}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Get from Alpaca portfolio.unrealized_pl + realized_pl */}
              ${totalPnL.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              {/* REAL BACKEND INTEGRATION: Calculate daily P&L from trade history */}
              {dailyPnL >= 0 ? "+" : ""}{dailyPnL.toFixed(2)} today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Get from Alpaca portfolio.portfolio_value */}
              ${portfolioValue.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {/* REAL BACKEND INTEGRATION: Calculate daily percentage change */}
              {dailyChange >= 0 ? "+" : ""}{dailyChange.toFixed(2)}% today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Calculate from your risk management system */}
              {riskMetrics.sharpeRatio.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              {/* REAL BACKEND INTEGRATION: Calculate portfolio beta from your risk models */}
              Beta: {riskMetrics.beta.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {riskMetrics.maxDrawdown.toFixed(2)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Current risk level
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Market Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Market Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">S&P 500</span>
              <div className="text-right">
                <div className="font-semibold">
                  {/* REAL BACKEND INTEGRATION: Get from Finnhub quote endpoint */}
                  ${marketOverview.spx.price.toFixed(2)}
                </div>
                <div className={`text-xs ${marketOverview.spx.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {/* REAL BACKEND INTEGRATION: Calculate from Finnhub price change data */}
                  {marketOverview.spx.change >= 0 ? "+" : ""}{marketOverview.spx.change.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">VIX</span>
              <div className="text-right">
                <div className="font-semibold">{marketOverview.vix.price.toFixed(2)}</div>
                <div className={`text-xs ${marketOverview.vix.change >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {marketOverview.vix.change >= 0 ? "+" : ""}{marketOverview.vix.change.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Dollar Index</span>
              <div className="text-right">
                <div className="font-semibold">{marketOverview.dxy.price.toFixed(2)}</div>
                <div className={`text-xs ${marketOverview.dxy.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {marketOverview.dxy.change >= 0 ? "+" : ""}{marketOverview.dxy.change.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Positions */}
      <Card>
        <CardHeader>
          <CardTitle>Current Positions</CardTitle>
          <div className="text-sm text-muted-foreground">
            {/* REAL BACKEND INTEGRATION: Count from actual positions */}
            {positions.length} positions
          </div>
          <div className="text-sm text-muted-foreground">
            {/* REAL BACKEND INTEGRATION: Count long/short positions from Alpaca data */}
            {positions.filter(p => p.quantity > 0).length} long, {positions.filter(p => p.quantity < 0).length} short
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {positions.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No active positions
              </div>
            ) : (
              positions.map((position) => (
                <div key={position.symbol} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div>
                      <div className="font-semibold">
                        {/* REAL BACKEND INTEGRATION: Map over real Alpaca positions */}
                        {/* REAL BACKEND INTEGRATION: position.symbol */}
                        {position.symbol}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {/* REAL BACKEND INTEGRATION: position.qty */}
                        {position.quantity} shares
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">
                      {/* REAL BACKEND INTEGRATION: position.avg_entry_price */}
                      Avg: ${position.avgEntryPrice?.toFixed(2) || "N/A"}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {/* REAL BACKEND INTEGRATION: Get from live market data feed */}
                      Current: ${position.currentPrice?.toFixed(2) || "N/A"}
                    </div>
                    <div className={`font-semibold ${position.unrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {/* REAL BACKEND INTEGRATION: position.unrealized_pl */}${position.unrealizedPl?.toFixed(2) || "N/A"}
                    </div>
                    <div className={`text-xs ${position.unrealizedPl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {/* REAL BACKEND INTEGRATION: Calculate percentage from position data */}
                      {position.unrealizedPlPercent ? `${position.unrealizedPlPercent >= 0 ? '+' : ''}${position.unrealizedPlPercent.toFixed(2)}%` : "N/A"}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentTrades.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No recent trades
              </div>
            ) : (
              recentTrades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <Badge variant={trade.side === 'buy' ? 'default' : 'secondary'}>
                      {/* REAL BACKEND INTEGRATION: Get from Alpaca TradingClient.get_orders() */}
                      {/* REAL BACKEND INTEGRATION: order.side (buy/sell) */}
                      {trade.side?.toUpperCase()}
                    </Badge>
                    <div>
                      <div className="font-semibold">
                        {/* REAL BACKEND INTEGRATION: order.symbol */}
                        {trade.symbol}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {/* REAL BACKEND INTEGRATION: order.qty @ order.filled_avg_price */}
                        {trade.quantity} @ ${trade.filledAvgPrice?.toFixed(2) || "N/A"}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">
                      {/* REAL BACKEND INTEGRATION: Format order.filled_at timestamp */}
                      {trade.filledAt ? new Date(trade.filledAt).toLocaleString() : "N/A"}
                    </div>
                    <div className="font-semibold">
                      ${trade.filledAvgPrice ? (trade.filledAvgPrice * trade.quantity).toFixed(2) : "N/A"}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
