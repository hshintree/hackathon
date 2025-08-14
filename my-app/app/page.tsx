"use client"

import { useState, useEffect } from "react"
import { ChevronRight, TrendingUp, Bot, Target, Brain, Server, Bell, RefreshCw, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import TradingDashboard from "./trading-dashboard/page"
import AgentNetwork from "./agent-network/page"
import StrategyOperations from "./strategy-operations/page"
import MarketIntelligence from "./market-intelligence/page"
import SystemHealth from "./system-health/page"

// BACKEND INTEGRATION: Main Dashboard Component
// This component orchestrates the entire autonomous trading system
//
// GITHUB REPO CONNECTIONS:
// 1. Connect to FastAPI backend (main.py) for real-time system status
// 2. WebSocket connection for live updates (websockets==12.0)
// 3. Database queries via SQLAlchemy for persistent state
// 4. Modal compute status monitoring
//
// API ENDPOINTS TO IMPLEMENT:
// - GET /api/system/status - Overall system health and metrics
// - GET /api/portfolio/pnl - Real-time P&L calculations
// - GET /api/agents/status - Active agent count and status
// - GET /api/strategies/active - Running strategy count
// - GET /api/market/status - Market hours and trading status
// - WebSocket /ws/system - Real-time system updates

export default function AutonomousTradingDashboard() {
  const [activeSection, setActiveSection] = useState("dashboard")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // MOCK DATA - REPLACE WITH REAL API CALLS
  // Connect to your FastAPI backend endpoints:
  // - systemStatus should come from GET /api/system/status
  // - Use WebSocket connection for real-time updates
  const [systemStatus, setSystemStatus] = useState({
    totalPnL: 0, // REPLACE: Get from Alpaca API portfolio.unrealized_pl + realized_pl
    activeAgents: 4, // REPLACE: Count from your agent management system
    runningStrategies: 0, // REPLACE: Count from active strategy database table
    marketStatus: "OPEN", // REPLACE: Get from Alpaca API market calendar
  })

  useEffect(() => {
    // BACKEND INTEGRATION: Replace this mock interval with WebSocket connection
    //
    // IMPLEMENTATION STEPS:
    // 1. Create WebSocket connection to your FastAPI backend
    // 2. Listen for real-time updates from your trading system
    // 3. Update state based on actual portfolio changes
    //
    // EXAMPLE WEBSOCKET SETUP:
    // const ws = new WebSocket('ws://localhost:8000/ws/system')
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data)
    //   setSystemStatus(data)
    // }

    const interval = setInterval(() => {
      // REMOVE THIS MOCK CODE - Replace with real WebSocket updates
      setSystemStatus((prev) => ({
        ...prev,
        totalPnL: prev.totalPnL + (Math.random() - 0.5) * 100,
        runningStrategies: Math.floor(Math.random() * 8) + 2,
      }))
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // BACKEND INTEGRATION: Add authentication check here
  // Check if user is authenticated with your system
  // Redirect to login if not authenticated

  return (
    <div className="flex h-screen bg-neutral-950">
      {/* Sidebar */}
      <div
        className={`${sidebarCollapsed ? "w-16" : "w-72"} bg-neutral-900 border-r border-neutral-800 transition-all duration-300 fixed md:relative z-50 md:z-auto h-full md:h-auto ${!sidebarCollapsed ? "md:block" : ""}`}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-8">
            <div className={`${sidebarCollapsed ? "hidden" : "block"}`}>
              <h1 className="text-emerald-400 font-bold text-lg tracking-wider">AUTONOMOUS TRADER</h1>
              {/* BACKEND INTEGRATION: Get version from your system config */}
              <p className="text-neutral-500 text-xs">v2.1.7 • LIVE TRADING</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="text-neutral-400 hover:text-emerald-400"
            >
              <ChevronRight
                className={`w-4 h-4 sm:w-5 sm:h-5 transition-transform ${sidebarCollapsed ? "" : "rotate-180"}`}
              />
            </Button>
          </div>

          <nav className="space-y-2">
            {[
              { id: "dashboard", icon: TrendingUp, label: "TRADING DASHBOARD", color: "emerald" },
              { id: "agents", icon: Bot, label: "AI AGENTS", color: "blue" },
              { id: "strategies", icon: Target, label: "STRATEGIES", color: "purple" },
              { id: "intelligence", icon: Brain, label: "MARKET INTEL", color: "orange" },
              { id: "systems", icon: Server, label: "SYSTEM HEALTH", color: "red" },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center gap-3 p-3 rounded transition-colors ${
                  activeSection === item.id
                    ? `bg-${item.color}-500 text-white`
                    : "text-neutral-400 hover:text-white hover:bg-neutral-800"
                }`}
              >
                <item.icon className="w-5 h-5 md:w-5 md:h-5 sm:w-6 sm:h-6" />
                {!sidebarCollapsed && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            ))}
          </nav>

          {!sidebarCollapsed && (
            <div className="mt-8 space-y-4">
              {/* P&L Summary */}
              {/* BACKEND INTEGRATION: Connect to Alpaca API for real P&L */}
              <div className="p-4 bg-neutral-800 border border-neutral-700 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-emerald-400 font-medium">TOTAL P&L</span>
                </div>
                <div
                  className={`text-lg font-bold ${systemStatus.totalPnL >= 0 ? "text-emerald-400" : "text-red-400"}`}
                >
                  {/* MOCK DATA - REPLACE: Get from alpaca-py TradingClient.get_portfolio() */}$
                  {systemStatus.totalPnL.toFixed(2)}
                </div>
              </div>

              {/* System Status */}
              {/* BACKEND INTEGRATION: Connect to your system monitoring */}
              <div className="p-4 bg-neutral-800 border border-neutral-700 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-emerald-400">SYSTEM ONLINE</span>
                </div>
                <div className="text-xs text-neutral-500 space-y-1">
                  {/* MOCK DATA - REPLACE: Get from Alpaca market calendar API */}
                  <div>MARKET: {systemStatus.marketStatus}</div>
                  {/* MOCK DATA - REPLACE: Count from your agent management database */}
                  <div>AI AGENTS: {systemStatus.activeAgents} ACTIVE</div>
                  {/* MOCK DATA - REPLACE: Count from your strategy execution database */}
                  <div>STRATEGIES: {systemStatus.runningStrategies} RUNNING</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Overlay */}
      {!sidebarCollapsed && (
        <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setSidebarCollapsed(true)} />
      )}

      {/* Main Content */}
      <div className={`flex-1 flex flex-col ${!sidebarCollapsed ? "md:ml-0" : ""}`}>
        {/* Top Toolbar */}
        <div className="h-16 bg-neutral-900 border-b border-neutral-800 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="text-sm text-neutral-400">
              AUTONOMOUS TRADER / <span className="text-emerald-400">{activeSection.toUpperCase()}</span>
            </div>
            {/* BACKEND INTEGRATION: Get trading mode from your system config */}
            <Badge variant="outline" className="text-xs border-emerald-500 text-emerald-400">
              PAPER TRADING
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            {/* BACKEND INTEGRATION: Get last update timestamp from your system */}
            <div className="text-xs text-neutral-500">LAST UPDATE: {new Date().toLocaleTimeString()}</div>
            <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-emerald-400">
              <Bell className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-emerald-400">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-auto bg-neutral-950">
          {activeSection === "dashboard" && <TradingDashboard />}
          {activeSection === "agents" && <AgentNetwork />}
          {activeSection === "strategies" && <StrategyOperations />}
          {activeSection === "intelligence" && <MarketIntelligence />}
          {activeSection === "systems" && <SystemHealth />}
        </div>
      </div>
    </div>
  )
}

/*
DATABASE SCHEMA REQUIREMENTS (PostgreSQL with SQLAlchemy):

1. SYSTEM_STATUS table:
   - id (Primary Key)
   - total_pnl (Decimal)
   - active_agents (Integer)
   - running_strategies (Integer)
   - market_status (String)
   - last_updated (Timestamp)

2. AGENTS table:
   - id (Primary Key)
   - name (String) - "Macro Analyst", "Quant Research", etc.
   - status (String) - "ACTIVE", "IDLE", "ERROR"
   - confidence_level (Float)
   - last_decision (Text)
   - created_at (Timestamp)

3. STRATEGIES table:
   - id (Primary Key)
   - name (String)
   - status (String) - "RUNNING", "PAUSED", "STOPPED"
   - performance (Decimal)
   - risk_level (String)
   - created_at (Timestamp)

4. PORTFOLIO table:
   - id (Primary Key)
   - symbol (String)
   - quantity (Integer)
   - avg_cost (Decimal)
   - current_price (Decimal)
   - unrealized_pnl (Decimal)
   - last_updated (Timestamp)

REDIS CACHE STRUCTURE:
- system:status - Current system status (JSON)
- agents:active - List of active agent IDs
- market:status - Current market status
- portfolio:pnl - Real-time P&L data
*/
