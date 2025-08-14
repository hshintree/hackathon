#!/usr/bin/env python3
"""
Autonomous Trading Agent - FastAPI Backend
Provides REST API endpoints for the trading agent.
"""

from fastapi import FastAPI, HTTPException
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

from agents.langgraph_agent import build_graph

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
    
    try:
        storage = DataStorage()
        with storage.get_session() as session:
            session.execute("SELECT 1")
        database_connected = True
    except Exception:
        database_connected = False
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_keys": api_keys,
        "database_connected": database_connected,
        "modal_available": True
    }


class AgentChatRequest(BaseModel):
    query: str


@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    try:
        state = await graph.ainvoke({"query": request.query})
        return {"state": state}
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


# New endpoints for Next.js frontend
@app.get("/api/system/status")
async def get_system_status():
    """Get overall system health and metrics"""
    try:
        # Get health check data
        health_data = await health_check()
        
        # Mock data for now - replace with real implementations
        system_metrics = {
            "totalPnL": 0.0,  # TODO: Get from Alpaca portfolio
            "activeAgents": 4,  # TODO: Count from agent management system
            "runningStrategies": 2,  # TODO: Count from strategy database
            "marketStatus": "OPEN",  # TODO: Get from Alpaca market calendar
            "systemUptime": "2h 15m",
            "lastUpdate": datetime.now().isoformat(),
            "health": health_data
        }
        
        return system_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/pnl")
async def get_portfolio_pnl():
    """Get real-time P&L calculations"""
    try:
        # Mock data for now - replace with real Alpaca portfolio data
        portfolio_data = {
            "totalPnL": 1250.75,
            "unrealizedPnL": 850.25,
            "realizedPnL": 400.50,
            "totalValue": 25000.00,
            "dailyChange": 125.75,
            "dailyChangePercent": 0.51,
            "positions": [
                {"symbol": "AAPL", "quantity": 10, "avgPrice": 150.00, "currentPrice": 155.25, "pnl": 52.50},
                {"symbol": "TSLA", "quantity": 5, "avgPrice": 200.00, "currentPrice": 210.00, "pnl": 50.00}
            ]
        }
        
        return portfolio_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
async def get_agents_status():
    """Get active agent count and status"""
    try:
        # Mock data for now - replace with real agent management system
        agents_data = {
            "totalAgents": 4,
            "activeAgents": 4,
            "agents": [
                {"id": "agent_1", "name": "Market Analyzer", "status": "active", "lastActivity": "2 min ago"},
                {"id": "agent_2", "name": "Risk Manager", "status": "active", "lastActivity": "1 min ago"},
                {"id": "agent_3", "name": "Portfolio Optimizer", "status": "active", "lastActivity": "30 sec ago"},
                {"id": "agent_4", "name": "News Monitor", "status": "active", "lastActivity": "5 min ago"}
            ]
        }
        
        return agents_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/active")
async def get_active_strategies():
    """Get running strategy count"""
    try:
        # Mock data for now - replace with real strategy database
        strategies_data = {
            "totalStrategies": 8,
            "activeStrategies": 2,
            "strategies": [
                {"id": "strategy_1", "name": "Momentum Trading", "status": "active", "pnl": 450.25},
                {"id": "strategy_2", "name": "Mean Reversion", "status": "active", "pnl": 800.50}
            ]
        }
        
        return strategies_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/status")
async def get_market_status():
    """Get market hours and trading status"""
    try:
        # Mock data for now - replace with real Alpaca market calendar
        market_data = {
            "status": "OPEN",
            "nextOpen": "2024-01-22T09:30:00Z",
            "nextClose": "2024-01-22T16:00:00Z",
            "isOpen": True,
            "sessionOpen": "09:30",
            "sessionClose": "16:00",
            "timezone": "America/New_York"
        }
        
        return market_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True, log_level="info")
