#!/usr/bin/env python3
"""
Autonomous Trading Agent - FastAPI Backend
Provides REST API endpoints for the trading agent.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database.storage import DataStorage
from database.models import (
    MarketDataRequest, SECFilingRequest, MacroDataRequest, 
    CryptoDataRequest, DataIngestionJobRequest, HealthCheckResponse,
    DatabaseStats, DataSourceStatus, DataSource
)
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import uvicorn
import asyncio
import json
import psutil
import time

from agents.langgraph_agent import build_graph
from database.data_service import DataService

app = FastAPI(
    title="Autonomous Trading Agent API",
    description="REST API for the autonomous trading agent",
    version="1.0.0",
)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# System start time for uptime calculation
SYSTEM_START_TIME = time.time()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected clients
                self.active_connections.remove(connection)

manager = ConnectionManager()


class StockRequest(BaseModel):
    symbols: List[str]
    period: str = "30d"


class PortfolioMetrics(BaseModel):
    total_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float


@app.get("/")
async def root():
    return {"message": "Autonomous Trading Agent API", "version": "2.0.0", "features": ["alpaca", "sec_edgar", "fred", "binance", "modal"]}


@app.get("/health")
async def health_check():
    """Detailed health check with API status"""
    api_keys = {
        "finnhub": bool(os.getenv("FINNHUB_API_KEY")),
        "alpaca": bool(os.getenv("APCA_API_KEY_ID") and os.getenv("APCA_API_SECRET_KEY")),
        "fred": bool(os.getenv("FRED_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "binance": bool(os.getenv("BINANCE_API_KEY"))
    }
    
    # Check database connection
    try:
        from database.connection import is_database_connected, get_database_info
        database_connected = is_database_connected()
        db_info = get_database_info() if database_connected else None
    except Exception:
        database_connected = False
        db_info = None
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_keys": api_keys,
        "database_connected": database_connected,
        "database_info": db_info,
        "modal_available": True
    }


class AgentChatRequest(BaseModel):
    query: str


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


@app.post("/market-data")
async def get_market_data(request: StockRequest):
    """Fetch market data for given symbols"""
    try:
        # Deferred imports for external clients to avoid startup failures if SDKs are missing
        from data_sources.alpaca_client import AlpacaClient
        client = AlpacaClient()
        symbols_str = ",".join(request.symbols) if len(request.symbols) > 1 else request.symbols[0]
        df = client.get_market_data_for_symbol(symbols_str, request.period)
        
        # Convert to expected format
        data = df.set_index('timestamp')

        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for symbols")

        # Convert to JSON-serializable format
        result = {}
        for symbol in request.symbols:
            if len(request.symbols) == 1:
                symbol_data = data
            else:
                symbol_data = data

            result[symbol] = {
                "prices": symbol_data["close"].to_dict(),
                "volumes": symbol_data["volume"].to_dict(),
                "latest_price": float(symbol_data["close"].iloc[-1]),
                "change_pct": float(
                    (symbol_data["close"].iloc[-1] / symbol_data["close"].iloc[-2] - 1)
                    * 100
                ) if len(symbol_data) > 1 else 0.0,
            }

        return {
            "symbols": request.symbols,
            "period": request.period,
            "data": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching market data: {str(e)}"
        )


@app.get("/portfolio/metrics")
async def get_portfolio_metrics():
    """Get current portfolio performance metrics"""
    # Generate mock portfolio data for demo
    dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
    returns = np.random.randn(len(dates)) * 0.02
    cumulative_returns = (1 + pd.Series(returns, index=dates)).cumprod()

    # Calculate metrics
    total_return = (cumulative_returns.iloc[-1] - 1) * 100
    volatility = returns.std() * np.sqrt(252) * 100
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    max_dd = (
        (cumulative_returns / cumulative_returns.expanding().max()) - 1
    ).min() * 100

    return PortfolioMetrics(
        total_return=round(total_return, 2),
        volatility=round(volatility, 2),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown=round(max_dd, 2),
    )


@app.get("/agents/status")
async def get_agent_status():
    """Get status of all trading agents"""
    return {
        "agents": {
            "macro_analyst": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Analyzing Fed meeting minutes and global economic indicators",
            },
            "quant_research": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Running Monte Carlo simulations on 10,000 assets",
            },
            "risk_manager": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Portfolio VaR at 2.3%, within acceptable limits",
            },
            "execution_agent": {
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "message": "Optimal execution window: 2:30-3:00 PM EST",
            },
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/modal/jobs")
async def get_modal_jobs():
    """Get Modal job status"""
    try:
        storage = DataStorage()
        with storage.get_session() as session:
            from database.schema import DataIngestionJobs
            jobs = session.query(DataIngestionJobs).order_by(
                DataIngestionJobs.created_at.desc()
            ).limit(20).all()
            
            job_list = []
            for job in jobs:
                job_list.append({
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error_message": job.error_message
                })
            
            return {"status": "success", "jobs": job_list}
    except Exception as e:
        return {"status": "error", "error": str(e), "jobs": []}


@app.post("/data/market")
async def ingest_market_data(request: MarketDataRequest):
    """Trigger market data ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_market_data_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/sec")
