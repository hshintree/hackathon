# 🔗 Backend Integration Guide

This document provides a comprehensive mapping of all "REAL BACKEND INTEGRATION" points in the frontend and what needs to be implemented in the backend to make them functional.

## 📊 **Data Flow Architecture**

```
Frontend Components → API Client → FastAPI Backend → Data Sources/Modal → Database
     ↓                    ↓              ↓              ↓              ↓
Real-time UI ← WebSocket Updates ← API Responses ← External APIs ← PostgreSQL
```

---

## 🎯 **1. TRADING DASHBOARD INTEGRATION**

### **Portfolio Data (`/api/portfolio/pnl`)**
**Current Status**: Mock data in `api.py:447-465`
**Real Implementation Needed**:

```python
# In api.py - Replace mock data with real Alpaca portfolio
@app.get("/api/portfolio/pnl")
async def get_portfolio_pnl():
    try:
        from data_sources.alpaca_client import AlpacaClient
        client = AlpacaClient()
        
        # Get real portfolio data from Alpaca
        account = client.trading_client.get_account()
        positions = client.trading_client.get_all_positions()
        
        # Calculate real P&L
        total_pnl = sum(float(pos.unrealized_pl) for pos in positions)
        portfolio_value = float(account.portfolio_value)
        
        # Get daily P&L from trade history
        # TODO: Implement trade history calculation
        
        return {
            "totalPnL": total_pnl,
            "unrealizedPnL": total_pnl,
            "realizedPnL": 0.0,  # Calculate from trade history
            "totalValue": portfolio_value,
            "dailyChange": 0.0,  # Calculate from daily returns
            "dailyChangePercent": 0.0,
            "dailyPnL": 0.0,
            "portfolioValue": portfolio_value,
            "riskMetrics": {
                "sharpeRatio": 0.0,  # Calculate from returns
                "beta": 0.0,         # Calculate from market correlation
                "maxDrawdown": 0.0   # Calculate from drawdown analysis
            },
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": int(pos.qty),
                    "avgEntryPrice": float(pos.avg_entry_price),
                    "currentPrice": float(pos.current_price),
                    "unrealizedPl": float(pos.unrealized_pl),
                    "unrealizedPlPercent": float(pos.unrealized_plpc) * 100
                } for pos in positions
            ],
            "recentTrades": []  # Get from Alpaca order history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Market Data (`/api/market/data`)**
**Current Status**: Missing endpoint
**Real Implementation Needed**:

```python
# In api.py - Add new endpoint
@app.get("/api/market/data")
async def get_market_data():
    try:
        from data_sources.alpaca_client import AlpacaClient
        from data_sources.finnhub_client import FinnhubClient
        
        alpaca_client = AlpacaClient()
        finnhub_client = FinnhubClient()
        
        # Get major indices
        spx_quote = finnhub_client.get_quote("SPY")
        vix_quote = finnhub_client.get_quote("VXX")
        
        return {
            "overview": {
                "spx": {
                    "price": spx_quote["c"],
                    "change": spx_quote["d"]
                },
                "vix": {
                    "price": vix_quote["c"],
                    "change": vix_quote["d"]
                },
                "dxy": {
                    "price": 103.25,  # Get from FRED API
                    "change": 0.15
                }
            },
            "lastUpdate": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🤖 **2. AGENT NETWORK INTEGRATION**

### **Agent Status (`/api/agents/status`)**
**Current Status**: Mock data in `api.py:467-485`
**Real Implementation Needed**:

```python
# In api.py - Replace with real agent status
@app.get("/api/agents/status")
async def get_agents_status():
    try:
        # Get real agent status from LangGraph
        from agents.langgraph_agent import build_graph
        
        # TODO: Implement agent status tracking
        # This requires storing agent state in database
        
        return {
            "totalAgents": 4,
            "activeAgents": 4,
            "agents": [
                {
                    "id": "macro-analyst",
                    "name": "Macro Analyst",
                    "status": "active",
                    "lastActivity": "2 min ago"
                },
                {
                    "id": "quant-research", 
                    "name": "Quant Research",
                    "status": "active",
                    "lastActivity": "5 min ago"
                },
                {
                    "id": "risk-manager",
                    "name": "Risk Manager", 
                    "status": "active",
                    "lastActivity": "1 min ago"
                },
                {
                    "id": "execution-agent",
                    "name": "Execution Agent",
                    "status": "active", 
                    "lastActivity": "30 sec ago"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Agent Chat (`/agent/chat`)**
**Current Status**: Basic LangGraph integration in `api.py:115-122`
**Real Implementation Needed**:

```python
# In api.py - Enhance agent chat with real responses
@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    try:
        # Invoke LangGraph with user query
        state = await graph.ainvoke({"query": request.query})
        
        # Extract meaningful response from state
        result = state.get("result", {})
        context = state.get("context", [])
        
        # Format response for frontend
        response = {
            "state": state,
            "response": result.get("response", "I'm processing your request..."),
            "context": context,
            "agents_consulted": state.get("plan", "librarian")
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Agent Decisions (`/agents/{agent.id}/decisions`)**
**Current Status**: Missing endpoint
**Real Implementation Needed**:

```python
# In api.py - Add agent decision history
@app.get("/agents/{agent_id}/decisions")
async def get_agent_decisions(agent_id: str, limit: int = 50):
    try:
        # TODO: Implement decision tracking in database
        # Store agent decisions as they're made
        
        decisions = [
            {
                "id": "decision_1",
                "agent_id": agent_id,
                "decision": "Increase tech allocation by 5%",
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat(),
                "reasoning": "Strong earnings momentum detected"
            }
        ]
        
        return {"decisions": decisions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📈 **3. STRATEGY OPERATIONS INTEGRATION**

### **Strategy Status (`/api/strategies/active`)**
**Current Status**: Mock data in `api.py:487-505`
**Real Implementation Needed**:

```python
# In api.py - Replace with real strategy data
@app.get("/api/strategies/active")
async def get_active_strategies():
    try:
        # TODO: Implement strategy management system
        # Store strategies in database with status tracking
        
        return {
            "totalStrategies": 8,
            "activeStrategies": 2,
            "strategies": [
                {
                    "id": "strategy_1",
                    "name": "Momentum Trading",
                    "status": "active",
                    "allocation": 35000,
                    "pnl": 450.25,
                    "sharpe": 1.85,
                    "winRate": 68,
                    "maxDrawdown": -5.2,
                    "trades": 47,
                    "lastTrade": "2 min ago"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Strategy Control (`/api/strategies/{id}/start`, `/api/strategies/{id}/pause`, `/api/strategies/{id}/stop`)**
**Current Status**: Missing endpoints
**Real Implementation Needed**:

```python
# In api.py - Add strategy control endpoints
@app.post("/api/strategies/{strategy_id}/start")
async def start_strategy(strategy_id: str):
    try:
        # TODO: Implement strategy execution system
        # Start strategy in background process
        
        return {"status": "started", "strategy_id": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/{strategy_id}/pause")
async def pause_strategy(strategy_id: str):
    try:
        # TODO: Pause strategy execution
        return {"status": "paused", "strategy_id": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    try:
        # TODO: Stop strategy execution
        return {"status": "stopped", "strategy_id": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Backtest Results (VectorBT Integration)**
**Current Status**: Missing endpoint
**Real Implementation Needed**:

```python
# In api.py - Add backtest results endpoint
@app.get("/api/backtests/results")
async def get_backtest_results():
    try:
        # TODO: Integrate with Modal VectorBT functions
        # Call modal_app.py grid_scan_parent function
        
        return {
            "backtests": [
                {
                    "strategy": "Volatility Breakout",
                    "period": "2023-2024",
                    "returns": 24.5,
                    "sharpe": 1.67,
                    "maxDD": -12.3,
                    "status": "completed"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📰 **4. MARKET INTELLIGENCE INTEGRATION**

### **News Data (Tavily API)**
**Current Status**: Missing endpoint
**Real Implementation Needed**:

```python
# In api.py - Add news aggregation endpoint
@app.get("/api/news/latest")
async def get_latest_news(limit: int = 20):
    try:
        # TODO: Integrate with Tavily API
        # Use tavily-python for news search
        
        return {
            "news": [
                {
                    "title": "Fed Signals Potential Rate Cuts",
                    "source": "Reuters",
                    "sentiment": "bullish",  # AI sentiment analysis
                    "impact": "high",        # AI impact assessment
                    "timestamp": "15 min ago",
                    "summary": "Federal Reserve officials hint at possible rate reductions..."
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Economic Data (FRED API)**
**Current Status**: Basic endpoint in `api.py:380-400`
**Real Implementation Needed**:

```python
# In api.py - Enhance economic data endpoint
@app.get("/api/economic/indicators")
async def get_economic_indicators():
    try:
        from data_sources.fred_client import FREDClient
        
        client = FREDClient()
        
        # Get key economic indicators
        indicators = [
            {"id": "CPIAUCSL", "name": "CPI (YoY)"},
            {"id": "UNRATE", "name": "Unemployment"},
            {"id": "GDP", "name": "GDP Growth"},
            {"id": "FEDFUNDS", "name": "Fed Funds Rate"}
        ]
        
        data = []
        for indicator in indicators:
            series_data = client.get_series_data([indicator["id"]], "2023-01-01", "2024-12-31")
            if not series_data.empty:
                latest = series_data.iloc[-1]
                data.append({
                    "indicator": indicator["name"],
                    "value": f"{latest['value']:.1f}%",
                    "change": 0.0,  # Calculate change
                    "nextRelease": "Jan 15"  # Get from FRED calendar
                })
        
        return {"economic": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **SEC Filings (SEC EDGAR API)**
**Current Status**: Basic endpoint in `api.py:360-380`
**Real Implementation Needed**:

```python
# In api.py - Enhance SEC filings endpoint
@app.get("/api/sec/filings/latest")
async def get_latest_sec_filings(limit: int = 20):
    try:
        from data_sources.sec_edgar_client import SECEdgarClient
        
        client = SECEdgarClient()
        
        # Get recent filings with AI analysis
        filings = client.get_company_filings(forms=["10-K", "10-Q"], limit=limit)
        
        # TODO: Add AI analysis of filing content
        # Use LangChain to extract key insights
        
        return {
            "filings": [
                {
                    "company": "Apple Inc.",
                    "type": "10-K",
                    "filedAt": "2024-01-15T10:30:00Z",
                    "summary": "Strong iPhone sales, services revenue growth...",
                    "impact": "high"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🏥 **5. SYSTEM HEALTH INTEGRATION**

### **System Metrics**
**Current Status**: Mock data in `api.py:427-445`
**Real Implementation Needed**:

```python
# In api.py - Replace with real system metrics
@app.get("/api/system/status")
async def get_system_status():
    try:
        import psutil
        import time
        
        # Get real system metrics
        start_time = time.time()  # TODO: Store system start time
        uptime = time.time() - start_time
        
        # Get API response times
        # TODO: Implement response time tracking
        
        return {
            "totalPnL": 0.0,  # Get from portfolio endpoint
            "activeAgents": 4,  # Count from agent management
            "runningStrategies": 2,  # Count from strategy database
            "marketStatus": "OPEN",  # Get from Alpaca market calendar
            "systemUptime": f"{int(uptime//3600)}h {int((uptime%3600)//60)}m",
            "lastUpdate": datetime.now().isoformat(),
            "health": await health_check()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Modal Compute Status**
**Current Status**: Basic endpoint in `api.py:225-250`
**Real Implementation Needed**:

```python
# In api.py - Enhance Modal status endpoint
@app.get("/api/modal/status")
async def get_modal_status():
    try:
        # TODO: Integrate with Modal API
        # Get real job status and metrics
        
        return {
            "status": "running",
            "activeJobs": 12,
            "queuedJobs": 3,
            "completedToday": 847,
            "cpuUsage": 67,
            "memoryUsage": 45
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Database Health**
**Current Status**: Basic health check in `api.py:85-115`
**Real Implementation Needed**:

```python
# In api.py - Enhance database health monitoring
@app.get("/api/database/health")
async def get_database_health():
    try:
        from database.connection import get_connection_info
        
        db_info = get_connection_info()
        
        return {
            "status": "healthy",
            "connections": db_info.get("active_connections", 0),
            "queryTime": db_info.get("avg_query_time", 0),
            "storage": db_info.get("storage_usage", 0),
            "backupStatus": "completed",
            "lastBackup": "2024-01-15T02:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🔄 **6. WEBSOCKET REAL-TIME UPDATES**

### **Current Status**: Basic WebSocket endpoints in `api.py:520-599`
**Real Implementation Needed**:

```python
# In api.py - Enhance WebSocket with real data
@app.websocket("/ws/system")
async def websocket_system(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Get real system status
            system_data = await get_system_status()
            await manager.send_personal_message(
                json.dumps({
                    "type": "system_status",
                    "payload": system_data
                }), 
                websocket
            )
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Get real portfolio updates
            portfolio_data = await get_portfolio_pnl()
            await manager.send_personal_message(
                json.dumps({
                    "type": "portfolio_update",
                    "payload": portfolio_data
                }), 
                websocket
            )
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## 🗄️ **7. DATABASE SCHEMA UPDATES**

### **New Tables Needed**:

```sql
-- Agent management
CREATE TABLE agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive',
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Strategy management
CREATE TABLE strategies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'stopped',
    allocation DECIMAL(15,2) DEFAULT 0,
    pnl DECIMAL(15,2) DEFAULT 0,
    sharpe_ratio DECIMAL(10,4) DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    max_drawdown DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent decisions
CREATE TABLE agent_decisions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) REFERENCES agents(id),
    decision TEXT NOT NULL,
    confidence DECIMAL(3,2),
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System metrics
CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,4),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Trade history
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    filled_at TIMESTAMP,
    strategy_id VARCHAR(50) REFERENCES strategies(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 **8. IMPLEMENTATION PRIORITY**

### **Phase 1 (Critical)**
1. **Portfolio Data** - Connect to Alpaca API
2. **Market Data** - Connect to Finnhub/FRED APIs
3. **System Health** - Real metrics and monitoring

### **Phase 2 (Important)**
1. **Agent Status** - Real agent management
2. **Strategy Control** - Strategy execution system
3. **WebSocket Updates** - Real-time data flow

### **Phase 3 (Enhancement)**
1. **News Aggregation** - Tavily API integration
2. **SEC Filings** - AI analysis integration
3. **Backtest Results** - VectorBT integration

---

## 📝 **9. TESTING CHECKLIST**

- [ ] Portfolio data loads from Alpaca API
- [ ] Market data updates in real-time
- [ ] Agent chat returns meaningful responses
- [ ] Strategy control endpoints work
- [ ] WebSocket connections provide live updates
- [ ] System health shows real metrics
- [ ] Database queries return expected data
- [ ] Error handling works properly
- [ ] Loading states display correctly

---

## 🎯 **10. NEXT STEPS**

1. **Implement Phase 1 endpoints** with real API calls
2. **Add database tables** for state management
3. **Test WebSocket connections** with real data
4. **Add error handling** and loading states
5. **Document API responses** for frontend consumption
6. **Monitor performance** and optimize as needed

This guide provides a complete roadmap for implementing all the REAL BACKEND INTEGRATION points identified in the frontend code. 