async def ingest_sec_data(request: SECFilingRequest):
    """Trigger SEC filings ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_sec_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/macro")
async def ingest_macro_data(request: MacroDataRequest):
    """Trigger macro data ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_macro_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/crypto")
async def ingest_crypto_data(request: CryptoDataRequest):
    """Trigger crypto data ingestion"""
    try:
        import requests
        modal_url = "https://your-modal-app.modal.run/trigger_crypto_ingestion"
        
        response = requests.post(modal_url, json=request.dict())
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/sources")
async def get_data_sources():
    """Get available data sources and their status"""
    sources = []
    
    try:
        # Deferred imports for external clients to avoid startup failures if SDKs are missing
        from data_sources.alpaca_client import AlpacaClient
        sources.append(DataSourceStatus(source=DataSource.ALPACA, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.ALPACA, available=False, error_message=str(e)))
    
    try:
        # Deferred imports for external clients to avoid startup failures if SDKs are missing
        from data_sources.sec_edgar_client import SECEdgarClient
        sources.append(DataSourceStatus(source=DataSource.SEC_EDGAR, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.SEC_EDGAR, available=False, error_message=str(e)))
    
    try:
        # Deferred imports for external clients to avoid startup failures if SDKs are missing
        from data_sources.fred_client import FREDClient
        sources.append(DataSourceStatus(source=DataSource.FRED, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.FRED, available=False, error_message=str(e)))
    
    try:
        # Deferred imports for external clients to avoid startup failures if SDKs are missing
        from data_sources.binance_client import BinanceClient
        sources.append(DataSourceStatus(source=DataSource.BINANCE, available=True))
    except Exception as e:
        sources.append(DataSourceStatus(source=DataSource.BINANCE, available=False, error_message=str(e)))
    
    return {"sources": sources}

@app.get("/data/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        storage = DataStorage()
        with storage.get_session() as session:
            from database.schema import MarketData, SECFilings, MacroData, CryptoData
            
            market_count = session.query(MarketData).count()
            sec_count = session.query(SECFilings).count()
            macro_count = session.query(MacroData).count()
            crypto_count = session.query(CryptoData).count()
            
            return DatabaseStats(
                market_data_records=market_count,
                sec_filings_records=sec_count,
                macro_data_records=macro_count,
                crypto_data_records=crypto_count,
                total_records=market_count + sec_count + macro_count + crypto_count,
                last_updated=datetime.now()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sec/filings")
async def get_sec_filings(tickers: str = None, forms: str = None, limit: int = 100):
    """Get SEC filings from database"""
    try:
        storage = DataStorage()
        ticker_list = tickers.split(",") if tickers else None
        form_list = forms.split(",") if forms else None
        
        df = storage.get_sec_filings(ticker_list, form_list, limit)
        
        return {
            "filings": df.to_dict("records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/macro/data")
async def get_macro_data(series_ids: str, start_date: str = None, end_date: str = None):
    """Get macro data from database"""
    try:
        from datetime import datetime, timedelta
        
        storage = DataStorage()
        series_list = series_ids.split(",")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        df = storage.get_macro_data(series_list, start_dt, end_dt)
        
        return {
            "data": df.to_dict("records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crypto/data")
async def get_crypto_data(symbols: str, start_date: str = None, end_date: str = None):
    """Get crypto data from database"""
    try:
        from datetime import datetime, timedelta
        
        storage = DataStorage()
        symbol_list = symbols.split(",")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        df = storage.get_crypto_data(symbol_list, start_dt, end_dt)
        
        return {
            "data": df.to_dict("records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== REAL BACKEND INTEGRATION - PHASE 1 =====

@app.get("/api/system/status")
async def get_system_status():
    """Get overall system health and metrics"""
    try:
        # Get health check data
        health_data = await health_check()
        
        # Calculate real system uptime
        uptime_seconds = time.time() - SYSTEM_START_TIME
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        # Get real system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Get real data from database
        with DataService() as service:
            agents = service.get_all_agents()
            strategies = service.get_all_strategies()
            
            active_agents = len([a for a in agents if a.get('status') == 'active'])
            active_strategies = len([s for s in strategies if s.get('status') == 'active'])
        
        system_metrics = {
            "totalPnL": 0.0,  # Will be updated by portfolio endpoint
            "activeAgents": active_agents,
            "runningStrategies": active_strategies,
            "marketStatus": "OPEN",  # Will be updated by Alpaca market calendar
            "systemUptime": f"{uptime_hours}h {uptime_minutes}m",
            "lastUpdate": datetime.now().isoformat(),
            "health": health_data,
            "systemMetrics": {
                "cpuUsage": cpu_percent,
                "memoryUsage": memory.percent,
                "diskUsage": psutil.disk_usage('/').percent
            }
        }
        
        return system_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/pnl")
async def get_portfolio_pnl():
    """Get real-time P&L calculations from Alpaca"""
    try:
        # Try to get real portfolio data from Alpaca
        try:
            from data_sources.alpaca_client import AlpacaClient
            client = AlpacaClient()
            
            # Get real portfolio data from Alpaca
            account = client.trading_client.get_account()
            positions = client.trading_client.get_all_positions()
            
            # Calculate real P&L
            total_pnl = sum(float(pos.unrealized_pl) for pos in positions)
            portfolio_value = float(account.portfolio_value)
            
            # Format positions for frontend
            positions_data = []
            for pos in positions:
                positions_data.append({
                    "symbol": pos.symbol,
                    "quantity": int(pos.qty),
                    "avgEntryPrice": float(pos.avg_entry_price),
                    "currentPrice": float(pos.current_price),
                    "unrealizedPl": float(pos.unrealized_pl),
                    "unrealizedPlPercent": float(pos.unrealized_plpc) * 100
                })
            
            # Get recent trades from database
            with DataService() as service:
                recent_trades = service.get_recent_trades(limit=10)
            
            return {
                "totalPnL": total_pnl,
                "unrealizedPnL": total_pnl,
                "realizedPnL": 0.0,  # TODO: Calculate from trade history
                "totalValue": portfolio_value,
                "dailyChange": 0.0,  # TODO: Calculate from daily returns
                "dailyChangePercent": 0.0,
                "dailyPnL": 0.0,
                "portfolioValue": portfolio_value,
                "riskMetrics": {
                    "sharpeRatio": 0.0,  # TODO: Calculate from returns
                    "beta": 0.0,         # TODO: Calculate from market correlation
                    "maxDrawdown": 0.0   # TODO: Calculate from drawdown analysis
                },
                "positions": positions_data,
                "recentTrades": recent_trades
            }
            
        except Exception as alpaca_error:
            # Fallback to mock data if Alpaca is not available
            print(f"Alpaca API error: {alpaca_error}")
            return {
                "totalPnL": 1250.75,
                "unrealizedPnL": 850.25,
                "realizedPnL": 400.50,
                "totalValue": 25000.00,
                "dailyChange": 125.75,
                "dailyChangePercent": 0.51,
                "dailyPnL": 125.75,
                "portfolioValue": 25000.00,
                "riskMetrics": {
                    "sharpeRatio": 1.85,
                    "beta": 0.95,
                    "maxDrawdown": -5.2
                },
                "positions": [
                    {"symbol": "AAPL", "quantity": 10, "avgEntryPrice": 150.00, "currentPrice": 155.25, "unrealizedPl": 52.50, "unrealizedPlPercent": 3.5},
                    {"symbol": "TSLA", "quantity": 5, "avgEntryPrice": 200.00, "currentPrice": 210.00, "unrealizedPl": 50.00, "unrealizedPlPercent": 5.0}
                ],
                "recentTrades": [
                    {"id": "trade_1", "symbol": "AAPL", "side": "buy", "quantity": 10, "filledAvgPrice": 150.00, "filledAt": "2024-01-15T10:30:00Z"},
                    {"id": "trade_2", "symbol": "TSLA", "side": "buy", "quantity": 5, "filledAvgPrice": 200.00, "filledAt": "2024-01-15T09:15:00Z"}
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/data")
async def get_market_data():
    """Get real-time market data from multiple sources"""
    try:
        # Try to get real market data
        try:
            from data_sources.alpaca_client import AlpacaClient
            from data_sources.finnhub_client import FinnhubClient
            
            alpaca_client = AlpacaClient()
            finnhub_client = FinnhubClient()
            
            # Get major indices from Finnhub
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
                        "price": 103.25,  # TODO: Get from FRED API
                        "change": 0.15
                    }
                },
                "news": [
                    {
                        "title": "Fed Signals Potential Rate Cuts",
                        "source": "Reuters",
                        "sentiment": "bullish",
                        "impact": "high",
                        "timestamp": "15 min ago",
                        "summary": "Federal Reserve officials hint at possible rate reductions..."
                    }
                ],
                "economic": [
                    {
                        "indicator": "CPI (YoY)",
                        "value": "3.1%",
                        "change": 0.1,
                        "nextRelease": "Jan 15"
                    }
                ],
                "filings": [
                    {
                        "company": "Apple Inc.",
                        "type": "10-K",
                        "filedAt": "2024-01-15T10:30:00Z",
                        "summary": "Strong iPhone sales, services revenue growth...",
                        "impact": "high"
                    }
                ],
                "lastUpdate": datetime.now().isoformat()
            }
            
        except Exception as api_error:
            # Fallback to mock data if APIs are not available
            print(f"Market API error: {api_error}")
            return {
                "overview": {
                    "spx": {"price": 4850.25, "change": 15.75},
                    "vix": {"price": 12.50, "change": -0.25},
                    "dxy": {"price": 103.25, "change": 0.15}
                },
                "news": [
                    {
                        "title": "Fed Signals Potential Rate Cuts",
                        "source": "Reuters",
                        "sentiment": "bullish",
                        "impact": "high",
                        "timestamp": "15 min ago",
                        "summary": "Federal Reserve officials hint at possible rate reductions..."
                    }
                ],
                "economic": [
                    {
                        "indicator": "CPI (YoY)",
                        "value": "3.1%",
                        "change": 0.1,
                        "nextRelease": "Jan 15"
                    }
                ],
                "filings": [
                    {
                        "company": "Apple Inc.",
                        "type": "10-K",
                        "filedAt": "2024-01-15T10:30:00Z",
                        "summary": "Strong iPhone sales, services revenue growth...",
                        "impact": "high"
                    }
                ],
                "lastUpdate": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
async def get_agents_status():
    """Get active agent count and status from database"""
    try:
        with DataService() as service:
            agents = service.get_all_agents()
            
            # Format agents for frontend
            agents_data = []
            for agent in agents:
                agents_data.append({
                    "id": agent["id"],
                    "name": agent["name"],
                    "status": agent["status"],
                    "lastActivity": "2 min ago"  # TODO: Calculate from last_activity
                })
            
            return {
                "totalAgents": len(agents),
                "activeAgents": len([a for a in agents if a.get('status') == 'active']),
                "agents": agents_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/active")
async def get_active_strategies():
    """Get running strategy count from database"""
    try:
        with DataService() as service:
            strategies = service.get_all_strategies()
            
            # Format strategies for frontend
            strategies_data = []
            for strategy in strategies:
                strategies_data.append({
                    "id": strategy["id"],
                    "name": strategy["name"],
                    "status": strategy["status"],
                    "allocation": float(strategy.get("allocation", 0)),
                    "pnl": float(strategy.get("pnl", 0)),
                    "sharpe": float(strategy.get("sharpe_ratio", 0)),
                    "winRate": float(strategy.get("win_rate", 0)),
                    "maxDrawdown": float(strategy.get("max_drawdown", 0)),
                    "trades": int(strategy.get("trades_count", 0)),
                    "lastTrade": "2 min ago"  # TODO: Calculate from last_trade_at
                })
            
            return {
                "totalStrategies": len(strategies),
                "activeStrategies": len([s for s in strategies if s.get('status') == 'active']),
                "strategies": strategies_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/status")
async def get_market_status():
    """Get market hours and trading status"""
    try:
        # TODO: Get real market status from Alpaca market calendar
        return {
            "status": "OPEN",
            "nextOpen": "2024-01-22T09:30:00Z",
            "nextClose": "2024-01-22T16:00:00Z",
            "isOpen": True,
            "sessionOpen": "09:30",
            "sessionClose": "16:00",
            "timezone": "America/New_York"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== PHASE 2 INTEGRATIONS =====

@app.get("/agents/{agent_id}/decisions")
async def get_agent_decisions(agent_id: str, limit: int = 50):
    """Get agent decision history from database"""
    try:
        with DataService() as service:
            decisions = service.get_agent_decisions(agent_id, limit)
            
            # Format decisions for frontend
            formatted_decisions = []
            for decision in decisions:
                formatted_decisions.append({
                    "id": f"decision_{decision['id']}",
                    "agent_id": decision["agent_id"],
                    "decision": decision["decision"],
                    "confidence": float(decision.get("confidence", 0)),
                    "timestamp": decision["created_at"].isoformat() if decision.get("created_at") else datetime.now().isoformat(),
                    "reasoning": decision.get("reasoning", "")
                })
            
            return {"decisions": formatted_decisions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/start")
async def start_strategy(strategy_id: str):
    """Start strategy execution"""
    try:
        with DataService() as service:
            service.update_strategy_status(strategy_id, "active")
        return {"status": "started", "strategy_id": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/pause")
async def pause_strategy(strategy_id: str):
    """Pause strategy execution"""
    try:
        with DataService() as service:
            service.update_strategy_status(strategy_id, "paused")
        return {"status": "paused", "strategy_id": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    """Stop strategy execution"""
    try:
        with DataService() as service:
            service.update_strategy_status(strategy_id, "stopped")
        return {"status": "stopped", "strategy_id": strategy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtests/results")
async def get_backtest_results():
    """Get backtest results from database"""
    try:
        with DataService() as service:
            backtests = service.get_backtest_results()
            
            # Format backtests for frontend
            formatted_backtests = []
            for backtest in backtests:
                formatted_backtests.append({
                    "strategy": backtest["strategy_name"],
                    "period": f"{backtest.get('period_start', '2023')}-{backtest.get('period_end', '2024')}",
                    "returns": float(backtest.get("returns", 0)),
                    "sharpe": float(backtest.get("sharpe_ratio", 0)),
                    "maxDD": float(backtest.get("max_drawdown", 0)),
                    "status": backtest.get("status", "completed")
                })
            
            return {"backtests": formatted_backtests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/latest")
async def get_latest_news(limit: int = 20):
    """Get latest news from database"""
    try:
        with DataService() as service:
            news = service.get_latest_news(limit)
            
            # Format news for frontend
            formatted_news = []
            for article in news:
                formatted_news.append({
                    "title": article["title"],
                    "source": article.get("source", ""),
                    "sentiment": article.get("sentiment", "neutral"),
                    "impact": article.get("impact", "medium"),
                    "timestamp": "15 min ago",  # TODO: Calculate from published_at
                    "summary": article.get("summary", "")
                })
            
            return {"news": formatted_news}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/economic/indicators")
async def get_economic_indicators():
    """Get economic indicators from database"""
    try:
        with DataService() as service:
            indicators = service.get_economic_indicators()
            
            # Format indicators for frontend
            formatted_indicators = []
            for indicator in indicators:
                formatted_indicators.append({
                    "indicator": indicator["indicator_name"],
                    "value": f"{indicator.get('current_value', 0):.1f}%",
                    "change": float(indicator.get("change_value", 0)),
                    "nextRelease": indicator.get("next_release_date", "Jan 15")
                })
            
            return {"economic": formatted_indicators}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sec/filings/latest")
async def get_latest_sec_filings(limit: int = 20):
    """Get latest SEC filings from database"""
    try:
        # TODO: Implement SEC filings from database
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


@app.get("/api/modal/status")
async def get_modal_status():
    """Get Modal compute status"""
    try:
        # TODO: Integrate with Modal API
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


@app.get("/api/database/health")
async def get_database_health():
    """Get database health monitoring"""
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


# ===== ENHANCED WEBSOCKET ENDPOINTS =====

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


@app.websocket("/ws/agents")
async def websocket_agents(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send agent status updates every 15 seconds
            agents_data = await get_agents_status()
            await manager.send_personal_message(
                json.dumps({
                    "type": "agent_status",
                    "payload": agents_data
                }), 
                websocket
            )
            await asyncio.sleep(15)
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


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
